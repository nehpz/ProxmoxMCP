"""
Atomic tests for VM deletion operation.

Tests the delete_vm method following SOLID principles:
- Single Responsibility: Each test validates one specific behavior
- Open/Closed: Uses extensible base classes
- Liskov Substitution: Mocks maintain API contracts
- Interface Segregation: Minimal mocks per test
- Dependency Inversion: Tests depend on abstractions
"""
import pytest
import json
from unittest.mock import Mock

from fixtures.base_test_classes import BaseVMLifecycleTest


class TestDeleteVMSuccess(BaseVMLifecycleTest):
    """Test successful VM deletion scenarios.
    
    Follows SRP - only tests successful deletion operations.
    """

    @pytest.mark.asyncio
    async def test_delete_vm_with_stopped_vm_returns_success(self):
        """Test deleting a stopped VM returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        self.assert_delete_operation_success(result, params["vmid"])
        self.assertion_helper.assert_api_call_made(mock_proxmox, "delete", params["node"], params["vmid"])
        self.assertion_helper.assert_status_check_made(mock_proxmox)

    @pytest.mark.asyncio
    async def test_delete_vm_returns_task_id_in_response(self):
        """Test that delete VM returns task ID for monitoring."""
        # Arrange
        expected_task_id = "UPID:node1:00001234:56789ABC:timestamp:qmdestroy:100:user@pve:"
        mock_proxmox = (self.mock_builder
                       .with_vm_status("stopped")
                       .with_delete_operation(expected_task_id)
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["upid"] == expected_task_id

    @pytest.mark.asyncio
    async def test_delete_vm_with_different_node_succeeds(self):
        """Test deleting VM on different node succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_node = "node2"
        
        # Act
        result = await vm_tools.delete_vm(
            node=custom_node,
            vmid="100"
        )
        
        # Assert
        self.assert_delete_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "delete", custom_node, "100")

    @pytest.mark.asyncio
    async def test_delete_vm_with_different_vmid_succeeds(self):
        """Test deleting VM with different VMID succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_vmid = "555"
        
        # Act
        result = await vm_tools.delete_vm(
            node="node1",
            vmid=custom_vmid
        )
        
        # Assert
        self.assert_delete_operation_success(result, custom_vmid)
        self.assertion_helper.assert_api_call_made(mock_proxmox, "delete", "node1", custom_vmid)

    @pytest.mark.asyncio
    async def test_delete_vm_removes_all_vm_resources(self):
        """Test that delete VM removes all VM resources."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        self.assert_delete_operation_success(result, params["vmid"])
        
        # Verify delete was called on VM endpoint
        mock_proxmox.nodes.return_value.qemu.return_value.delete.assert_called_once()


class TestDeleteVMErrors(BaseVMLifecycleTest):
    """Test VM deletion error scenarios.
    
    Follows SRP - only tests error conditions.
    """

    @pytest.mark.asyncio
    async def test_delete_vm_with_running_vm_raises_value_error(self):
        """Test deleting running VM raises ValueError."""
        # Arrange
        mock_proxmox = (self.mock_builder
                       .with_vm_status("running")
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("must be stopped"):
            await vm_tools.delete_vm(
                node=params["node"],
                vmid=params["vmid"]
            )
        
        # Verify status check was made but delete was not called
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        mock_proxmox.nodes.return_value.qemu.return_value.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_vm_with_nonexistent_vm_raises_runtime_error(self):
        """Test deleting non-existent VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_vm_not_found_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM not found"):
            await vm_tools.delete_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_delete_vm_with_locked_vm_raises_runtime_error(self):
        """Test deleting locked VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("delete", "VM is locked")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM is locked"):
            await vm_tools.delete_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_delete_vm_with_dependent_resources_raises_runtime_error(self):
        """Test deleting VM with dependent resources raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("delete", "VM has snapshots")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM has snapshots"):
            await vm_tools.delete_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_delete_vm_with_api_failure_raises_runtime_error(self):
        """Test deleting VM with API failure raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("delete", "Failed to destroy VM")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Failed to destroy VM"):
            await vm_tools.delete_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_delete_vm_with_storage_error_raises_runtime_error(self):
        """Test deleting VM with storage error raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("delete", "Storage unavailable")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Storage unavailable"):
            await vm_tools.delete_vm(
                node=params["node"],
                vmid=params["vmid"]
            )


class TestDeleteVMResponseFormat(BaseVMLifecycleTest):
    """Test VM deletion response format validation.
    
    Follows SRP - only tests response format compliance.
    """

    @pytest.mark.asyncio
    async def test_delete_vm_response_contains_required_fields(self):
        """Test that delete VM response contains all required fields."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        # Verify required response fields
        assert "success" in response_data
        assert "message" in response_data
        assert "upid" in response_data
        
        # Verify field values
        assert response_data["success"] is True
        assert "deleted successfully" in response_data["message"]
        assert response_data["upid"] is not None

    @pytest.mark.asyncio
    async def test_delete_vm_response_format_matches_api_standard(self):
        """Test that delete VM response format matches API standard."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        
        # Verify response structure matches expected format
        expected_structure = {
            "success": bool,
            "message": str,
            "upid": (str, type(None))  # Can be string or None
        }
        
        for field, expected_type in expected_structure.items():
            assert field in response_data, f"Missing required field: {field}"
            if isinstance(expected_type, tuple):
                assert type(response_data[field]) in expected_type, f"Field {field} has wrong type"
            else:
                assert isinstance(response_data[field], expected_type), f"Field {field} has wrong type"

    @pytest.mark.asyncio
    async def test_delete_vm_response_is_valid_json(self):
        """Test that delete VM response is valid JSON format."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        assert len(result) == 1
        
        # Should not raise exception when parsing JSON
        try:
            response_data = json.loads(result[0].text)
            assert isinstance(response_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

    @pytest.mark.asyncio
    async def test_delete_vm_response_message_includes_vmid(self):
        """Test that delete VM response message includes the VM ID."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        test_vmid = "789"
        
        # Act
        result = await vm_tools.delete_vm(
            node="node1",
            vmid=test_vmid
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert test_vmid in response_data["message"]


class TestDeleteVMStatusChecks(BaseVMLifecycleTest):
    """Test VM deletion status validation behavior.
    
    Follows SRP - only tests status checking logic.
    """

    @pytest.mark.asyncio
    async def test_delete_vm_checks_current_status_before_operation(self):
        """Test that delete VM checks current status before attempting deletion."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Status check should be called before delete operation
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        
        # Verify call order: status check before delete
        handle = mock_proxmox.nodes.return_value.qemu.return_value
        assert handle.status.current.get.call_count == 1
        assert handle.delete.call_count == 1

    @pytest.mark.asyncio
    async def test_delete_vm_validates_stopped_status_requirement(self):
        """Test that delete VM validates VM must be in stopped state."""
        # Arrange - VM is in stopped state
        mock_proxmox = self.setup_vm_for_delete_test(status="stopped")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed for stopped VM
        self.assert_delete_operation_success(result, params["vmid"])

    @pytest.mark.asyncio
    async def test_delete_vm_rejects_running_status(self):
        """Test that delete VM rejects VMs in running state."""
        # Arrange - VM is in running state
        mock_proxmox = (self.mock_builder
                       .with_vm_status("running")
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("must be stopped"):
            await vm_tools.delete_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_delete_vm_rejects_paused_status(self):
        """Test that delete VM rejects VMs in paused state."""
        # Arrange - VM is in paused state
        mock_proxmox = (self.mock_builder
                       .with_vm_status("paused")
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("must be stopped"):
            await vm_tools.delete_vm(
                node=params["node"],
                vmid=params["vmid"]
            )


class TestDeleteVMSafetyChecks(BaseVMLifecycleTest):
    """Test VM deletion safety and confirmation behavior.
    
    Follows SRP - only tests safety checking logic.
    """

    @pytest.mark.asyncio
    async def test_delete_vm_is_destructive_operation(self):
        """Test that delete VM performs destructive removal of VM."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should call destructive delete endpoint
        mock_proxmox.nodes.return_value.qemu.return_value.delete.assert_called_once()
        
        # Verify success message indicates permanent deletion
        response_data = json.loads(result[0].text)
        assert "deleted successfully" in response_data["message"]

    @pytest.mark.asyncio
    async def test_delete_vm_handles_purge_operation(self):
        """Test that delete VM handles purge operation for complete removal."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed and indicate complete removal
        self.assert_delete_operation_success(result, params["vmid"])
        
        # Verify delete endpoint was called properly
        mock_proxmox.nodes.return_value.qemu.return_value.delete.assert_called_once()


class TestDeleteVMEdgeCases(BaseVMLifecycleTest):
    """Test VM deletion edge cases and boundary conditions.
    
    Follows SRP - only tests edge cases.
    """

    @pytest.mark.asyncio
    async def test_delete_vm_with_special_characters_in_node_name_succeeds(self):
        """Test deleting VM with special characters in node name succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        special_node = "node-test_123.domain"
        
        # Act
        result = await vm_tools.delete_vm(
            node=special_node,
            vmid="100"
        )
        
        # Assert
        self.assert_delete_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "delete", special_node, "100")

    @pytest.mark.asyncio
    async def test_delete_vm_handles_empty_task_id_response(self):
        """Test deleting VM handles empty task ID response gracefully."""
        # Arrange
        mock_proxmox = (self.mock_builder
                       .with_vm_status("stopped")
                       .with_delete_operation(None)  # No task ID returned
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.delete_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["upid"] is None  # Should handle None gracefully

    @pytest.mark.asyncio
    async def test_delete_vm_with_high_vmid_number_succeeds(self):
        """Test deleting VM with high VMID number succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        high_vmid = "999999"
        
        # Act
        result = await vm_tools.delete_vm(
            node="node1",
            vmid=high_vmid
        )
        
        # Assert
        self.assert_delete_operation_success(result, high_vmid)

    @pytest.mark.asyncio
    async def test_delete_vm_with_minimal_vmid_succeeds(self):
        """Test deleting VM with minimal VMID succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_delete_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        minimal_vmid = "100"  # Standard minimum VMID
        
        # Act
        result = await vm_tools.delete_vm(
            node="node1",
            vmid=minimal_vmid
        )
        
        # Assert
        self.assert_delete_operation_success(result, minimal_vmid)