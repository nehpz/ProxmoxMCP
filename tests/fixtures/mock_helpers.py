"""
Mock helper utilities following SOLID principles.

Provides focused mock configurations that implement only the interfaces
needed for specific tests (Interface Segregation Principle).
"""
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional, Union
from .vm_data_factory import VMTestDataFactory, ProxmoxAPIResponseFactory, ContainerTestDataFactory


class ProxmoxAPIMockBuilder:
    """Builder for creating focused ProxmoxAPI mocks.
    
    Follows Interface Segregation Principle by allowing creation of
    minimal mocks that only implement methods needed for specific tests.
    """

    def __init__(self):
        """Initialize the mock builder."""
        self.mock = Mock()
        self._configure_base_structure()

    def _configure_base_structure(self) -> None:
        """Configure the basic ProxmoxAPI mock structure."""
        # Create the chained method structure for VMs and containers
        self.mock.nodes = Mock()
        self.mock.nodes.return_value = Mock()
        self.mock.nodes.return_value.qemu = Mock()
        self.mock.nodes.return_value.qemu.return_value = Mock()
        self.mock.nodes.return_value.lxc = Mock()
        self.mock.nodes.return_value.lxc.return_value = Mock()

    def with_vm_status(
        self, 
        status: str = "stopped", 
        vmid: str = "100",
        **overrides: Any
    ) -> "ProxmoxAPIMockBuilder":
        """Configure mock to return specific VM status.
        
        Args:
            status: VM status to return
            vmid: VM ID
            **overrides: Additional status fields
            
        Returns:
            Self for method chaining
        """
        status_response = VMTestDataFactory.create_vm_status_response(
            status=status, vmid=vmid, **overrides
        )
        self.mock.nodes.return_value.qemu.return_value.status.current.get.return_value = status_response
        return self

    def with_start_operation(self, task_id: Optional[str] = None) -> "ProxmoxAPIMockBuilder":
        """Configure mock for VM start operation.
        
        Args:
            task_id: Custom task ID (optional)
            
        Returns:
            Self for method chaining
        """
        if task_id is None:
            task_id = VMTestDataFactory.create_task_response()
        self.mock.nodes.return_value.qemu.return_value.status.start.post.return_value = task_id
        return self

    def with_stop_operation(self, task_id: Optional[str] = None) -> "ProxmoxAPIMockBuilder":
        """Configure mock for VM stop operation.
        
        Args:
            task_id: Custom task ID (optional)
            
        Returns:
            Self for method chaining
        """
        if task_id is None:
            task_id = VMTestDataFactory.create_task_response()
        self.mock.nodes.return_value.qemu.return_value.status.stop.post.return_value = task_id
        return self

    def with_shutdown_operation(self, task_id: Optional[str] = None) -> "ProxmoxAPIMockBuilder":
        """Configure mock for VM shutdown operation.
        
        Args:
            task_id: Custom task ID (optional)
            
        Returns:
            Self for method chaining
        """
        if task_id is None:
            task_id = VMTestDataFactory.create_task_response()
        self.mock.nodes.return_value.qemu.return_value.status.shutdown.post.return_value = task_id
        return self

    def with_restart_operation(self, task_id: Optional[str] = None) -> "ProxmoxAPIMockBuilder":
        """Configure mock for VM restart operation.
        
        Args:
            task_id: Custom task ID (optional)
            
        Returns:
            Self for method chaining
        """
        if task_id is None:
            task_id = VMTestDataFactory.create_task_response()
        self.mock.nodes.return_value.qemu.return_value.status.reboot.post.return_value = task_id
        return self

    def with_create_operation(self) -> "ProxmoxAPIMockBuilder":
        """Configure mock for VM creation operation.
        
        Returns:
            Self for method chaining
        """
        # Create operation doesn't return a task ID, just succeeds
        self.mock.nodes.return_value.qemu.post.return_value = None
        return self

    def with_delete_operation(self, task_id: Optional[str] = None) -> "ProxmoxAPIMockBuilder":
        """Configure mock for VM deletion operation.
        
        Args:
            task_id: Custom task ID (optional)
            
        Returns:
            Self for method chaining
        """
        if task_id is None:
            task_id = VMTestDataFactory.create_task_response()
        self.mock.nodes.return_value.qemu.return_value.delete.return_value = task_id
        return self

    def with_vm_not_found_error(self) -> "ProxmoxAPIMockBuilder":
        """Configure mock to raise VM not found error.
        
        Returns:
            Self for method chaining
        """
        error = Exception("VM not found")
        self.mock.nodes.return_value.qemu.return_value.status.current.get.side_effect = error
        return self

    def with_operation_error(self, operation: str, error_message: str = "Operation failed") -> "ProxmoxAPIMockBuilder":
        """Configure mock to raise error for specific operation.
        
        Args:
            operation: Operation name (start, stop, etc.)
            error_message: Error message to raise
            
        Returns:
            Self for method chaining
        """
        error = Exception(error_message)
        
        operation_map = {
            "start": self.mock.nodes.return_value.qemu.return_value.status.start.post,
            "stop": self.mock.nodes.return_value.qemu.return_value.status.stop.post,
            "shutdown": self.mock.nodes.return_value.qemu.return_value.status.shutdown.post,
            "restart": self.mock.nodes.return_value.qemu.return_value.status.reboot.post,
            "create": self.mock.nodes.return_value.qemu.post,
            "delete": self.mock.nodes.return_value.qemu.return_value.delete,
        }
        
        if operation in operation_map:
            operation_map[operation].side_effect = error
        
        return self

    def with_container_nodes(self, nodes: list = None) -> "ProxmoxAPIMockBuilder":
        """Configure mock to return specific nodes for container listing.
        
        Args:
            nodes: List of nodes (optional, uses default if None)
            
        Returns:
            Self for method chaining
        """
        if nodes is None:
            nodes = ContainerTestDataFactory.create_single_node_response()
        self.mock.nodes.get.return_value = nodes
        return self

    def with_container_list(self, containers: list = None, node: str = "node1") -> "ProxmoxAPIMockBuilder":
        """Configure mock to return specific container list for a node.
        
        Args:
            containers: List of containers (optional, uses default if None)
            node: Node name (default: "node1")
            
        Returns:
            Self for method chaining
        """
        if containers is None:
            containers = ContainerTestDataFactory.create_container_list_response(node)
        self.mock.nodes.return_value.lxc.get.return_value = containers
        return self

    def with_container_config(self, vmid: str = "200", config: Dict[str, Any] = None) -> "ProxmoxAPIMockBuilder":
        """Configure mock to return specific container configuration.
        
        Args:
            vmid: Container ID (default: "200")
            config: Container config (optional, uses default if None)
            
        Returns:
            Self for method chaining
        """
        if config is None:
            config = ContainerTestDataFactory.create_container_config_response(vmid)
        self.mock.nodes.return_value.lxc.return_value.config.get.return_value = config
        return self

    def with_container_config_error(self, error_message: str = "Config access failed") -> "ProxmoxAPIMockBuilder":
        """Configure mock to raise error when accessing container config.
        
        Args:
            error_message: Error message to raise
            
        Returns:
            Self for method chaining
        """
        error = Exception(error_message)
        self.mock.nodes.return_value.lxc.return_value.config.get.side_effect = error
        return self

    def with_empty_container_list(self) -> "ProxmoxAPIMockBuilder":
        """Configure mock to return empty container list.
        
        Returns:
            Self for method chaining
        """
        empty_list = ContainerTestDataFactory.create_empty_container_response()
        self.mock.nodes.return_value.lxc.get.return_value = empty_list
        return self

    def with_multi_node_containers(self) -> "ProxmoxAPIMockBuilder":
        """Configure mock for multi-node container scenario.
        
        Returns:
            Self for method chaining
        """
        nodes = ContainerTestDataFactory.create_multi_node_response()
        self.mock.nodes.get.return_value = nodes
        
        # Configure different container lists for different nodes
        def get_containers_for_node(*args, **kwargs):
            # Return different containers based on which node is being accessed
            return ContainerTestDataFactory.create_container_list_response(args[0] if args else "node1")
        
        self.mock.nodes.return_value.lxc.get.side_effect = get_containers_for_node
        return self

    def build(self) -> Mock:
        """Build and return the configured mock.
        
        Returns:
            Configured ProxmoxAPI mock
        """
        return self.mock


class VMToolsMockHelper:
    """Helper for creating VMTools instances with mocked dependencies.
    
    Follows Dependency Inversion Principle by injecting mock dependencies.
    """

    @staticmethod
    def create_vm_tools_with_mock(mock_proxmox: Mock):
        """Create VMTools instance with injected mock.
        
        Args:
            mock_proxmox: Mock ProxmoxAPI instance
            
        Returns:
            VMTools instance with mock dependency
        """
        from proxmox_mcp.tools.vm import VMTools
        return VMTools(mock_proxmox)

    @staticmethod
    def create_minimal_mock_for_operation(operation: str, **kwargs) -> Mock:
        """Create minimal mock for specific operation (ISP compliance).
        
        Args:
            operation: Operation name
            **kwargs: Operation-specific parameters
            
        Returns:
            Minimal mock configured for the specific operation
        """
        builder = ProxmoxAPIMockBuilder()
        
        # Configure based on operation
        if operation == "start":
            builder.with_vm_status("stopped").with_start_operation()
        elif operation == "stop":
            builder.with_vm_status("running").with_stop_operation()
        elif operation == "shutdown":
            builder.with_vm_status("running").with_shutdown_operation()
        elif operation == "restart":
            builder.with_vm_status("running").with_restart_operation()
        elif operation == "create":
            builder.with_vm_not_found_error().with_create_operation()
        elif operation == "delete":
            builder.with_vm_status("stopped").with_delete_operation()
        
        return builder.build()


class ContainerToolsMockHelper:
    """Helper for creating ContainerTools instances with mocked dependencies.
    
    Follows Dependency Inversion Principle by injecting mock dependencies.
    """

    @staticmethod
    def create_container_tools_with_mock(mock_proxmox: Mock):
        """Create ContainerTools instance with injected mock.
        
        Args:
            mock_proxmox: Mock ProxmoxAPI instance
            
        Returns:
            ContainerTools instance with mock dependency
        """
        from proxmox_mcp.tools.container import ContainerTools
        return ContainerTools(mock_proxmox)

    @staticmethod
    def create_minimal_mock_for_container_operation(scenario: str, **kwargs) -> Mock:
        """Create minimal mock for specific container operation (ISP compliance).
        
        Args:
            scenario: Test scenario name
            **kwargs: Scenario-specific parameters
            
        Returns:
            Minimal mock configured for the specific scenario
        """
        builder = ProxmoxAPIMockBuilder()
        
        # Configure based on scenario
        if scenario == "single_node_with_containers":
            builder.with_container_nodes().with_container_list().with_container_config()
        elif scenario == "multi_node_containers":
            builder.with_multi_node_containers()
        elif scenario == "empty_containers":
            builder.with_container_nodes().with_empty_container_list()
        elif scenario == "config_fallback":
            builder.with_container_nodes().with_container_list().with_container_config_error()
        
        return builder.build()


class AssertionHelper:
    """Helper for making consistent test assertions.
    
    Provides reusable assertion methods to maintain consistency
    across tests (DRY principle).
    """

    @staticmethod
    def assert_success_response(response: list, expected_message: str = None):
        """Assert that response indicates success.
        
        Args:
            response: Response from VM operation
            expected_message: Expected success message (optional)
        """
        import json
        
        assert len(response) == 1, "Expected single response content"
        
        response_data = json.loads(response[0].text)
        assert response_data["success"] is True, "Expected success=True"
        
        if expected_message:
            assert expected_message in response_data["message"], f"Expected message containing '{expected_message}'"

    @staticmethod
    def assert_api_call_made(mock_proxmox: Mock, operation: str, node: str, vmid: str):
        """Assert that correct API call was made.
        
        Args:
            mock_proxmox: Mock ProxmoxAPI instance
            operation: Expected operation
            node: Expected node name
            vmid: Expected VM ID
        """
        # Verify node and vmid were called correctly
        mock_proxmox.nodes.assert_called_with(node)
        mock_proxmox.nodes.return_value.qemu.assert_called_with(vmid)
        
        # Verify operation-specific calls
        operation_map = {
            "start": mock_proxmox.nodes.return_value.qemu.return_value.status.start.post,
            "stop": mock_proxmox.nodes.return_value.qemu.return_value.status.stop.post,
            "shutdown": mock_proxmox.nodes.return_value.qemu.return_value.status.shutdown.post,
            "restart": mock_proxmox.nodes.return_value.qemu.return_value.status.reboot.post,
            "delete": mock_proxmox.nodes.return_value.qemu.return_value.delete,
        }
        
        if operation in operation_map:
            operation_map[operation].assert_called_once()

    @staticmethod
    def assert_status_check_made(mock_proxmox: Mock):
        """Assert that VM status check was made.
        
        Args:
            mock_proxmox: Mock ProxmoxAPI instance  
        """
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.assert_called_once()