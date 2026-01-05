"""
SQS client for communicating with the TWS service on EC2.

This module provides SQS communication with the Interactive Brokers
TWS service. It handles message correlation via execution IDs.

Required Environment Variables:
    IBKR_REQUEST_QUEUE_URL: SQS queue URL for sending requests
    IBKR_RESPONSE_QUEUE_URL: SQS queue URL for receiving responses
    AWS_REGION: AWS region (default: us-west-2)
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

DEFAULT_REGION = "us-west-2"


class SQSClientError(Exception):
    """Base exception for SQS client errors."""
    pass


class SQSTimeoutError(SQSClientError):
    """Raised when waiting for a response times out."""
    pass


class SQSClient:
    """
    Client for SQS-based communication with the TWS service.

    This client sends requests to the TWS service running on EC2 and
    waits for responses. It handles message correlation via execution IDs.

    Usage:
        client = SQSClient(
            request_queue_url="https://sqs.us-west-2.amazonaws.com/123456789/ibkr-requests",
            response_queue_url="https://sqs.us-west-2.amazonaws.com/123456789/ibkr-responses",
        )
        response = client.send_request("tws_health")
        print(response)  # {"status": "success", "metadata": {...}}
    """

    def __init__(
        self,
        request_queue_url: str,
        response_queue_url: str,
        region: str = DEFAULT_REGION,
    ):
        """
        Initialize the SQS client.

        Args:
            request_queue_url: URL for the request queue
            response_queue_url: URL for the response queue
            region: AWS region (defaults to us-west-2)
        """
        if not request_queue_url:
            raise ValueError("request_queue_url is required")
        if not response_queue_url:
            raise ValueError("response_queue_url is required")

        self.request_queue_url = request_queue_url
        self.response_queue_url = response_queue_url
        self.region = region
        self._client: Optional[boto3.client] = None

    @property
    def client(self) -> boto3.client:
        """Lazy-initialize the SQS client."""
        if self._client is None:
            self._client = boto3.client("sqs", region_name=self.region)
        return self._client

    def send_message(self, message: dict) -> dict:
        """
        Send a message to the request queue.

        Args:
            message: Message payload to send

        Returns:
            SQS send_message response
        """
        return self.client.send_message(
            QueueUrl=self.request_queue_url,
            MessageBody=json.dumps(message),
        )

    def send_request(
        self,
        operation: str,
        params: Optional[dict] = None,
        timeout_minutes: int = 5,
        wait_time_seconds: int = 3,
    ) -> dict:
        """
        Send a request to the TWS service and wait for response.

        This is the main entry point for TWS operations. It:
        1. Generates a unique execution ID
        2. Sends the request to the request queue
        3. Polls the response queue for a matching response
        4. Returns the response data

        Args:
            operation: Operation name (e.g., "tws_health", "account_values")
            params: Optional parameters for the operation
            timeout_minutes: Maximum time to wait for response
            wait_time_seconds: Time between polling attempts

        Returns:
            Response data from the TWS service

        Raises:
            SQSTimeoutError: If no response received within timeout
            SQSClientError: For other SQS-related errors
        """
        execution_id = str(uuid4())
        timestamp = datetime.now().isoformat()

        request = {
            "operation": operation,
            "execution_id": execution_id,
            "timestamp": timestamp,
        }
        if params:
            request.update(params)

        logger.info(f"Sending request {execution_id} for operation '{operation}'")

        try:
            self.send_message(request)
        except ClientError as e:
            raise SQSClientError(f"Failed to send request: {e}") from e

        logger.info(f"Waiting for response to {execution_id}")
        return self._wait_for_response(
            execution_id=execution_id,
            timeout_minutes=timeout_minutes,
            wait_time_seconds=wait_time_seconds,
        )

    def _wait_for_response(
        self,
        execution_id: str,
        timeout_minutes: int = 5,
        wait_time_seconds: int = 3,
    ) -> dict:
        """
        Wait for and retrieve a response matching the execution ID.

        Args:
            execution_id: Unique ID to match request with response
            timeout_minutes: Maximum time to wait
            wait_time_seconds: SQS long-polling wait time

        Returns:
            Response data from the TWS service

        Raises:
            SQSTimeoutError: If timeout is reached
        """
        start_time = datetime.now()
        timeout = start_time + timedelta(minutes=timeout_minutes)
        poll_delay = 0.5  # Start with short delay, use exponential backoff

        while datetime.now() < timeout:
            try:
                response = self.client.receive_message(
                    QueueUrl=self.response_queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=wait_time_seconds,
                    MessageAttributeNames=["ExecutionId"],
                )
            except ClientError as e:
                logger.warning(f"Error receiving message: {e}")
                time.sleep(poll_delay)
                poll_delay = min(poll_delay * 1.5, 5.0)
                continue

            messages = response.get("Messages", [])
            if not messages:
                time.sleep(min(poll_delay, 5.0))
                poll_delay = min(poll_delay * 1.5, 5.0)
                continue

            matching_message = None
            for message in messages:
                msg_execution_id = (
                    message.get("MessageAttributes", {})
                    .get("ExecutionId", {})
                    .get("StringValue")
                )

                if msg_execution_id == execution_id:
                    matching_message = message
                else:
                    # Return non-matching messages to the queue
                    try:
                        self.client.change_message_visibility(
                            QueueUrl=self.response_queue_url,
                            ReceiptHandle=message["ReceiptHandle"],
                            VisibilityTimeout=0,
                        )
                    except ClientError:
                        pass  # Best effort

            if matching_message:
                try:
                    response_data = json.loads(matching_message["Body"])
                    # Delete the processed message
                    self.client.delete_message(
                        QueueUrl=self.response_queue_url,
                        ReceiptHandle=matching_message["ReceiptHandle"],
                    )
                    logger.info(f"Received response for {execution_id}")
                    return response_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in response: {e}")
                    # Return malformed message to queue
                    try:
                        self.client.change_message_visibility(
                            QueueUrl=self.response_queue_url,
                            ReceiptHandle=matching_message["ReceiptHandle"],
                            VisibilityTimeout=0,
                        )
                    except ClientError:
                        pass

            # Exponential backoff
            time.sleep(min(poll_delay, 5.0))
            poll_delay = min(poll_delay * 1.5, 5.0)

        raise SQSTimeoutError(
            f"Timeout waiting for response. Execution ID: {execution_id}"
        )

    # Convenience methods for specific operations

    def health_check(self, timeout_minutes: int = 2) -> dict:
        """Check TWS connection health."""
        return self.send_request("tws_health", timeout_minutes=timeout_minutes)

    def account_values(self, timeout_minutes: int = 5) -> dict:
        """Get account values and balances."""
        return self.send_request("account_values", timeout_minutes=timeout_minutes)

    def positions(self, timeout_minutes: int = 5) -> dict:
        """Get current positions with exchange rates."""
        return self.send_request("raw_positions", timeout_minutes=timeout_minutes)

    def daily_ohlcv(self, timeout_minutes: int = 20) -> dict:
        """Get daily OHLCV data for tracked symbols."""
        return self.send_request("daily_ohlcv", timeout_minutes=timeout_minutes)

    def hourly_ohlcv(self, timeout_minutes: int = 20) -> dict:
        """Get hourly OHLCV data for tracked symbols."""
        return self.send_request("hourly_ohlcv", timeout_minutes=timeout_minutes)

    def contract_details(self, timeout_minutes: int = 20) -> dict:
        """Get contract details for all tracked symbols."""
        return self.send_request("contract_details", timeout_minutes=timeout_minutes)

    def find_symbols(self, query: str, timeout_minutes: int = 2) -> dict:
        """Search for contracts matching a query."""
        return self.send_request(
            "find_symbols",
            params={"query": query},
            timeout_minutes=timeout_minutes,
        )

    def get_contract_by_id(
        self,
        contract_id: int,
        check_ohlcv: bool = False,
        timeout_minutes: int = 2,
    ) -> dict:
        """Get details for a specific contract by ID."""
        return self.send_request(
            "get_contract_details_by_id",
            params={
                "contract_id": contract_id,
                "check_ohlcv_availability": check_ohlcv,
            },
            timeout_minutes=timeout_minutes,
        )

    def custom_ohlcv(
        self,
        symbols: list[dict],
        duration_str: str = "7 D",
        bar_size_setting: str = "1 day",
        timeout_minutes: int = 20,
    ) -> dict:
        """
        Get custom OHLCV data for specific symbols.

        Args:
            symbols: List of symbol dicts with keys like:
                     {"symbol": "AAPL", "currency": "USD", "secType": "STK"}
            duration_str: Duration string (e.g., "7 D", "1 M")
            bar_size_setting: Bar size (e.g., "1 day", "1 hour")
            timeout_minutes: Request timeout
        """
        return self.send_request(
            "ohlcv",
            params={
                "symbols": symbols,
                "duration_str": duration_str,
                "bar_size_setting": bar_size_setting,
            },
            timeout_minutes=timeout_minutes,
        )
