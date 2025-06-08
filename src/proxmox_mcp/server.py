"""
Main server implementation for Proxmox MCP.

This module implements the core MCP server for Proxmox integration, providing:
- Configuration loading and validation
- Logging setup
- Proxmox API connection management
- MCP tool registration and routing
- Signal handling for graceful shutdown

The server exposes a set of tools for managing Proxmox resources including:
- Node management
- VM operations
- Storage management
- Cluster status monitoring
"""
import os
import signal
import sys
from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .config.loader import load_config
from .core.logging import setup_logging
from .core.proxmox import ProxmoxManager
from .tools.cluster import ClusterTools
from .tools.definitions import (
    CREATE_VM_DESC,
    DELETE_VM_DESC,
    EXECUTE_VM_COMMAND_DESC,
    GET_CLUSTER_STATUS_DESC,
    GET_NODE_STATUS_DESC,
    GET_NODES_DESC,
    GET_STORAGE_DESC,
    GET_VMS_DESC,
    RESTART_VM_DESC,
    SHUTDOWN_VM_DESC,
    START_VM_DESC,
    STOP_VM_DESC,
)
from .tools.node import NodeTools
from .tools.storage import StorageTools
from .tools.vm import VMTools


class ProxmoxMCPServer:
    """Main server class for Proxmox MCP."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the server.

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.logger = setup_logging(self.config.logging)

        # Initialize core components
        self.proxmox_manager = ProxmoxManager(self.config.proxmox, self.config.auth)
        self.proxmox = self.proxmox_manager.get_api()

        # Initialize tools
        self.node_tools = NodeTools(self.proxmox)
        self.vm_tools = VMTools(self.proxmox)
        self.storage_tools = StorageTools(self.proxmox)
        self.cluster_tools = ClusterTools(self.proxmox)

        # Initialize MCP server
        self.mcp = FastMCP("ProxmoxMCP")
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Register MCP tools with the server.

        Initializes and registers all available tools with the MCP server:
        - Node management tools (list nodes, get status)
        - VM operation tools (list VMs, execute commands)
        - VM lifecycle management (start, stop, shutdown, restart)
        - Storage management tools (list storage)
        - Cluster tools (get cluster status)

        Each tool is registered with appropriate descriptions and parameter
        validation using Pydantic models.
        """

        # Node tools
        @self.mcp.tool(description=GET_NODES_DESC)
        def get_nodes():
            return self.node_tools.get_nodes()

        @self.mcp.tool(description=GET_NODE_STATUS_DESC)
        def get_node_status(
            node: Annotated[
                str,
                Field(
                    description="Name/ID of node to query (e.g. 'pve1', 'proxmox-node2')"
                ),
            ]
        ):
            return self.node_tools.get_node_status(node)

        # VM tools
        @self.mcp.tool(description=GET_VMS_DESC)
        def get_vms():
            return self.vm_tools.get_vms()

        @self.mcp.tool(description=EXECUTE_VM_COMMAND_DESC)
        async def execute_vm_command(
            node: Annotated[
                str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")
            ],
            vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")],
            command: Annotated[
                str,
                Field(
                    description="Shell command to run (e.g. 'uname -a', 'systemctl status nginx')"
                ),
            ],
        ):
            return await self.vm_tools.execute_command(node, vmid, command)

        # VM lifecycle tools
        @self.mcp.tool(description=START_VM_DESC)
        async def start_vm(
            node: Annotated[
                str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")
            ],
            vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")],
        ):
            return await self.vm_tools.start_vm(node, vmid)

        @self.mcp.tool(description=STOP_VM_DESC)
        async def stop_vm(
            node: Annotated[
                str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")
            ],
            vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")],
        ):
            return await self.vm_tools.stop_vm(node, vmid)

        @self.mcp.tool(description=SHUTDOWN_VM_DESC)
        async def shutdown_vm(
            node: Annotated[
                str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")
            ],
            vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")],
        ):
            return await self.vm_tools.shutdown_vm(node, vmid)

        @self.mcp.tool(description=RESTART_VM_DESC)
        async def restart_vm(
            node: Annotated[
                str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")
            ],
            vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")],
        ):
            return await self.vm_tools.restart_vm(node, vmid)

        @self.mcp.tool(description=CREATE_VM_DESC)
        async def create_vm(
            node: Annotated[
                str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")
            ],
            vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")],
            name: Annotated[str, Field(description="VM name (e.g. 'test-vm')")],
            memory: Annotated[int, Field(description="Memory in MB (default: 512)")] = 512,
            cores: Annotated[int, Field(description="CPU cores (default: 1)")] = 1,
        ):
            return await self.vm_tools.create_vm(node, vmid, name, memory, cores)

        @self.mcp.tool(description=DELETE_VM_DESC)
        async def delete_vm(
            node: Annotated[
                str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")
            ],
            vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")],
        ):
            return await self.vm_tools.delete_vm(node, vmid)

        # Storage tools
        @self.mcp.tool(description=GET_STORAGE_DESC)
        def get_storage():
            return self.storage_tools.get_storage()

        # Cluster tools
        @self.mcp.tool(description=GET_CLUSTER_STATUS_DESC)
        def get_cluster_status():
            return self.cluster_tools.get_cluster_status()

    def start(self) -> None:
        """Start the MCP server.

        Initializes the server with:
        - Signal handlers for graceful shutdown (SIGINT, SIGTERM)
        - Async runtime for handling concurrent requests
        - Error handling and logging

        The server runs until terminated by a signal or fatal error.
        """
        import anyio

        def signal_handler(signum, frame):
            self.logger.info("Received signal to shutdown...")
            sys.exit(0)

        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            self.logger.info("Starting MCP server...")
            anyio.run(self.mcp.run_stdio_async)
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    config_path = os.getenv("PROXMOX_MCP_CONFIG")
    if not config_path:
        print("PROXMOX_MCP_CONFIG environment variable must be set")
        sys.exit(1)

    try:
        server = ProxmoxMCPServer(config_path)
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
