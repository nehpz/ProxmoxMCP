"""
VM test data factory following SOLID principles.

Provides factory methods for creating consistent test data that can be
extended without modification (Open/Closed Principle).
"""
from typing import Dict, Any, Optional


class VMTestDataFactory:
    """Factory for creating VM test data with configurable parameters.
    
    Follows Open/Closed Principle - can be extended for new scenarios
    without modifying existing factory methods.
    """

    @staticmethod
    def create_vm_config(
        vmid: str = "100",
        name: str = "test-vm",
        status: str = "stopped",
        memory: int = 512,
        cores: int = 1,
        node: str = "node1",
        **overrides: Any
    ) -> Dict[str, Any]:
        """Create a VM configuration for testing.
        
        Args:
            vmid: VM ID (default: "100")
            name: VM name (default: "test-vm")
            status: VM status (default: "stopped")
            memory: Memory in MB (default: 512)
            cores: CPU cores (default: 1)
            node: Node name (default: "node1")
            **overrides: Additional or override values
            
        Returns:
            Dict containing VM configuration data
        """
        config = {
            "vmid": vmid,
            "name": name,
            "status": status,
            "memory": memory,
            "cores": cores,
            "node": node,
            "maxmem": memory * 1024 * 1024,  # Convert MB to bytes
            "mem": 0 if status == "stopped" else memory * 1024 * 1024 // 4,  # 25% usage when running
        }
        config.update(overrides)
        return config

    @staticmethod
    def create_vm_status_response(
        status: str = "stopped",
        vmid: str = "100",
        **overrides: Any
    ) -> Dict[str, Any]:
        """Create a VM status API response.
        
        Args:
            status: VM status (stopped, running, paused)
            vmid: VM ID
            **overrides: Additional response fields
            
        Returns:
            Dict matching Proxmox API status response format
        """
        response = {
            "status": status,
            "vmid": vmid,
            "uptime": 0 if status == "stopped" else 3600,
            "pid": None if status == "stopped" else 12345,
        }
        response.update(overrides)
        return response

    @staticmethod 
    def create_task_response(
        task_id: str = "UPID:node1:00001234:12345678:12345678:qmstart:100:user@pve:",
        **overrides: Any
    ) -> str:
        """Create a Proxmox task ID response.
        
        Args:
            task_id: Task identifier string
            **overrides: Additional fields (currently unused for string response)
            
        Returns:
            Task ID string
        """
        return task_id

    @staticmethod
    def create_vm_list_response(
        vm_configs: Optional[list] = None,
        **overrides: Any
    ) -> list:
        """Create a VM list API response.
        
        Args:
            vm_configs: List of VM configurations
            **overrides: Additional fields
            
        Returns:
            List of VM configurations matching Proxmox API format
        """
        if vm_configs is None:
            vm_configs = [
                VMTestDataFactory.create_vm_config(vmid="100", name="vm1", status="running"),
                VMTestDataFactory.create_vm_config(vmid="101", name="vm2", status="stopped"),
            ]
        return vm_configs

    @staticmethod
    def create_error_response(
        error_code: int = 400,
        error_message: str = "Bad Request",
        **overrides: Any
    ) -> Dict[str, Any]:
        """Create an error response for testing error scenarios.
        
        Args:
            error_code: HTTP error code
            error_message: Error message
            **overrides: Additional error fields
            
        Returns:
            Dict containing error information
        """
        error = {
            "code": error_code,
            "message": error_message,
            "errors": [],
        }
        error.update(overrides)
        return error


class VMOperationResponseFactory:
    """Factory for creating VM operation API responses.
    
    Separate factory for operation responses to maintain Single Responsibility.
    """

    @staticmethod
    def create_success_response(
        vmid: str = "100",
        operation: str = "start",
        **overrides: Any
    ) -> Dict[str, Any]:
        """Create a successful VM operation response.
        
        Args:
            vmid: VM ID
            operation: Operation name (start, stop, shutdown, restart, delete)
            **overrides: Additional response fields
            
        Returns:
            Dict containing success response
        """
        response = {
            "success": True,
            "message": f"VM {vmid} {operation} {'initiated' if operation in ['shutdown', 'restart'] else 'successfully'}",
            "upid": VMTestDataFactory.create_task_response(),
        }
        response.update(overrides)
        return response

    @staticmethod
    def create_creation_response(
        vmid: str = "100",
        name: str = "test-vm",
        **overrides: Any
    ) -> Dict[str, Any]:
        """Create a VM creation success response.
        
        Args:
            vmid: Created VM ID
            name: Created VM name
            **overrides: Additional response fields
            
        Returns:
            Dict containing creation response
        """
        response = {
            "success": True,
            "message": f"VM {vmid} ({name}) created successfully",
            "vmid": vmid,
        }
        response.update(overrides)
        return response


class ProxmoxAPIResponseFactory:
    """Factory for creating realistic Proxmox API responses.
    
    Ensures mock responses match real API behavior (Liskov Substitution Principle).
    """

    @staticmethod
    def create_node_list() -> list:
        """Create a node list response."""
        return [
            {"node": "node1", "status": "online", "type": "node"},
            {"node": "node2", "status": "online", "type": "node"},
        ]

    @staticmethod
    def create_qemu_vm_list(node: str = "node1") -> list:
        """Create a QEMU VM list for a specific node."""
        return [
            {
                "vmid": 100,
                "name": "test-vm-1",
                "status": "running",
                "mem": 536870912,  # 512MB in bytes
                "maxmem": 1073741824,  # 1GB in bytes
                "cpus": 2,
            },
            {
                "vmid": 101,
                "name": "test-vm-2", 
                "status": "stopped",
                "mem": 0,
                "maxmem": 536870912,  # 512MB in bytes
                "cpus": 1,
            }
        ]

    @staticmethod
    def create_vm_config(vmid: str = "100") -> Dict[str, Any]:
        """Create a VM configuration response."""
        return {
            "cores": 2,
            "memory": 1024,
            "name": f"test-vm-{vmid}",
            "ostype": "l26",
            "sockets": 1,
            "vmgenid": "12345678-1234-1234-1234-123456789012",
        }


class ContainerTestDataFactory:
    """Factory for creating container test data with configurable parameters.
    
    Follows Open/Closed Principle - can be extended for new scenarios
    without modifying existing factory methods.
    """

    @staticmethod
    def create_container_list_response(node: str = "node1") -> list:
        """Create a container list response for a specific node.
        
        Args:
            node: Node name (default: "node1")
            
        Returns:
            List of container configurations
        """
        return [
            {
                "vmid": "200",
                "name": "web-container",
                "status": "running",
                "mem": 268435456,  # 256MB in bytes
                "maxmem": 536870912,  # 512MB in bytes
                "type": "lxc",
                "node": node,
            },
            {
                "vmid": "201", 
                "name": "db-container",
                "status": "stopped",
                "mem": 0,
                "maxmem": 1073741824,  # 1GB in bytes
                "type": "lxc",
                "node": node,
            }
        ]

    @staticmethod
    def create_container_config_response(
        vmid: str = "200", 
        cores: int = 2,
        template: str = "ubuntu-20.04",
        **overrides: Any
    ) -> Dict[str, Any]:
        """Create container configuration response.
        
        Args:
            vmid: Container ID (default: "200")
            cores: CPU cores (default: 2)
            template: Container template (default: "ubuntu-20.04")
            **overrides: Additional config fields
            
        Returns:
            Dict containing container configuration
        """
        config = {
            "cores": cores,
            "memory": 512,
            "rootfs": "local-lvm:vm-200-disk-0,size=8G",
            "template": template,
            "ostype": "ubuntu",
            "arch": "amd64",
        }
        config.update(overrides)
        return config

    @staticmethod
    def create_single_node_response(node: str = "node1") -> list:
        """Create single node response for testing.
        
        Args:
            node: Node name (default: "node1")
            
        Returns:
            List containing single node
        """
        return [{"node": node, "status": "online", "type": "node"}]

    @staticmethod
    def create_multi_node_response() -> list:
        """Create multi-node response for testing.
        
        Returns:
            List containing multiple nodes
        """
        return [
            {"node": "node1", "status": "online", "type": "node"},
            {"node": "node2", "status": "online", "type": "node"},
        ]

    @staticmethod
    def create_empty_container_response() -> list:
        """Create empty container list response.
        
        Returns:
            Empty list
        """
        return []