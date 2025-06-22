# ProxmoxMCP Project Overview

## Purpose
ProxmoxMCP is a Python-based Model Context Protocol (MCP) server for interacting with Proxmox hypervisors. It provides a clean interface for managing nodes, VMs, and containers through the MCP protocol, with full integration with Cline and other MCP-compatible clients.

## Key Features
- Full integration with Cline and MCP SDK
- Secure token-based authentication with Proxmox
- Tools for managing nodes, VMs, containers, and storage
- VM console command execution via QEMU Guest Agent
- Type-safe implementation with Pydantic
- Rich output formatting with customizable themes
- Configurable logging system

## Tech Stack
- **Language**: Python 3.12+
- **Main Dependencies**:
  - `mcp` - Model Context Protocol SDK
  - `proxmoxer` - Python wrapper for Proxmox API
  - `pydantic` - Data validation using Python type annotations
  - `requests` - HTTP library
- **Development Dependencies**:
  - `pytest` - Testing framework
  - `pytest-asyncio` - Async testing support
  - `black` - Code formatter
  - `mypy` - Type checker
  - `ruff` - Linter
  - `types-requests` - Type stubs for requests

## Architecture
The project is built as an MCP server that:
1. Connects to Proxmox hypervisors via API tokens
2. Exposes Proxmox management capabilities as MCP tools
3. Provides formatted output for better readability
4. Handles authentication, error handling, and logging

## Configuration
Uses JSON configuration files with:
- Proxmox connection details (host, port, SSL settings)
- Authentication credentials (user, token name, token value)
- Logging configuration (level, format, file output)

Environment variable: `PROXMOX_MCP_CONFIG` points to the config file.