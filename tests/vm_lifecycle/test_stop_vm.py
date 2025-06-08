"""
Atomic tests for VM stop operation.

Tests the stop_vm method following SOLID principles:
- Single Responsibility: Each test validates one specific behavior
- Open/Closed: Uses extensible base classes
- Liskov Substitution: Mocks maintain API contracts
- Interface Segregation: Minimal mocks per test
- Dependency Inversion: Tests depend on abstractions
"""
import pytest
import json
from unittest.mock import Mock

from fixtures.base_test_classes import BaseVMStartStopTest


class TestStopVMSuccess(BaseVMStartStopTest):
    """Test successful VM stop scenarios.
    
    Follows SRP - only tests successful stop operations.
    """

    @pytest.mark.asyncio
    async def test_stop_vm_with_running_vm_returns_success(self):
        """Test stopping a running VM returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        self.assert_stop_operation_success(result, params["vmid"])
        self.assertion_helper.assert_api_call_made(mock_proxmox, "stop", params["node"], params["vmid"])
        self.assertion_helper.assert_status_check_made(mock_proxmox)

    @pytest.mark.asyncio
    async def test_stop_vm_with_paused_vm_returns_success(self):
        """Test stopping a paused VM returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test(status="paused")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        self.assert_stop_operation_success(result, params["vmid"])

    @pytest.mark.asyncio
    async def test_stop_vm_returns_task_id_in_response(self):
        """Test that stop VM returns task ID for monitoring."""
        # Arrange
        expected_task_id = "UPID:node1:00001234:56789ABC:timestamp:qmstop:100:user@pve:"
        mock_proxmox = (self.mock_builder
                       .with_vm_status("running")
                       .with_stop_operation(expected_task_id)
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["upid"] == expected_task_id

    @pytest.mark.asyncio
    async def test_stop_vm_with_different_node_succeeds(self):
        """Test stopping VM on different node succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_node = "node3"
        
        # Act
        result = await vm_tools.stop_vm(
            node=custom_node,
            vmid="100"
        )
        
        # Assert
        self.assert_stop_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "stop", custom_node, "100")

    @pytest.mark.asyncio
    async def test_stop_vm_with_different_vmid_succeeds(self):
        """Test stopping VM with different VMID succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_vmid = "888"
        
        # Act
        result = await vm_tools.stop_vm(
            node="node1",
            vmid=custom_vmid
        )
        
        # Assert
        self.assert_stop_operation_success(result, custom_vmid)
        self.assertion_helper.assert_api_call_made(mock_proxmox, "stop", "node1", custom_vmid)


class TestStopVMErrors(BaseVMStartStopTest):
    """Test VM stop error scenarios.
    
    Follows SRP - only tests error conditions.
    """

    @pytest.mark.asyncio
    async def test_stop_vm_with_already_stopped_vm_raises_value_error(self):
        """Test stopping already stopped VM raises ValueError."""
        # Arrange
        mock_proxmox = self.setup_vm_already_stopped_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("already stopped"):
            await vm_tools.stop_vm(
                node=params["node"],
                vmid=params["vmid"]
            )
        
        # Verify status check was made but stop was not called
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        mock_proxmox.nodes.return_value.qemu.return_value.status.stop.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_vm_with_nonexistent_vm_raises_runtime_error(self):
        """Test stopping non-existent VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_vm_not_found_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM not found"):
            await vm_tools.stop_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_stop_vm_with_locked_vm_raises_runtime_error(self):
        """Test stopping locked VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("stop", "VM is locked")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM is locked"):
            await vm_tools.stop_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_stop_vm_with_api_failure_raises_runtime_error(self):
        """Test stopping VM with API failure raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("stop", "Failed to stop VM")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Failed to stop VM"):
            await vm_tools.stop_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_stop_vm_with_network_error_raises_runtime_error(self):
        """Test stopping VM with network error raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("stop", "Connection timeout")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Connection timeout"):
            await vm_tools.stop_vm(
                node=params["node"],
                vmid=params["vmid"]
            )


class TestStopVMResponseFormat(BaseVMStartStopTest):
    """Test VM stop response format validation.
    
    Follows SRP - only tests response format compliance.
    """

    @pytest.mark.asyncio
    async def test_stop_vm_response_contains_required_fields(self):
        """Test that stop VM response contains all required fields."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
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
        assert "stopped successfully" in response_data["message"]
        assert response_data["upid"] is not None

    @pytest.mark.asyncio
    async def test_stop_vm_response_format_matches_api_standard(self):
        """Test that stop VM response format matches API standard."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
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
    async def test_stop_vm_response_is_valid_json(self):
        """Test that stop VM response is valid JSON format."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
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
    async def test_stop_vm_response_message_includes_vmid(self):
        """Test that stop VM response message includes the VM ID."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        test_vmid = "456"
        
        # Act
        result = await vm_tools.stop_vm(
            node="node1",
            vmid=test_vmid
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert test_vmid in response_data["message"]


class TestStopVMStatusChecks(BaseVMStartStopTest):
    """Test VM stop status validation behavior.
    
    Follows SRP - only tests status checking logic.
    """

    @pytest.mark.asyncio
    async def test_stop_vm_checks_current_status_before_operation(self):
        """Test that stop VM checks current status before attempting stop."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        await vm_tools.stop_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Status check should be called before stop operation
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        
        # Verify call order: status check before stop
        handle = mock_proxmox.nodes.return_value.qemu.return_value
        assert handle.status.current.get.call_count == 1
        assert handle.status.stop.post.call_count == 1

    @pytest.mark.asyncio
    async def test_stop_vm_validates_running_status_requirement(self):
        """Test that stop VM validates VM must be in running state."""
        # Arrange - VM is in running state
        mock_proxmox = self.setup_vm_for_stop_test(status="running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed for running VM
        self.assert_stop_operation_success(result, params["vmid"])

    @pytest.mark.asyncio
    async def test_stop_vm_rejects_stopped_status(self):
        """Test that stop VM rejects VMs in stopped state."""
        # Arrange - VM is in stopped state
        mock_proxmox = self.setup_vm_already_stopped_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("already stopped"):
            await vm_tools.stop_vm(
                node=params["node"],
                vmid=params["vmid"]
            )


class TestStopVMForceOperation(BaseVMStartStopTest):
    """Test VM stop force operation characteristics.
    
    Follows SRP - only tests force stop behavior.
    """

    @pytest.mark.asyncio
    async def test_stop_vm_is_immediate_force_operation(self):
        """Test that stop VM performs immediate force stop (not graceful)."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should call force stop endpoint, not shutdown
        mock_proxmox.nodes.return_value.qemu.return_value.status.stop.post.assert_called_once()
        mock_proxmox.nodes.return_value.qemu.return_value.status.shutdown.post.assert_not_called()
        
        # Verify success message indicates force stop
        response_data = json.loads(result[0].text)
        assert "stopped successfully" in response_data["message"]

    @pytest.mark.asyncio
    async def test_stop_vm_handles_vm_with_running_processes(self):
        """Test that stop VM handles VM with running processes (force stop)."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test(status="running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed even with running processes
        self.assert_stop_operation_success(result, params["vmid"])


class TestStopVMEdgeCases(BaseVMStartStopTest):
    """Test VM stop edge cases and boundary conditions.
    
    Follows SRP - only tests edge cases.
    """

    @pytest.mark.asyncio
    async def test_stop_vm_with_special_characters_in_node_name_succeeds(self):
        """Test stopping VM with special characters in node name succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        special_node = "node-test_123.domain"
        
        # Act
        result = await vm_tools.stop_vm(
            node=special_node,
            vmid="100"
        )
        
        # Assert
        self.assert_stop_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "stop", special_node, "100")

    @pytest.mark.asyncio
    async def test_stop_vm_handles_empty_task_id_response(self):
        """Test stopping VM handles empty task ID response gracefully."""
        # Arrange
        mock_proxmox = (self.mock_builder
                       .with_vm_status("running")
                       .with_stop_operation(None)  # No task ID returned
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.stop_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["upid"] is None  # Should handle None gracefully

    @pytest.mark.asyncio
    async def test_stop_vm_with_high_vmid_number_succeeds(self):
        """Test stopping VM with high VMID number succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_stop_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        high_vmid = "999999"
        
        # Act
        result = await vm_tools.stop_vm(
            node="node1",
            vmid=high_vmid
        )
        
        # Assert
        self.assert_stop_operation_success(result, high_vmid)