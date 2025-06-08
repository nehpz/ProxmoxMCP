"""
Base test classes following SOLID principles.

Provides extensible base classes that can be inherited and extended
without modification (Open/Closed Principle).
"""
import pytest
from unittest.mock import Mock
from typing import Dict, Any

from .mock_helpers import ProxmoxAPIMockBuilder, VMToolsMockHelper, AssertionHelper
from .vm_data_factory import VMTestDataFactory


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
        return (self.mock_builder
                .with_vm_status("stopped", **overrides)
                .with_start_operation()
                .build())

    def setup_vm_for_stop_test(self, **overrides) -> Mock:
        """Set up mock for VM stop test scenario.
        
        Args:
            **overrides: Override default VM configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        return (self.mock_builder
                .with_vm_status("running", **overrides)
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
        return (self.mock_builder
                .with_vm_status("stopped", **overrides)
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
        return (self.mock_builder
                .with_vm_status("running", **overrides)
                .with_shutdown_operation()
                .build())

    def setup_vm_for_restart_test(self, **overrides) -> Mock:
        """Set up mock for VM restart test scenario.
        
        Args:
            **overrides: Override default configuration
            
        Returns:
            Configured mock ProxmoxAPI
        """
        return (self.mock_builder
                .with_vm_status("running", **overrides)
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