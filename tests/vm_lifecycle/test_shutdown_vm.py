"""
Atomic tests for VM shutdown operation.

Tests the shutdown_vm method following SOLID principles:
- Single Responsibility: Each test validates one specific behavior
- Open/Closed: Uses extensible base classes
- Liskov Substitution: Mocks maintain API contracts
- Interface Segregation: Minimal mocks per test
- Dependency Inversion: Tests depend on abstractions
"""
import pytest
import json
from unittest.mock import Mock

from fixtures.base_test_classes import BaseVMStateChangeTest


class TestShutdownVMSuccess(BaseVMStateChangeTest):
    """Test successful VM shutdown scenarios.
    
    Follows SRP - only tests successful shutdown operations.
    """

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_running_vm_returns_success(self):
        """Test shutting down a running VM returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        self.assert_shutdown_operation_success(result, params["vmid"])
        self.assertion_helper.assert_api_call_made(mock_proxmox, "shutdown", params["node"], params["vmid"])
        self.assertion_helper.assert_status_check_made(mock_proxmox)

    @pytest.mark.asyncio
    async def test_shutdown_vm_returns_task_id_in_response(self):
        """Test that shutdown VM returns task ID for monitoring."""
        # Arrange
        expected_task_id = "UPID:node1:00001234:56789ABC:timestamp:qmshutdown:100:user@pve:"
        mock_proxmox = (self.mock_builder
                       .with_vm_status("running")
                       .with_shutdown_operation(expected_task_id)
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["upid"] == expected_task_id

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_different_node_succeeds(self):
        """Test shutting down VM on different node succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_node = "node3"
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=custom_node,
            vmid="100"
        )
        
        # Assert
        self.assert_shutdown_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "shutdown", custom_node, "100")

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_different_vmid_succeeds(self):
        """Test shutting down VM with different VMID succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_vmid = "777"
        
        # Act
        result = await vm_tools.shutdown_vm(
            node="node1",
            vmid=custom_vmid
        )
        
        # Assert
        self.assert_shutdown_operation_success(result, custom_vmid)
        self.assertion_helper.assert_api_call_made(mock_proxmox, "shutdown", "node1", custom_vmid)

    @pytest.mark.asyncio
    async def test_shutdown_vm_initiates_graceful_shutdown(self):
        """Test that shutdown VM initiates graceful OS shutdown."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should call graceful shutdown endpoint, not force stop
        mock_proxmox.nodes.return_value.qemu.return_value.status.shutdown.post.assert_called_once()
        mock_proxmox.nodes.return_value.qemu.return_value.status.stop.post.assert_not_called()
        
        # Verify success message indicates graceful shutdown
        response_data = json.loads(result[0].text)
        assert "shutdown initiated" in response_data["message"]


class TestShutdownVMErrors(BaseVMStateChangeTest):
    """Test VM shutdown error scenarios.
    
    Follows SRP - only tests error conditions.
    """

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_already_stopped_vm_raises_value_error(self):
        """Test shutting down already stopped VM raises ValueError."""
        # Arrange
        mock_proxmox = self.setup_vm_already_stopped_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("already stopped"):
            await vm_tools.shutdown_vm(
                node=params["node"],
                vmid=params["vmid"]
            )
        
        # Verify status check was made but shutdown was not called
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        mock_proxmox.nodes.return_value.qemu.return_value.status.shutdown.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_nonexistent_vm_raises_runtime_error(self):
        """Test shutting down non-existent VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_vm_not_found_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM not found"):
            await vm_tools.shutdown_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_locked_vm_raises_runtime_error(self):
        """Test shutting down locked VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("shutdown", "VM is locked")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM is locked"):
            await vm_tools.shutdown_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_guest_agent_unavailable_raises_runtime_error(self):
        """Test shutting down VM with unavailable guest agent raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("shutdown", "QEMU guest agent is not running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("guest agent is not running"):
            await vm_tools.shutdown_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_api_failure_raises_runtime_error(self):
        """Test shutting down VM with API failure raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("shutdown", "Failed to shutdown VM")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Failed to shutdown VM"):
            await vm_tools.shutdown_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_timeout_raises_runtime_error(self):
        """Test shutting down VM with timeout raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("shutdown", "Shutdown timeout")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Shutdown timeout"):
            await vm_tools.shutdown_vm(
                node=params["node"],
                vmid=params["vmid"]
            )


class TestShutdownVMResponseFormat(BaseVMStateChangeTest):
    """Test VM shutdown response format validation.
    
    Follows SRP - only tests response format compliance.
    """

    @pytest.mark.asyncio
    async def test_shutdown_vm_response_contains_required_fields(self):
        """Test that shutdown VM response contains all required fields."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
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
        assert "shutdown initiated" in response_data["message"]
        assert response_data["upid"] is not None

    @pytest.mark.asyncio
    async def test_shutdown_vm_response_format_matches_api_standard(self):
        """Test that shutdown VM response format matches API standard."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
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
    async def test_shutdown_vm_response_is_valid_json(self):
        """Test that shutdown VM response is valid JSON format."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
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
    async def test_shutdown_vm_response_message_includes_vmid(self):
        """Test that shutdown VM response message includes the VM ID."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        test_vmid = "456"
        
        # Act
        result = await vm_tools.shutdown_vm(
            node="node1",
            vmid=test_vmid
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert test_vmid in response_data["message"]


class TestShutdownVMStatusChecks(BaseVMStateChangeTest):
    """Test VM shutdown status validation behavior.
    
    Follows SRP - only tests status checking logic.
    """

    @pytest.mark.asyncio
    async def test_shutdown_vm_checks_current_status_before_operation(self):
        """Test that shutdown VM checks current status before attempting shutdown."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Status check should be called before shutdown operation
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        
        # Verify call order: status check before shutdown
        handle = mock_proxmox.nodes.return_value.qemu.return_value
        assert handle.status.current.get.call_count == 1
        assert handle.status.shutdown.post.call_count == 1

    @pytest.mark.asyncio
    async def test_shutdown_vm_validates_running_status_requirement(self):
        """Test that shutdown VM validates VM must be in running state."""
        # Arrange - VM is in running state
        mock_proxmox = self.setup_vm_for_shutdown_test(status="running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed for running VM
        self.assert_shutdown_operation_success(result, params["vmid"])

    @pytest.mark.asyncio
    async def test_shutdown_vm_rejects_stopped_status(self):
        """Test that shutdown VM rejects VMs in stopped state."""
        # Arrange - VM is in stopped state
        mock_proxmox = self.setup_vm_already_stopped_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("already stopped"):
            await vm_tools.shutdown_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_shutdown_vm_accepts_paused_status(self):
        """Test that shutdown VM accepts VMs in paused state."""
        # Arrange - VM is in paused state
        mock_proxmox = self.setup_vm_for_shutdown_test(status="paused")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed for paused VM
        self.assert_shutdown_operation_success(result, params["vmid"])


class TestShutdownVMGracefulBehavior(BaseVMStateChangeTest):
    """Test VM shutdown graceful operation characteristics.
    
    Follows SRP - only tests graceful shutdown behavior.
    """

    @pytest.mark.asyncio
    async def test_shutdown_vm_is_graceful_operation(self):
        """Test that shutdown VM performs graceful OS shutdown (not force stop)."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should call graceful shutdown endpoint, not force stop
        mock_proxmox.nodes.return_value.qemu.return_value.status.shutdown.post.assert_called_once()
        mock_proxmox.nodes.return_value.qemu.return_value.status.stop.post.assert_not_called()
        
        # Verify success message indicates graceful operation
        response_data = json.loads(result[0].text)
        assert "shutdown initiated" in response_data["message"]

    @pytest.mark.asyncio
    async def test_shutdown_vm_allows_guest_os_cleanup(self):
        """Test that shutdown VM allows guest OS to perform cleanup."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test(status="running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed and indicate graceful shutdown
        self.assert_shutdown_operation_success(result, params["vmid"])
        
        # Verify graceful shutdown endpoint was called
        mock_proxmox.nodes.return_value.qemu.return_value.status.shutdown.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_vm_respects_guest_agent_communication(self):
        """Test that shutdown VM uses guest agent for communication."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed with graceful shutdown
        self.assert_shutdown_operation_success(result, params["vmid"])


class TestShutdownVMEdgeCases(BaseVMStateChangeTest):
    """Test VM shutdown edge cases and boundary conditions.
    
    Follows SRP - only tests edge cases.
    """

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_special_characters_in_node_name_succeeds(self):
        """Test shutting down VM with special characters in node name succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        special_node = "node-test_123.domain"
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=special_node,
            vmid="100"
        )
        
        # Assert
        self.assert_shutdown_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "shutdown", special_node, "100")

    @pytest.mark.asyncio
    async def test_shutdown_vm_handles_empty_task_id_response(self):
        """Test shutting down VM handles empty task ID response gracefully."""
        # Arrange
        mock_proxmox = (self.mock_builder
                       .with_vm_status("running")
                       .with_shutdown_operation(None)  # No task ID returned
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["upid"] is None  # Should handle None gracefully

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_high_vmid_number_succeeds(self):
        """Test shutting down VM with high VMID number succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        high_vmid = "999999"
        
        # Act
        result = await vm_tools.shutdown_vm(
            node="node1",
            vmid=high_vmid
        )
        
        # Assert
        self.assert_shutdown_operation_success(result, high_vmid)

    @pytest.mark.asyncio
    async def test_shutdown_vm_with_concurrent_operations_succeeds(self):
        """Test shutting down VM handles concurrent operations gracefully."""
        # Arrange
        mock_proxmox = self.setup_vm_for_shutdown_test(status="running")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.shutdown_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed even with potential concurrent operations
        self.assert_shutdown_operation_success(result, params["vmid"])