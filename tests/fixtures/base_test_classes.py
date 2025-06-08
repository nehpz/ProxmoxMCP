"""
Base test classes following SOLID principles.

Provides extensible base classes that can be inherited and extended
without modification (Open/Closed Principle).
"""
import pytest
from unittest.mock import Mock
from typing import Dict, Any

from .mock_helpers import ProxmoxAPIMockBuilder, VMToolsMockHelper, ContainerToolsMockHelper, AssertionHelper
from .vm_data_factory import VMTestDataFactory, ContainerTestDataFactory


class BaseVMOperationTest:
    """Base class for VM operation tests.
    
    Follows Open/Closed Principle - can be extended for specific operations
    without modifying this base class. Provides common setup and utilities.
    """

    def setup_method(self):
        """Set up test method with fresh mocks.
        
        Each test gets a clean mock environment (test isolation).
        """
        self.mock_builder = ProxmoxAPIMockBuilder()
        self.assertion_helper = AssertionHelper()
        self.data_factory = VMTestDataFactory()

    def create_vm_tools_with_mock(self, mock_proxmox: Mock):
        """Create VMTools instance with mock dependency injection.
        
        Args:
            mock_proxmox: Mock ProxmoxAPI instance
            
        Returns:
            VMTools instance with injected mock
        """
        return VMToolsMockHelper.create_vm_tools_with_mock(mock_proxmox)

    def get_default_test_params(self) -> Dict[str, str]:
        """Get default test parameters for VM operations.
        
        Returns:
            Dict with default node and vmid
        """
        return {
            "node": "node1", 
            "vmid": "100"
        }


class BaseVMStartStopTest(BaseVMOperationTest):
    """Base class for VM start/stop operations.
    
    Extends base class with start/stop specific functionality.
    Demonstrates inheritance following Liskov Substitution Principle.
    """

    def setup_vm_for_start_test(self, **overrides) -> Mock:
        """Set up mock for VM start test scenario.
        
        Args:
            **overrides: Override default VM configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        status = overrides.pop("status", "stopped")
        return (self.mock_builder
                .with_vm_status(status=status, **overrides)
                .with_start_operation()
                .build())

    def setup_vm_for_stop_test(self, **overrides) -> Mock:
        """Set up mock for VM stop test scenario.
        
        Args:
            **overrides: Override default VM configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        status = overrides.pop("status", "running")
        return (self.mock_builder
                .with_vm_status(status=status, **overrides)
                .with_stop_operation()
                .build())

    def assert_start_operation_success(self, response: list, vmid: str = "100"):
        """Assert start operation was successful.
        
        Args:
            response: Operation response
            vmid: Expected VM ID
        """
        expected_message = f"VM {vmid} started successfully"
        self.assertion_helper.assert_success_response(response, expected_message)

    def assert_stop_operation_success(self, response: list, vmid: str = "100"):
        """Assert stop operation was successful.
        
        Args:
            response: Operation response  
            vmid: Expected VM ID
        """
        expected_message = f"VM {vmid} stopped successfully"
        self.assertion_helper.assert_success_response(response, expected_message)


class BaseVMLifecycleTest(BaseVMOperationTest):
    """Base class for VM lifecycle operations (create/delete).
    
    Extends base class with lifecycle-specific functionality.
    """

    def setup_vm_for_create_test(self, **overrides) -> Mock:
        """Set up mock for VM creation test scenario.
        
        Args:
            **overrides: Override default configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        return (self.mock_builder
                .with_vm_not_found_error()  # VM doesn't exist, good for creation
                .with_create_operation()
                .build())

    def setup_vm_for_delete_test(self, **overrides) -> Mock:
        """Set up mock for VM deletion test scenario.
        
        Args:
            **overrides: Override default configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        status = overrides.pop("status", "stopped")
        return (self.mock_builder
                .with_vm_status(status=status, **overrides)
                .with_delete_operation()
                .build())

    def assert_create_operation_success(self, response: list, vmid: str = "100", name: str = "test-vm"):
        """Assert create operation was successful.
        
        Args:
            response: Operation response
            vmid: Expected VM ID
            name: Expected VM name
        """
        expected_message = f"VM {vmid} ({name}) created successfully"
        self.assertion_helper.assert_success_response(response, expected_message)

    def assert_delete_operation_success(self, response: list, vmid: str = "100"):
        """Assert delete operation was successful.
        
        Args:
            response: Operation response
            vmid: Expected VM ID
        """
        expected_message = f"VM {vmid} deleted successfully"
        self.assertion_helper.assert_success_response(response, expected_message)


class BaseVMStateChangeTest(BaseVMOperationTest):
    """Base class for VM state change operations (shutdown/restart).
    
    Extends base class with state change specific functionality.
    """

    def setup_vm_for_shutdown_test(self, **overrides) -> Mock:
        """Set up mock for VM shutdown test scenario.
        
        Args:
            **overrides: Override default configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        status = overrides.pop("status", "running")
        return (self.mock_builder
                .with_vm_status(status=status, **overrides)
                .with_shutdown_operation()
                .build())

    def setup_vm_for_restart_test(self, **overrides) -> Mock:
        """Set up mock for VM restart test scenario.
        
        Args:
            **overrides: Override default configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        status = overrides.pop("status", "running")
        return (self.mock_builder
                .with_vm_status(status=status, **overrides)
                .with_restart_operation()
                .build())

    def assert_shutdown_operation_success(self, response: list, vmid: str = "100"):
        """Assert shutdown operation was successful.
        
        Args:
            response: Operation response
            vmid: Expected VM ID
        """
        expected_message = f"VM {vmid} shutdown initiated"
        self.assertion_helper.assert_success_response(response, expected_message)

    def assert_restart_operation_success(self, response: list, vmid: str = "100"):
        """Assert restart operation was successful.
        
        Args:
            response: Operation response
            vmid: Expected VM ID
        """
        expected_message = f"VM {vmid} reboot initiated"
        self.assertion_helper.assert_success_response(response, expected_message)


class BaseVMErrorTest(BaseVMOperationTest):
    """Base class for VM operation error testing.
    
    Provides common error testing functionality that can be extended
    for different types of error scenarios.
    """

    def setup_vm_already_running_error(self) -> Mock:
        """Set up mock for 'VM already running' error scenario.
        
        Returns:
            Mock configured to return running status
        """
        return (self.mock_builder
                .with_vm_status("running")
                .build())

    def setup_vm_already_stopped_error(self) -> Mock:
        """Set up mock for 'VM already stopped' error scenario.
        
        Returns:
            Mock configured to return stopped status
        """
        return (self.mock_builder
                .with_vm_status("stopped")
                .build())

    def setup_vm_not_found_error(self) -> Mock:
        """Set up mock for 'VM not found' error scenario.
        
        Returns:
            Mock configured to raise not found error
        """
        return (self.mock_builder
                .with_vm_not_found_error()
                .build())

    def setup_operation_failure_error(self, operation: str, error_message: str = "Operation failed") -> Mock:
        """Set up mock for operation failure scenario.
        
        Args:
            operation: Operation that should fail
            error_message: Error message to use
            
        Returns:
            Mock configured to raise operation error
        """
        return (self.mock_builder
                .with_operation_error(operation, error_message)
                .build())

    def assert_value_error_raised(self, expected_message: str):
        """Context manager for asserting ValueError with specific message.
        
        Args:
            expected_message: Expected error message substring
            
        Returns:
            pytest.raises context manager
        """
        return pytest.raises(ValueError, match=expected_message)

    def assert_runtime_error_raised(self, expected_message: str):
        """Context manager for asserting RuntimeError with specific message.
        
        Args:
            expected_message: Expected error message substring
            
        Returns:
            pytest.raises context manager
        """
        return pytest.raises(RuntimeError, match=expected_message)


class BaseContainerOperationTest:
    """Base class for container operation tests.
    
    Follows Open/Closed Principle - can be extended for specific operations
    without modifying this base class. Provides common setup and utilities.
    """

    def setup_method(self):
        """Set up test method with fresh mocks.
        
        Each test gets a clean mock environment (test isolation).
        """
        self.mock_builder = ProxmoxAPIMockBuilder()
        self.assertion_helper = AssertionHelper()
        self.data_factory = ContainerTestDataFactory()

    def create_container_tools_with_mock(self, mock_proxmox: Mock):
        """Create ContainerTools instance with mock dependency injection.
        
        Args:
            mock_proxmox: Mock ProxmoxAPI instance
            
        Returns:
            ContainerTools instance with injected mock
        """
        return ContainerToolsMockHelper.create_container_tools_with_mock(mock_proxmox)

    def get_default_test_params(self) -> Dict[str, str]:
        """Get default test parameters for container operations.
        
        Returns:
            Dict with default node and container ID
        """
        return {
            "node": "node1", 
            "vmid": "200"
        }


class BaseContainerListTest(BaseContainerOperationTest):
    """Base class for container listing operations.
    
    Extends base class with listing-specific functionality.
    Demonstrates inheritance following Liskov Substitution Principle.
    """

    def setup_single_node_with_containers(self, **overrides) -> Mock:
        """Set up mock for single node with containers scenario.
        
        Args:
            **overrides: Override default configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        node = overrides.pop("node", "node1")
        containers = overrides.pop("containers", None)
        return (self.mock_builder
                .with_container_nodes()
                .with_container_list(containers, node)
                .with_container_config()
                .build())

    def setup_multi_node_containers(self, **overrides) -> Mock:
        """Set up mock for multi-node container scenario.
        
        Args:
            **overrides: Override default configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        return (self.mock_builder
                .with_multi_node_containers()
                .with_container_config()
                .build())

    def setup_empty_container_list(self, **overrides) -> Mock:
        """Set up mock for empty container list scenario.
        
        Args:
            **overrides: Override default configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        return (self.mock_builder
                .with_container_nodes()
                .with_empty_container_list()
                .build())

    def setup_config_fallback_scenario(self, **overrides) -> Mock:
        """Set up mock for config fallback scenario.
        
        Args:
            **overrides: Override default configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        return (self.mock_builder
                .with_container_nodes()
                .with_container_list()
                .with_container_config_error()
                .build())

    def assert_container_list_response_format(self, response: list):
        """Assert container list response has correct format.
        
        Args:
            response: Response from container operation
        """
        assert len(response) == 1, "Expected single response content"
        assert hasattr(response[0], 'text'), "Expected response with text content"
        assert isinstance(response[0].text, str), "Expected text content as string"

    def assert_container_data_present(self, response: list, expected_count: int = None):
        """Assert container data is present in response.
        
        Args:
            response: Response from container operation
            expected_count: Expected number of containers (optional)
        """
        self.assert_container_list_response_format(response)
        
        response_text = response[0].text
        assert "📦" in response_text, "Expected container emoji in formatted response"
        
        if expected_count is not None:
            # Count occurrences of container entries
            container_count = response_text.count("📦") - 1  # Subtract 1 for header
            assert container_count == expected_count, f"Expected {expected_count} containers, found {container_count}"

    def assert_no_containers_response(self, response: list):
        """Assert response indicates no containers found.
        
        Args:
            response: Response from container operation
        """
        self.assert_container_list_response_format(response)
        response_text = response[0].text
        # Should have header but no individual container entries
        container_count = response_text.count("📦")
        assert container_count <= 1, "Expected no container entries (header only)"