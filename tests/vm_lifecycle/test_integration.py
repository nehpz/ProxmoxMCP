"""
Integration tests for full VM lifecycle operations.

Tests complete VM lifecycle scenarios following SOLID principles:
- Single Responsibility: Each test validates one complete workflow
- Open/Closed: Uses extensible base classes
- Liskov Substitution: Mocks maintain API contracts
- Interface Segregation: Focused integration scenarios
- Dependency Inversion: Tests depend on abstractions

These tests validate that VM operations work together correctly
in realistic scenarios rather than testing individual operations.
"""
import pytest
import json
from unittest.mock import Mock

from fixtures.base_test_classes import BaseVMOperationTest


class TestVMLifecycleComplete(BaseVMOperationTest):
    """Test complete VM lifecycle from creation to deletion.
    
    Follows SRP - tests complete lifecycle workflows.
    """

    @pytest.mark.asyncio
    async def test_complete_vm_lifecycle_create_start_stop_delete(self):
        """Test complete VM lifecycle: create → start → stop → delete."""
        # Arrange
        mock_proxmox = self._setup_complete_lifecycle_mock()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert - Create VM
        create_result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="lifecycle-test-vm"
        )
        self._assert_operation_success(create_result, "created successfully")
        
        # Act & Assert - Start VM
        start_result = await vm_tools.start_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        self._assert_operation_success(start_result, "started successfully")
        
        # Act & Assert - Stop VM
        stop_result = await vm_tools.stop_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        self._assert_operation_success(stop_result, "stopped successfully")
        
        # Act & Assert - Delete VM
        delete_result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        self._assert_operation_success(delete_result, "deleted successfully")

    @pytest.mark.asyncio
    async def test_vm_lifecycle_with_restart_operations(self):
        """Test VM lifecycle with restart operations: create → start → restart → shutdown → delete."""
        # Arrange
        mock_proxmox = self._setup_restart_lifecycle_mock()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert - Create VM
        create_result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="restart-test-vm"
        )
        self._assert_operation_success(create_result, "created successfully")
        
        # Act & Assert - Start VM
        start_result = await vm_tools.start_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        self._assert_operation_success(start_result, "started successfully")
        
        # Act & Assert - Restart VM
        restart_result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        self._assert_operation_success(restart_result, "reboot initiated")
        
        # Act & Assert - Shutdown VM
        shutdown_result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        self._assert_operation_success(shutdown_result, "shutdown initiated")
        
        # Act & Assert - Delete VM
        delete_result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        self._assert_operation_success(delete_result, "deleted successfully")

    @pytest.mark.asyncio
    async def test_vm_lifecycle_with_custom_configuration(self):
        """Test VM lifecycle with custom memory and CPU configuration."""
        # Arrange
        mock_proxmox = self._setup_custom_config_lifecycle_mock()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        custom_config = {
            "memory": 2048,
            "cores": 4
        }
        
        # Act & Assert - Create VM with custom config
        create_result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="custom-config-vm",
            **custom_config
        )
        self._assert_operation_success(create_result, "created successfully")
        
        # Verify custom configuration was applied
        create_call = mock_proxmox.nodes.return_value.qemu.post.call_args
        assert create_call.kwargs["memory"] == custom_config["memory"]
        assert create_call.kwargs["cores"] == custom_config["cores"]
        
        # Act & Assert - Start, stop, delete sequence
        await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])
        await vm_tools.stop_vm(node=params["node"], vmid=params["vmid"])
        delete_result = await vm_tools.delete_vm(node=params["node"], vmid=params["vmid"])
        self._assert_operation_success(delete_result, "deleted successfully")

    def _setup_complete_lifecycle_mock(self) -> Mock:
        """Set up mock for complete lifecycle test."""
        return (self.mock_builder
                .with_vm_not_found_error()  # For create (VM doesn't exist)
                .with_create_operation()
                .with_vm_status("stopped")  # After creation
                .with_start_operation()
                .with_vm_status("running")  # After start
                .with_stop_operation()
                .with_vm_status("stopped")  # After stop
                .with_delete_operation()
                .build())

    def _setup_restart_lifecycle_mock(self) -> Mock:
        """Set up mock for lifecycle test with restart operations."""
        return (self.mock_builder
                .with_vm_not_found_error()  # For create
                .with_create_operation()
                .with_vm_status("stopped")  # After creation
                .with_start_operation()
                .with_vm_status("running")  # After start
                .with_restart_operation()
                .with_vm_status("running")  # After restart
                .with_shutdown_operation()
                .with_vm_status("stopped")  # After shutdown
                .with_delete_operation()
                .build())

    def _setup_custom_config_lifecycle_mock(self) -> Mock:
        """Set up mock for lifecycle test with custom configuration."""
        return (self.mock_builder
                .with_vm_not_found_error()  # For create
                .with_create_operation()
                .with_vm_status("stopped")  # After creation
                .with_start_operation()
                .with_vm_status("running")  # After start
                .with_stop_operation()
                .with_vm_status("stopped")  # After stop
                .with_delete_operation()
                .build())

    def _assert_operation_success(self, result, expected_message_part):
        """Assert that an operation was successful."""
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert expected_message_part in response_data["message"]


class TestVMLifecycleErrorRecovery(BaseVMOperationTest):
    """Test VM lifecycle error scenarios and recovery.
    
    Follows SRP - tests error handling in lifecycle workflows.
    """

    @pytest.mark.asyncio
    async def test_lifecycle_handles_creation_failure_gracefully(self):
        """Test that lifecycle handles VM creation failure gracefully."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("create", "Storage not available")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Storage not available"):
            await vm_tools.create_vm(
                node=params["node"],
                vmid=params["vmid"],
                name="test-vm"
            )
        
        # Verify that no further operations are attempted after creation fails
        mock_proxmox.nodes.return_value.qemu.return_value.status.start.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_lifecycle_handles_start_failure_with_cleanup(self):
        """Test that lifecycle handles start failure and allows cleanup."""
        # Arrange
        mock_proxmox = self._setup_start_failure_lifecycle_mock()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert - Create VM successfully
        create_result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="test-vm"
        )
        self._assert_operation_success(create_result, "created successfully")
        
        # Act & Assert - Start VM fails
        with pytest.raises(RuntimeError, match="Insufficient memory"):
            await vm_tools.start_vm(
                node=params["node"],
                vmid=params["vmid"]
            )
        
        # Act & Assert - Cleanup by deleting VM should still work
        delete_result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        self._assert_operation_success(delete_result, "deleted successfully")

    @pytest.mark.asyncio
    async def test_lifecycle_prevents_invalid_state_transitions(self):
        """Test that lifecycle prevents invalid state transitions."""
        # Arrange
        mock_proxmox = self._setup_invalid_state_lifecycle_mock()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert - Try to start already running VM
        with pytest.raises(ValueError, match="already running"):
            await vm_tools.start_vm(
                node=params["node"],
                vmid=params["vmid"]
            )
        
        # Act & Assert - Try to stop already stopped VM
        with pytest.raises(ValueError, match="already stopped"):
            await vm_tools.stop_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    def _setup_start_failure_lifecycle_mock(self) -> Mock:
        """Set up mock for start failure lifecycle test."""
        return (self.mock_builder
                .with_vm_not_found_error()  # For create
                .with_create_operation()
                .with_vm_status("stopped")  # After creation
                .with_operation_error("start", "Insufficient memory to start VM")
                .with_delete_operation()  # Allow cleanup
                .build())

    def _setup_invalid_state_lifecycle_mock(self) -> Mock:
        """Set up mock for invalid state transitions test."""
        return (self.mock_builder
                .with_vm_status("running")  # VM is running for invalid start
                .with_vm_status("stopped")  # VM is stopped for invalid stop
                .build())


class TestVMLifecycleMultiNode(BaseVMOperationTest):
    """Test VM lifecycle operations across multiple nodes.
    
    Follows SRP - tests multi-node scenarios.
    """

    @pytest.mark.asyncio
    async def test_vm_operations_across_different_nodes(self):
        """Test VM operations work correctly on different nodes."""
        # Arrange
        mock_proxmox = self._setup_multi_node_lifecycle_mock()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        
        node1 = "node1"
        node2 = "node2" 
        vmid1 = "100"
        vmid2 = "200"
        
        # Act & Assert - Create VMs on different nodes
        create1_result = await vm_tools.create_vm(
            node=node1,
            vmid=vmid1,
            name="vm-node1"
        )
        self._assert_operation_success(create1_result, "created successfully")
        
        create2_result = await vm_tools.create_vm(
            node=node2,
            vmid=vmid2,
            name="vm-node2"
        )
        self._assert_operation_success(create2_result, "created successfully")
        
        # Act & Assert - Start VMs on their respective nodes
        start1_result = await vm_tools.start_vm(node=node1, vmid=vmid1)
        self._assert_operation_success(start1_result, "started successfully")
        
        start2_result = await vm_tools.start_vm(node=node2, vmid=vmid2)
        self._assert_operation_success(start2_result, "started successfully")
        
        # Act & Assert - Clean up both VMs
        await vm_tools.stop_vm(node=node1, vmid=vmid1)
        await vm_tools.stop_vm(node=node2, vmid=vmid2)
        
        delete1_result = await vm_tools.delete_vm(node=node1, vmid=vmid1)
        self._assert_operation_success(delete1_result, "deleted successfully")
        
        delete2_result = await vm_tools.delete_vm(node=node2, vmid=vmid2)
        self._assert_operation_success(delete2_result, "deleted successfully")

    def _setup_multi_node_lifecycle_mock(self) -> Mock:
        """Set up mock for multi-node lifecycle test."""
        return (self.mock_builder
                .with_vm_not_found_error()  # For creates
                .with_create_operation()
                .with_vm_status("stopped")  # After creation
                .with_start_operation()
                .with_vm_status("running")  # After start
                .with_stop_operation()
                .with_vm_status("stopped")  # After stop
                .with_delete_operation()
                .build())


class TestVMLifecyclePerformance(BaseVMOperationTest):
    """Test VM lifecycle performance characteristics.
    
    Follows SRP - tests performance-related scenarios.
    """

    @pytest.mark.asyncio
    async def test_lifecycle_handles_task_monitoring(self):
        """Test that lifecycle operations return task IDs for monitoring."""
        # Arrange
        expected_task_ids = {
            "create": "UPID:node1:00001234:56789ABC:timestamp:qmcreate:100:user@pve:",
            "start": "UPID:node1:00001235:56789ABD:timestamp:qmstart:100:user@pve:",
            "stop": "UPID:node1:00001236:56789ABE:timestamp:qmstop:100:user@pve:",
            "delete": "UPID:node1:00001237:56789ABF:timestamp:qmdestroy:100:user@pve:"
        }
        
        mock_proxmox = self._setup_task_monitoring_lifecycle_mock(expected_task_ids)
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert - Each operation returns expected task ID
        create_result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="task-test-vm"
        )
        create_data = json.loads(create_result[0].text)
        assert create_data["upid"] == expected_task_ids["create"]
        
        start_result = await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])
        start_data = json.loads(start_result[0].text)
        assert start_data["upid"] == expected_task_ids["start"]
        
        stop_result = await vm_tools.stop_vm(node=params["node"], vmid=params["vmid"])
        stop_data = json.loads(stop_result[0].text)
        assert stop_data["upid"] == expected_task_ids["stop"]
        
        delete_result = await vm_tools.delete_vm(node=params["node"], vmid=params["vmid"])
        delete_data = json.loads(delete_result[0].text)
        assert delete_data["upid"] == expected_task_ids["delete"]

    @pytest.mark.asyncio
    async def test_lifecycle_maintains_consistent_response_format(self):
        """Test that all lifecycle operations maintain consistent response format."""
        # Arrange
        mock_proxmox = self._setup_consistent_format_lifecycle_mock()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act - Perform complete lifecycle
        operations = []
        
        create_result = await vm_tools.create_vm(node=params["node"], vmid=params["vmid"], name="test-vm")
        operations.append(("create", create_result))
        
        start_result = await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])
        operations.append(("start", start_result))
        
        stop_result = await vm_tools.stop_vm(node=params["node"], vmid=params["vmid"])
        operations.append(("stop", stop_result))
        
        delete_result = await vm_tools.delete_vm(node=params["node"], vmid=params["vmid"])
        operations.append(("delete", delete_result))
        
        # Assert - All operations have consistent response format
        for operation_name, result in operations:
            assert len(result) == 1, f"{operation_name} should return single response"
            
            response_data = json.loads(result[0].text)
            
            # Verify consistent structure
            assert "success" in response_data, f"{operation_name} missing 'success' field"
            assert "message" in response_data, f"{operation_name} missing 'message' field"
            assert isinstance(response_data["success"], bool), f"{operation_name} 'success' not boolean"
            assert isinstance(response_data["message"], str), f"{operation_name} 'message' not string"
            assert response_data["success"] is True, f"{operation_name} operation should succeed"

    def _setup_task_monitoring_lifecycle_mock(self, task_ids) -> Mock:
        """Set up mock for task monitoring lifecycle test."""
        return (self.mock_builder
                .with_vm_not_found_error()  # For create
                .with_create_operation(task_ids["create"])
                .with_vm_status("stopped")  # After creation
                .with_start_operation(task_ids["start"])
                .with_vm_status("running")  # After start
                .with_stop_operation(task_ids["stop"])
                .with_vm_status("stopped")  # After stop
                .with_delete_operation(task_ids["delete"])
                .build())

    def _setup_consistent_format_lifecycle_mock(self) -> Mock:
        """Set up mock for consistent format lifecycle test."""
        return (self.mock_builder
                .with_vm_not_found_error()  # For create
                .with_create_operation()
                .with_vm_status("stopped")  # After creation
                .with_start_operation()
                .with_vm_status("running")  # After start
                .with_stop_operation()
                .with_vm_status("stopped")  # After stop
                .with_delete_operation()
                .build())