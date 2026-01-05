# Contributing to MCP Mainframe

Thank you for your interest in contributing to MCP Mainframe! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** and clone it locally
2. **Set up your environment** following the README instructions
3. **Create a branch** for your changes

## Types of Contributions

### Bug Reports

If you find a bug, please open an issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)

### Feature Requests

Have an idea for a new MCP server integration or feature? Open an issue with:
- A description of the feature
- Use cases and benefits
- Any implementation ideas you have

### Code Contributions

#### Adding a New MCP Server

1. Check if there's an existing integration first
2. Create a new directory under `servers/` if building a custom server
3. Follow the existing patterns for configuration:
   - Add entry to `config.yaml`
   - Create secrets template in `secrets/examples/`
   - Document environment variables
4. Test thoroughly before submitting

#### Improving Documentation

Documentation improvements are always welcome:
- Fix typos or unclear explanations
- Add examples
- Document edge cases
- Improve setup instructions

### Pull Request Process

1. **Create a focused PR** - One feature or fix per PR
2. **Update documentation** if your change affects setup or usage
3. **Test your changes** in a fresh environment if possible
4. **Describe your changes** clearly in the PR description

## Code Style

- Follow existing patterns in the codebase
- Use clear, descriptive variable names
- Add comments for complex logic
- Keep configuration files well-organized

## Security

- **Never commit secrets** - Use the secrets templates as examples
- **Sanitize examples** - Remove any personal URLs, IDs, or tokens
- **Report vulnerabilities** privately via security contact

## Questions?

Open an issue with the "question" label if you need help or clarification.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
