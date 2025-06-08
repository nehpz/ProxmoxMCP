"""
Atomic tests for VM start operation.

Tests the start_vm method following SOLID principles:
- Single Responsibility: Each test validates one specific behavior
- Open/Closed: Uses extensible base classes
- Liskov Substitution: Mocks maintain API contracts
- Interface Segregation: Minimal mocks per test
- Dependency Inversion: Tests depend on abstractions
"""
import pytest
import json
from unittest.mock import Mock

from tests.fixtures.base_test_classes import BaseVMStartStopTest, BaseVMErrorTest


class TestStartVMSuccess(BaseVMStartStopTest):
    """Test successful VM start scenarios.
    
    Follows SRP - only tests successful start operations.
    """

    @pytest.mark.asyncio
    async def test_start_vm_with_stopped_vm_returns_success(self):
        """Test starting a stopped VM returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.start_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        self.assert_start_operation_success(result, params["vmid"])
        self.assertion_helper.assert_api_call_made(mock_proxmox, "start", params["node"], params["vmid"])
        self.assertion_helper.assert_status_check_made(mock_proxmox)

    @pytest.mark.asyncio
    async def test_start_vm_with_paused_vm_returns_success(self):
        """Test starting a paused VM returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test(status="paused")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.start_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        self.assert_start_operation_success(result, params["vmid"])

    @pytest.mark.asyncio
    async def test_start_vm_returns_task_id_in_response(self):
        """Test that start VM returns task ID for monitoring."""
        # Arrange
        expected_task_id = "UPID:node1:00001234:56789ABC:timestamp:qmstart:100:user@pve:"
        mock_proxmox = (self.mock_builder
                       .with_vm_status("stopped")
                       .with_start_operation(expected_task_id)
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.start_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["upid"] == expected_task_id

    @pytest.mark.asyncio
    async def test_start_vm_with_different_node_succeeds(self):
        """Test starting VM on different node succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_node = "node2"
        
        # Act
        result = await vm_tools.start_vm(
            node=custom_node,
            vmid="100"
        )
        
        # Assert
        self.assert_start_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "start", custom_node, "100")

    @pytest.mark.asyncio
    async def test_start_vm_with_different_vmid_succeeds(self):
        """Test starting VM with different VMID succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        custom_vmid = "999"
        
        # Act
        result = await vm_tools.start_vm(
            node="node1",
            vmid=custom_vmid
        )
        
        # Assert
        self.assert_start_operation_success(result, custom_vmid)
        self.assertion_helper.assert_api_call_made(mock_proxmox, "start", "node1", custom_vmid)


class TestStartVMErrors(BaseVMErrorTest):
    """Test VM start error scenarios.
    
    Follows SRP - only tests error conditions.
    """

    @pytest.mark.asyncio
    async def test_start_vm_with_already_running_vm_raises_value_error(self):
        """Test starting already running VM raises ValueError."""
        # Arrange
        mock_proxmox = self.setup_vm_already_running_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("already running"):
            await vm_tools.start_vm(
                node=params["node"],
                vmid=params["vmid"]
            )
        
        # Verify status check was made but start was not called
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        mock_proxmox.nodes.return_value.qemu.return_value.status.start.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_vm_with_nonexistent_vm_raises_runtime_error(self):
        """Test starting non-existent VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_vm_not_found_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM not found"):
            await vm_tools.start_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_start_vm_with_insufficient_resources_raises_runtime_error(self):
        """Test starting VM with insufficient resources raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("start", "Insufficient memory to start VM")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Insufficient memory"):
            await vm_tools.start_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_start_vm_with_storage_unavailable_raises_runtime_error(self):
        """Test starting VM with unavailable storage raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("start", "Storage 'local-zfs' is not available")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Storage.*not available"):
            await vm_tools.start_vm(
                node=params["node"],
                vmid=params["vmid"]
            )

    @pytest.mark.asyncio
    async def test_start_vm_with_locked_vm_raises_runtime_error(self):
        """Test starting locked VM raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("start", "VM is locked")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("VM is locked"):
            await vm_tools.start_vm(
                node=params["node"],
                vmid=params["vmid"]
            )


class TestStartVMResponseFormat(BaseVMStartStopTest):
    """Test VM start response format validation.
    
    Follows SRP - only tests response format compliance.
    """

    @pytest.mark.asyncio
    async def test_start_vm_response_contains_required_fields(self):
        """Test that start VM response contains all required fields."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.start_vm(
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
        assert "started successfully" in response_data["message"]
        assert response_data["upid"] is not None

    @pytest.mark.asyncio
    async def test_start_vm_response_format_matches_api_standard(self):
        """Test that start VM response format matches API standard."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.start_vm(
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
    async def test_start_vm_response_is_valid_json(self):
        """Test that start VM response is valid JSON format."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.start_vm(
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
    async def test_start_vm_response_message_includes_vmid(self):
        """Test that start VM response message includes the VM ID."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        test_vmid = "123"
        
        # Act
        result = await vm_tools.start_vm(
            node="node1",
            vmid=test_vmid
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert test_vmid in response_data["message"]


class TestStartVMStatusChecks(BaseVMStartStopTest):
    """Test VM start status validation behavior.
    
    Follows SRP - only tests status checking logic.
    """

    @pytest.mark.asyncio
    async def test_start_vm_checks_current_status_before_operation(self):
        """Test that start VM checks current status before attempting start."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        await vm_tools.start_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Status check should be called before start operation
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        
        # Verify call order: status check before start
        handle = mock_proxmox.nodes.return_value.qemu.return_value
        assert handle.status.current.get.call_count == 1
        assert handle.status.start.post.call_count == 1

    @pytest.mark.asyncio
    async def test_start_vm_validates_stopped_status_requirement(self):
        """Test that start VM validates VM must be in stopped state."""
        # Arrange - VM is in stopped state
        mock_proxmox = self.setup_vm_for_start_test(status="stopped")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.start_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert - Should succeed for stopped VM
        self.assert_start_operation_success(result, params["vmid"])

    @pytest.mark.asyncio
    async def test_start_vm_rejects_running_status(self):
        """Test that start VM rejects VMs in running state."""
        # Arrange - VM is in running state
        mock_proxmox = self.setup_vm_already_running_error()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("already running"):
            await vm_tools.start_vm(
                node=params["node"],
                vmid=params["vmid"]
            )


class TestStartVMEdgeCases(BaseVMStartStopTest):
    """Test VM start edge cases and boundary conditions.
    
    Follows SRP - only tests edge cases.
    """

    @pytest.mark.asyncio
    async def test_start_vm_with_long_node_name_succeeds(self):
        """Test starting VM with long node name succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        long_node_name = "very-long-node-name-for-testing-edge-cases"
        
        # Act
        result = await vm_tools.start_vm(
            node=long_node_name,
            vmid="100"
        )
        
        # Assert
        self.assert_start_operation_success(result, "100")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "start", long_node_name, "100")

    @pytest.mark.asyncio
    async def test_start_vm_with_numeric_string_vmid_succeeds(self):
        """Test starting VM with numeric string VMID succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_start_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        numeric_vmid = "999999"
        
        # Act
        result = await vm_tools.start_vm(
            node="node1",
            vmid=numeric_vmid
        )
        
        # Assert
        self.assert_start_operation_success(result, numeric_vmid)

    @pytest.mark.asyncio
    async def test_start_vm_handles_empty_task_id_response(self):
        """Test starting VM handles empty task ID response gracefully."""
        # Arrange
        mock_proxmox = (self.mock_builder
                       .with_vm_status("stopped")
                       .with_start_operation(None)  # No task ID returned
                       .build())
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.start_vm(
            node=params["node"],
            vmid=params["vmid"]
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["upid"] is None  # Should handle None gracefully