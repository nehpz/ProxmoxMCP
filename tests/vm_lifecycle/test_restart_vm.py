"""
Atomic tests for VM restart operation.

Tests the restart_vm method following SOLID principles:
- Single Responsibility: Each test validates one specific behavior
- Open/Closed: Uses extensible base classes
- Liskov Substitution: Mocks maintain API contracts
- Interface Segregation: Minimal mocks per test
- Dependency Inversion: Tests depend on abstractions
"""
import pytest
import json
from unittest.mock import Mock

from tests.fixtures.base_test_classes import BaseVMStateChangeTest


class TestRestartVMSuccess(BaseVMStateChangeTest):
    """Test successful VM restart scenarios.
    
    Follows SRP - only tests successful restart operations.
    """

    @pytest.mark.asyncio
    async def test_restart_vm_with_running_vm_returns_success(self):
        """Test restarting a running VM returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        self.assert_restart_operation_success(result, params["vmid"])
        self.assertion_helper.assert_api_call_made(mock_proxmox, "restart", params["node"], params["vmid"])
        self.assertion_helper.assert_status_check_made(mock_proxmox)

    @pytest.mark.asyncio
    async def test_restart_vm_returns_task_id_in_response(self):
        """Test that restart VM returns task ID for monitoring."""
        # Arrange
        expected_task_id = "UPID:node1:00001234:56789ABC:timestamp:qmreboot:100:user@pve:"
        mock_proxmox = (self.mock_builder
                       .with_vm_status("running")
                       .with_restart_operation(expected_task_id)
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["upid"] == expected_task_id

    @pytest.mark.asyncio
    async def test_restart_vm_with_different_node_succeeds(self):
        """Test restarting VM on different node succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_node = "node4"
        
        # Act
        result = await vm_tools.restart_vm(
            node=custom_node,
            vmid="100"
        )
        
        # Assert
        self.assert_restart_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "restart", custom_node, "100")

    @pytest.mark.asyncio
    async def test_restart_vm_with_different_vmid_succeeds(self):
        """Test restarting VM with different VMID succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_vmid = "888"
        
        # Act
        result = await vm_tools.restart_vm(
            node="node1",
            vmid=custom_vmid
        )
        
        # Assert
        self.assert_restart_operation_success(result, custom_vmid)
        self.assertion_helper.assert_api_call_made(mock_proxmox, "restart", "node1", custom_vmid)

    @pytest.mark.asyncio
    async def test_restart_vm_initiates_graceful_reboot(self):
        """Test that restart VM initiates graceful OS reboot."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should call graceful reboot endpoint
        mock_proxmox.nodes.return_value.qemu.return_value.status.reboot.post.assert_called_once()
        
        # Verify success message indicates graceful reboot
        response_data = json.loads(result[0].text)
        assert "reboot initiated" in response_data["message"]

    @pytest.mark.asyncio
    async def test_restart_vm_with_stopped_vm_starts_instead(self):
        """Test restarting stopped VM performs start operation instead."""
        # Arrange
        mock_proxmox = (self.mock_builder
                       .with_vm_status("stopped")
                       .with_start_operation()
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should call start instead of reboot for stopped VM
        mock_proxmox.nodes.return_value.qemu.return_value.status.start.post.assert_called_once()
        mock_proxmox.nodes.return_value.qemu.return_value.status.reboot.post.assert_not_called()


class TestRestartVMErrors(BaseVMStateChangeTest):
    """Test VM restart error scenarios.
    
    Follows SRP - only tests error conditions.
    """

    @pytest.mark.asyncio
    async def test_restart_vm_with_nonexistent_vm_raises_runtime_error(self):
        """Test restarting non-existent VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_vm_not_found_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM not found"):
            await vm_tools.restart_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_restart_vm_with_locked_vm_raises_runtime_error(self):
        """Test restarting locked VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("restart", "VM is locked")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM is locked"):
            await vm_tools.restart_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_restart_vm_with_guest_agent_unavailable_raises_runtime_error(self):
        """Test restarting VM with unavailable guest agent raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("restart", "QEMU guest agent is not running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("guest agent is not running"):
            await vm_tools.restart_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_restart_vm_with_api_failure_raises_runtime_error(self):
        """Test restarting VM with API failure raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("restart", "Failed to restart VM")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Failed to restart VM"):
            await vm_tools.restart_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_restart_vm_with_insufficient_resources_raises_runtime_error(self):
        """Test restarting VM with insufficient resources raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("restart", "Insufficient memory to restart VM")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Insufficient memory"):
            await vm_tools.restart_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_restart_vm_with_storage_unavailable_raises_runtime_error(self):
        """Test restarting VM with unavailable storage raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("restart", "Storage 'local-zfs' is not available")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Storage.*not available"):
            await vm_tools.restart_vm(
                node=params["node"],
                vmid=params["vmid"]
            )


class TestRestartVMResponseFormat(BaseVMStateChangeTest):
    """Test VM restart response format validation.
    
    Follows SRP - only tests response format compliance.
    """

    @pytest.mark.asyncio
    async def test_restart_vm_response_contains_required_fields(self):
        """Test that restart VM response contains all required fields."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
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
        assert "reboot initiated" in response_data["message"]
        assert response_data["upid"] is not None

    @pytest.mark.asyncio
    async def test_restart_vm_response_format_matches_api_standard(self):
        """Test that restart VM response format matches API standard."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
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
    async def test_restart_vm_response_is_valid_json(self):
        """Test that restart VM response is valid JSON format."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
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
    async def test_restart_vm_response_message_includes_vmid(self):
        """Test that restart VM response message includes the VM ID."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        test_vmid = "654"
        
        # Act
        result = await vm_tools.restart_vm(
            node="node1",
            vmid=test_vmid
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert test_vmid in response_data["message"]


class TestRestartVMStatusChecks(BaseVMStateChangeTest):
    """Test VM restart status validation behavior.
    
    Follows SRP - only tests status checking logic.
    """

    @pytest.mark.asyncio
    async def test_restart_vm_checks_current_status_before_operation(self):
        """Test that restart VM checks current status before attempting restart."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Status check should be called before restart operation
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        
        # Verify call order: status check before restart
        handle = mock_proxmox.nodes.return_value.qemu.return_value
        assert handle.status.current.get.call_count == 1
        assert handle.status.reboot.post.call_count == 1

    @pytest.mark.asyncio
    async def test_restart_vm_adapts_to_vm_status(self):
        """Test that restart VM adapts operation based on current VM status."""
        # Arrange - Test with running VM (should use reboot)
        mock_proxmox = self.setup_vm_for_restart_test(status="running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed for running VM with reboot
        self.assert_restart_operation_success(result, params["vmid"])

    @pytest.mark.asyncio
    async def test_restart_vm_handles_stopped_vm_correctly(self):
        """Test that restart VM handles stopped VM by starting it."""
        # Arrange - VM is in stopped state
        mock_proxmox = (self.mock_builder
                       .with_vm_status("stopped")
                       .with_start_operation()
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should start the stopped VM instead of reboot
        mock_proxmox.nodes.return_value.qemu.return_value.status.start.post.assert_called_once()
        mock_proxmox.nodes.return_value.qemu.return_value.status.reboot.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_restart_vm_accepts_paused_status(self):
        """Test that restart VM accepts VMs in paused state."""
        # Arrange - VM is in paused state
        mock_proxmox = self.setup_vm_for_restart_test(status="paused")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed for paused VM
        self.assert_restart_operation_success(result, params["vmid"])


class TestRestartVMGracefulBehavior(BaseVMStateChangeTest):
    """Test VM restart graceful operation characteristics.
    
    Follows SRP - only tests graceful restart behavior.
    """

    @pytest.mark.asyncio
    async def test_restart_vm_is_graceful_operation(self):
        """Test that restart VM performs graceful OS reboot (not force restart)."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should call graceful reboot endpoint
        mock_proxmox.nodes.return_value.qemu.return_value.status.reboot.post.assert_called_once()
        
        # Verify success message indicates graceful operation
        response_data = json.loads(result[0].text)
        assert "reboot initiated" in response_data["message"]

    @pytest.mark.asyncio
    async def test_restart_vm_allows_guest_os_cleanup(self):
        """Test that restart VM allows guest OS to perform cleanup before reboot."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test(status="running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed and indicate graceful reboot
        self.assert_restart_operation_success(result, params["vmid"])
        
        # Verify graceful reboot endpoint was called
        mock_proxmox.nodes.return_value.qemu.return_value.status.reboot.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_restart_vm_respects_guest_agent_communication(self):
        """Test that restart VM uses guest agent for communication."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed with graceful reboot
        self.assert_restart_operation_success(result, params["vmid"])


class TestRestartVMEdgeCases(BaseVMStateChangeTest):
    """Test VM restart edge cases and boundary conditions.
    
    Follows SRP - only tests edge cases.
    """

    @pytest.mark.asyncio
    async def test_restart_vm_with_special_characters_in_node_name_succeeds(self):
        """Test restarting VM with special characters in node name succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        special_node = "node-test_123.domain"
        
        # Act
        result = await vm_tools.restart_vm(
            node=special_node,
            vmid="100"
        )
        
        # Assert
        self.assert_restart_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "restart", special_node, "100")

    @pytest.mark.asyncio
    async def test_restart_vm_handles_empty_task_id_response(self):
        """Test restarting VM handles empty task ID response gracefully."""
        # Arrange
        mock_proxmox = (self.mock_builder
                       .with_vm_status("running")
                       .with_restart_operation(None)  # No task ID returned
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["upid"] is None  # Should handle None gracefully

    @pytest.mark.asyncio
    async def test_restart_vm_with_high_vmid_number_succeeds(self):
        """Test restarting VM with high VMID number succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        high_vmid = "999999"
        
        # Act
        result = await vm_tools.restart_vm(
            node="node1",
            vmid=high_vmid
        )
        
        # Assert
        self.assert_restart_operation_success(result, high_vmid)

    @pytest.mark.asyncio
    async def test_restart_vm_handles_state_transitions_correctly(self):
        """Test restarting VM handles different state transitions correctly."""
        # Arrange - VM in running state
        mock_proxmox = self.setup_vm_for_restart_test(status="running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed and handle state transition properly
        self.assert_restart_operation_success(result, params["vmid"])

    @pytest.mark.asyncio
    async def test_restart_vm_with_concurrent_operations_succeeds(self):
        """Test restarting VM handles concurrent operations gracefully."""
        # Arrange
        mock_proxmox = self.setup_vm_for_restart_test(status="running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.restart_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed even with potential concurrent operations
        self.assert_restart_operation_success(result, params["vmid"])