"""
VM-related tools for Proxmox MCP.

This module provides tools for managing and interacting with Proxmox VMs:
- Listing all VMs across the cluster with their status
- Retrieving detailed VM information including:
  * Resource allocation (CPU, memory)
  * Runtime status
  * Node placement
- VM lifecycle operations:
  * Starting and stopping VMs
  * Graceful shutdown and restart
  * Power management operations
- Executing commands within VMs via QEMU guest agent
- Handling VM console operations

The tools implement fallback mechanisms for scenarios where
detailed VM information might be temporarily unavailable.
"""
from typing import List

from mcp.types import TextContent as Content

from .base import ProxmoxTool
from .console.manager import VMConsoleManager


class VMTools(ProxmoxTool):
    """Tools for managing Proxmox VMs.

    Provides functionality for:
    - Retrieving cluster-wide VM information
    - Getting detailed VM status and configuration
    - VM lifecycle management (start, stop, shutdown, restart)
    - Executing commands within VMs
    - Managing VM console operations

    Implements fallback mechanisms for scenarios where detailed
    VM information might be temporarily unavailable. Integrates
    with QEMU guest agent for VM command execution.
    """

    def __init__(self, proxmox_api):
        """Initialize VM tools.

        Args:
            proxmox_api: Initialized ProxmoxAPI instance
        """
        super().__init__(proxmox_api)
        self.console_manager = VMConsoleManager(proxmox_api)

    def get_vms(self) -> List[Content]:
        """List all virtual machines across the cluster with detailed status.

        Retrieves comprehensive information for each VM including:
        - Basic identification (ID, name)
        - Runtime status (running, stopped)
        - Resource allocation and usage:
          * CPU cores
          * Memory allocation and usage
        - Node placement

        Implements a fallback mechanism that returns basic information
        if detailed configuration retrieval fails for any VM.

        Returns:
            List of Content objects containing formatted VM information:
            {
                "vmid": "100",
                "name": "vm-name",
                "status": "running/stopped",
                "node": "node-name",
                "cpus": core_count,
                "memory": {
                    "used": bytes,
                    "total": bytes
                }
            }

        Raises:
            RuntimeError: If the cluster-wide VM query fails
        """
        try:
            result = []
            for node in self.proxmox.nodes.get():
                node_name = node["node"]
                vms = self.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    vmid = vm["vmid"]
                    # Get VM config for CPU cores
                    try:
                        config = self.proxmox.nodes(node_name).qemu(vmid).config.get()
                        result.append(
                            {
                                "vmid": vmid,
                                "name": vm["name"],
                                "status": vm["status"],
                                "node": node_name,
                                "cpus": config.get("cores", "N/A"),
                                "memory": {
                                    "used": vm.get("mem", 0),
                                    "total": vm.get("maxmem", 0),
                                },
                            }
                        )
                    except Exception:
                        # Fallback if can't get config
                        result.append(
                            {
                                "vmid": vmid,
                                "name": vm["name"],
                                "status": vm["status"],
                                "node": node_name,
                                "cpus": "N/A",
                                "memory": {
                                    "used": vm.get("mem", 0),
                                    "total": vm.get("maxmem", 0),
                                },
                            }
                        )
            return self._format_response(result, "vms")
        except Exception as e:
            self._handle_error("get VMs", e)

    async def execute_command(
        self, node: str, vmid: str, command: str
    ) -> List[Content]:
        """Execute a command in a VM via QEMU guest agent.

        Uses the QEMU guest agent to execute commands within a running VM.
        Requires:
        - VM must be running
        - QEMU guest agent must be installed and running in the VM
        - Command execution permissions must be enabled

        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2')
            vmid: VM ID number (e.g., '100', '101')
            command: Shell command to run (e.g., 'uname -a', 'systemctl status nginx')

        Returns:
            List of Content objects containing formatted command output:
            {
                "success": true/false,
                "output": "command output",
                "error": "error message if any"
            }

        Raises:
            ValueError: If VM is not found, not running, or guest agent is not available
            RuntimeError: If command execution fails due to permissions or other issues
        """
        try:
            result = await self.console_manager.execute_command(node, vmid, command)
            # Use the command output formatter from ProxmoxFormatters
            from ..formatting import ProxmoxFormatters

            formatted = ProxmoxFormatters.format_command_output(
                success=result["success"],
                command=command,
                output=result["output"],
                error=result.get("error"),
            )
            return [Content(type="text", text=formatted)]
        except Exception as e:
            self._handle_error(f"execute command on VM {vmid}", e)

    async def start_vm(self, node: str, vmid: str) -> List[Content]:
        """Start a virtual machine.

        Initiates the boot process for a stopped virtual machine. The VM
        must be in a stopped state for this operation to succeed.

        Args:
            node: Name of the node where the VM is located (e.g., 'pve1')
            vmid: ID of the VM to start (e.g., '100')

        Returns:
            List of Content objects containing operation result:
            {
                "success": true/false,
                "message": "descriptive message",
                "upid": "task_id_for_monitoring"
            }

        Raises:
            ValueError: If VM is not found or already running
            RuntimeError: If start operation fails due to resource constraints
        """
        try:
            self.logger.info(f"Starting VM {vmid} on node {node}")

            # Check current VM status
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            if vm_status["status"] == "running":
                raise ValueError(f"VM {vmid} is already running")

            # Start the VM
            result = self.proxmox.nodes(node).qemu(vmid).status.start.post()

            self.logger.info(f"VM {vmid} start initiated successfully")

            import json

            response = {
                "success": True,
                "message": f"VM {vmid} started successfully",
                "upid": result if isinstance(result, str) else None,
            }
            return [Content(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            self._handle_error(f"start VM {vmid}", e)

    async def stop_vm(self, node: str, vmid: str) -> List[Content]:
        """Stop a virtual machine forcefully.

        Immediately stops a running virtual machine without graceful shutdown.
        This is equivalent to pulling the power cord on a physical machine.

        Args:
            node: Name of the node where the VM is located (e.g., 'pve1')
            vmid: ID of the VM to stop (e.g., '100')

        Returns:
            List of Content objects containing operation result:
            {
                "success": true/false,
                "message": "descriptive message",
                "upid": "task_id_for_monitoring"
            }

        Raises:
            ValueError: If VM is not found or already stopped
            RuntimeError: If stop operation fails
        """
        try:
            self.logger.info(f"Stopping VM {vmid} on node {node}")

            # Check current VM status
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            if vm_status["status"] == "stopped":
                raise ValueError(f"VM {vmid} is already stopped")

            # Stop the VM
            result = self.proxmox.nodes(node).qemu(vmid).status.stop.post()

            self.logger.info(f"VM {vmid} stop initiated successfully")

            import json

            response = {
                "success": True,
                "message": f"VM {vmid} stopped successfully",
                "upid": result if isinstance(result, str) else None,
            }
            return [Content(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            self._handle_error(f"stop VM {vmid}", e)

    async def shutdown_vm(self, node: str, vmid: str) -> List[Content]:
        """Shutdown a virtual machine gracefully.

        Sends a shutdown signal to the guest operating system, allowing it
        to perform a clean shutdown. Requires guest tools to be installed.

        Args:
            node: Name of the node where the VM is located (e.g., 'pve1')
            vmid: ID of the VM to shutdown (e.g., '100')

        Returns:
            List of Content objects containing operation result:
            {
                "success": true/false,
                "message": "descriptive message",
                "upid": "task_id_for_monitoring"
            }

        Raises:
            ValueError: If VM is not found or already stopped
            RuntimeError: If shutdown operation fails
        """
        try:
            self.logger.info(f"Shutting down VM {vmid} on node {node}")

            # Check current VM status
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            if vm_status["status"] == "stopped":
                raise ValueError(f"VM {vmid} is already stopped")

            # Shutdown the VM
            result = self.proxmox.nodes(node).qemu(vmid).status.shutdown.post()

            self.logger.info(f"VM {vmid} shutdown initiated successfully")

            import json

            response = {
                "success": True,
                "message": f"VM {vmid} shutdown initiated",
                "upid": result if isinstance(result, str) else None,
            }
            return [Content(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            self._handle_error(f"shutdown VM {vmid}", e)

    async def restart_vm(self, node: str, vmid: str) -> List[Content]:
        """Restart a virtual machine gracefully.

        Performs a graceful reboot operation on a running virtual machine. This
        sends a reboot signal to the guest OS, allowing it to shut down cleanly
        and restart. Much preferred over hard reset for VMs with operating systems.

        Args:
            node: Name of the node where the VM is located (e.g., 'pve1')
            vmid: ID of the VM to restart (e.g., '100')

        Returns:
            List of Content objects containing operation result:
            {
                "success": true/false,
                "message": "descriptive message",
                "upid": "task_id_for_monitoring"
            }

        Raises:
            ValueError: If VM is not found or not running
            RuntimeError: If restart operation fails
        """
        try:
            self.logger.info(f"Rebooting VM {vmid} on node {node}")

            # Check current VM status
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            if vm_status["status"] != "running":
                raise ValueError(
                    f"VM {vmid} is not running (current status: {vm_status['status']})"
                )

            # Reboot the VM gracefully
            result = self.proxmox.nodes(node).qemu(vmid).status.reboot.post()

            self.logger.info(f"VM {vmid} reboot initiated successfully")

            import json

            response = {
                "success": True,
                "message": f"VM {vmid} reboot initiated",
                "upid": result if isinstance(result, str) else None,
            }
            return [Content(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            self._handle_error(f"reboot VM {vmid}", e)

    async def create_vm(
        self, node: str, vmid: str, name: str, memory: int = 512, cores: int = 1
    ) -> List[Content]:
        """Create a new virtual machine with minimal configuration.

        Creates a basic VM suitable for testing purposes. The VM will be created
        in a stopped state and can be started using the start_vm method.

        Args:
            node: Name of the node to create the VM on (e.g., 'pve1')
            vmid: ID for the new VM (e.g., '999')
            name: Name for the VM (e.g., 'test-vm')
            memory: Memory allocation in MB (default: 512)
            cores: Number of CPU cores (default: 1)

        Returns:
            List of Content objects containing creation result:
            {
                "success": true/false,
                "message": "descriptive message",
                "vmid": "created_vm_id"
            }

        Raises:
            ValueError: If VM ID already exists
            RuntimeError: If VM creation fails
        """
        try:
            self.logger.info(f"Creating VM {vmid} ({name}) on node {node}")

            # Check if VM ID already exists
            try:
                self.proxmox.nodes(node).qemu(vmid).status.current.get()
                raise ValueError(f"VM {vmid} already exists")
            except Exception:
                # VM doesn't exist, good to proceed
                pass

            # Create the VM with minimal configuration
            self.proxmox.nodes(node).qemu.post(
                vmid=vmid,
                name=name,
                ostype="l26",  # Linux 2.6+
                memory=memory,
                cores=cores,
                sockets=1,
                # Minimal disk setup
                scsi0="local-zfs:1",
                boot="order=scsi0",
                # Network setup
                net0="virtio,bridge=vmbr0",
            )

            self.logger.info(f"VM {vmid} created successfully")

            import json

            response = {
                "success": True,
                "message": f"VM {vmid} ({name}) created successfully",
                "vmid": vmid,
            }
            return [Content(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            self._handle_error(f"create VM {vmid}", e)

    async def delete_vm(self, node: str, vmid: str) -> List[Content]:
        """Delete a virtual machine permanently.

        Removes a VM and all its associated resources. The VM must be
        stopped before it can be deleted.

        Args:
            node: Name of the node where the VM is located (e.g., 'pve1')
            vmid: ID of the VM to delete (e.g., '999')

        Returns:
            List of Content objects containing deletion result:
            {
                "success": true/false,
                "message": "descriptive message",
                "upid": "task_id_for_monitoring"
            }

        Raises:
            ValueError: If VM is not found or still running
            RuntimeError: If deletion fails
        """
        try:
            self.logger.info(f"Deleting VM {vmid} on node {node}")

            # Check current VM status
            try:
                vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
                if vm_status["status"] in ["running", "paused"]:
                    raise ValueError(f"VM {vmid} must be stopped before deletion")
            except Exception as e:
                if "not found" not in str(e).lower():
                    raise
                # VM doesn't exist
                raise ValueError(f"VM {vmid} not found") from None

            # Delete the VM
            result = self.proxmox.nodes(node).qemu(vmid).delete()

            self.logger.info(f"VM {vmid} deleted successfully")

            import json

            response = {
                "success": True,
                "message": f"VM {vmid} deleted successfully",
                "upid": result if isinstance(result, str) else None,
            }
            return [Content(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            self._handle_error(f"delete VM {vmid}", e)
