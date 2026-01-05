#!/usr/bin/env python3
"""
Generate Claude MCP configuration from config.yaml.

This script reads the master config.yaml and generates the appropriate
mcpServers configuration for Claude Code's ~/.claude.json file.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

MCP_HUB_DIR = Path(__file__).parent.parent
CONFIG_FILE = MCP_HUB_DIR / "config.yaml"
OUTPUT_FILE = MCP_HUB_DIR / "generated" / "claude-mcp-servers.json"


def load_config() -> dict:
    """Load the master config.yaml."""
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def decrypt_secrets(secrets_file: str) -> dict:
    """Decrypt a SOPS-encrypted secrets file and return as dict."""
    secrets_path = MCP_HUB_DIR / secrets_file
    sops_config = MCP_HUB_DIR / "secrets" / ".sops.yaml"
    age_key_file = Path.home() / ".config" / "sops" / "age" / "keys.txt"

    if not secrets_path.exists():
        print(f"  Warning: Secrets file not found: {secrets_file}")
        return {}

    # Set age key file for SOPS
    env = os.environ.copy()
    env["SOPS_AGE_KEY_FILE"] = str(age_key_file)

    try:
        result = subprocess.run(
            ["sops", "--config", str(sops_config), "-d", str(secrets_path)],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        return yaml.safe_load(result.stdout) or {}
    except subprocess.CalledProcessError as e:
        print(f"  Warning: Failed to decrypt {secrets_file}: {e.stderr}")
        return {}
    except FileNotFoundError:
        print("  Warning: SOPS not installed, using environment variables")
        return {}


def resolve_env_var(value: str, secrets: dict) -> str:
    """Resolve environment variable references like ${VAR} or ${VAR:-default}."""
    if not isinstance(value, str) or not value.startswith("${"):
        return value

    # Parse ${VAR} or ${VAR:-default}
    inner = value[2:-1]  # Remove ${ and }
    if ":-" in inner:
        var_name, default = inner.split(":-", 1)
    else:
        var_name = inner
        default = None

    # Check secrets first, then environment
    if var_name in secrets:
        return secrets[var_name]
    elif var_name in os.environ:
        return os.environ[var_name]
    elif default is not None:
        return default
    else:
        # Return the placeholder - Claude will resolve from environment
        return value


def build_server_config(name: str, server: dict, secrets: dict) -> dict | None:
    """Build a single server configuration for Claude."""
    if not server.get("enabled", True):
        print(f"  Skipping {name} (disabled)")
        return None

    source = server.get("source")
    transport = server.get("transport", "stdio")

    config = {"type": transport}

    # Build command and args based on source type
    if source == "npx":
        package = server.get("package")
        args = server.get("args", [])
        config["command"] = "npx"
        config["args"] = ["-y", package] + args

    elif source == "npm":
        package = server.get("package")
        config["command"] = "npx"
        config["args"] = ["-y", package]

    elif source == "pip":
        command = server.get("command", ["python", "-m", server.get("package")])
        config["command"] = command[0]
        config["args"] = command[1:]

    elif source == "docker":
        image = server.get("image")
        config["command"] = "docker"
        config["args"] = ["run", "-i", "--rm"]

        # Add environment variables to docker run
        for env_name in server.get("env", {}).keys():
            config["args"].extend(["-e", env_name])

        config["args"].append(image)

    elif source == "local":
        path = MCP_HUB_DIR / server.get("path")
        command = server.get("command", ["node", "./dist/index.js"])
        config["command"] = command[0]
        config["args"] = command[1:]
        # Set working directory for local servers
        config["cwd"] = str(path)

    elif source == "remote":
        # Remote MCP servers use HTTP/SSE transport with a URL
        url = server.get("url")
        if not url:
            print(f"  Warning: Remote server {name} missing URL")
            return None
        # Resolve any environment variables in the URL
        resolved_url = resolve_env_var(url, secrets)
        if resolved_url.startswith("${"):
            print(f"  Warning: URL not configured for {name}, skipping")
            return None
        config["url"] = resolved_url
        # Remote servers don't need command/args - just url and type

    else:
        print(f"  Warning: Unknown source type for {name}: {source}")
        return None

    # Add environment variables
    if "env" in server:
        env = {}
        for key, value in server["env"].items():
            resolved = resolve_env_var(value, secrets)
            env[key] = resolved
        config["env"] = env

    return config


def generate_claude_config(config: dict) -> dict:
    """Generate the complete mcpServers configuration."""
    mcp_servers = {}

    for name, server in config.get("servers", {}).items():
        print(f"Processing: {name}")

        # Load secrets if specified
        secrets = {}
        if "secrets_file" in server:
            secrets = decrypt_secrets(server["secrets_file"])

        server_config = build_server_config(name, server, secrets)
        if server_config:
            mcp_servers[name] = server_config
            print(f"  ✓ Added {name}")

    return {"mcpServers": mcp_servers}


def update_claude_json(mcp_config: dict) -> None:
    """Update ~/.claude.json with the new mcpServers configuration."""
    claude_json_path = Path.home() / ".claude.json"

    # Read existing config
    if claude_json_path.exists():
        with open(claude_json_path) as f:
            claude_config = json.load(f)
    else:
        claude_config = {}

    # Update mcpServers
    claude_config["mcpServers"] = mcp_config["mcpServers"]

    # Write back
    with open(claude_json_path, "w") as f:
        json.dump(claude_config, f, indent=2)

    print(f"\n✓ Updated {claude_json_path}")


def main():
    print("Generating Claude MCP configuration...\n")

    # Load master config
    config = load_config()

    # Generate MCP config
    mcp_config = generate_claude_config(config)

    # Save to generated directory
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(mcp_config, f, indent=2)
    print(f"\n✓ Saved to {OUTPUT_FILE}")

    # Update ~/.claude.json
    update_claude_json(mcp_config)

    # Summary
    enabled = len(mcp_config["mcpServers"])
    total = len(config.get("servers", {}))
    print(f"\nSummary: {enabled}/{total} servers enabled")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
