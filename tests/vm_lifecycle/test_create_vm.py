"""
Atomic tests for VM creation operation.

Tests the create_vm method following SOLID principles:
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


class TestCreateVMSuccess(BaseVMLifecycleTest):
    """Test successful VM creation scenarios.
    
    Follows SRP - only tests successful creation paths.
    """

    @pytest.mark.asyncio
    async def test_create_vm_with_default_parameters_returns_success(self):
        """Test creating VM with default memory and cores returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"], 
            name="test-vm"
        )
        
        # Assert
        self.assert_create_operation_success(result, params["vmid"], "test-vm")
        self.assertion_helper.assert_api_call_made(mock_proxmox, "create", params["node"], params["vmid"])

    @pytest.mark.asyncio
    async def test_create_vm_with_custom_memory_returns_success(self):
        """Test creating VM with custom memory allocation returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        custom_memory = 1024
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="test-vm",
            memory=custom_memory
        )
        
        # Assert
        self.assert_create_operation_success(result, params["vmid"], "test-vm")
        
        # Verify custom memory was passed to API
        mock_proxmox.nodes.return_value.qemu.post.assert_called_once()
        call_args = mock_proxmox.nodes.return_value.qemu.post.call_args
        assert call_args.kwargs["memory"] == custom_memory

    @pytest.mark.asyncio
    async def test_create_vm_with_custom_cores_returns_success(self):
        """Test creating VM with custom CPU cores returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        custom_cores = 4
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="test-vm",
            cores=custom_cores
        )
        
        # Assert
        self.assert_create_operation_success(result, params["vmid"], "test-vm")
        
        # Verify custom cores was passed to API
        mock_proxmox.nodes.return_value.qemu.post.assert_called_once()
        call_args = mock_proxmox.nodes.return_value.qemu.post.call_args
        assert call_args.kwargs["cores"] == custom_cores

    @pytest.mark.asyncio
    async def test_create_vm_with_all_custom_parameters_returns_success(self):
        """Test creating VM with all custom parameters returns success response."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        custom_params = {
            "name": "custom-test-vm",
            "memory": 2048,
            "cores": 8
        }
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            **custom_params
        )
        
        # Assert
        self.assert_create_operation_success(result, params["vmid"], custom_params["name"])
        
        # Verify all custom parameters were passed
        mock_proxmox.nodes.return_value.qemu.post.assert_called_once()
        call_args = mock_proxmox.nodes.return_value.qemu.post.call_args
        assert call_args.kwargs["name"] == custom_params["name"]
        assert call_args.kwargs["memory"] == custom_params["memory"]
        assert call_args.kwargs["cores"] == custom_params["cores"]

    @pytest.mark.asyncio
    async def test_create_vm_configures_correct_vm_properties(self):
        """Test that VM creation configures correct default VM properties."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="test-vm"
        )
        
        # Assert - Verify VM configuration properties
        mock_proxmox.nodes.return_value.qemu.post.assert_called_once()
        call_args = mock_proxmox.nodes.return_value.qemu.post.call_args
        
        # Check required VM properties
        assert call_args.kwargs["vmid"] == params["vmid"]
        assert call_args.kwargs["name"] == "test-vm"
        assert call_args.kwargs["ostype"] == "l26"  # Linux 2.6+
        assert call_args.kwargs["sockets"] == 1
        assert call_args.kwargs["scsi0"] == "local-zfs:1"  # ZFS storage
        assert call_args.kwargs["boot"] == "order=scsi0"
        assert call_args.kwargs["net0"] == "virtio,bridge=vmbr0"


class TestCreateVMErrors(BaseVMLifecycleTest):
    """Test VM creation error scenarios.
    
    Follows SRP - only tests error conditions.
    """

    @pytest.mark.asyncio
    async def test_create_vm_with_existing_vmid_raises_value_error(self):
        """Test creating VM with existing VMID raises ValueError."""
        # Arrange
        mock_proxmox = Mock()
        # Configure mock to return existing VM (no exception on status check)
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.return_value = {
            "status": "stopped"
        }
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_value_error_raised("already exists"):
            await vm_tools.create_vm(
                node=params["node"],
                vmid=params["vmid"],
                name="test-vm"
            )
        
        # Verify status check was made but create was not called
        self.assertion_helper.assert_status_check_made(mock_proxmox)
        mock_proxmox.nodes.return_value.qemu.post.assert_not_called()

    @pytest.mark.asyncio 
    async def test_create_vm_with_api_failure_raises_runtime_error(self):
        """Test VM creation with API failure raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("create", "Storage not available")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Storage not available"):
            await vm_tools.create_vm(
                node=params["node"],
                vmid=params["vmid"],
                name="test-vm"
            )

    @pytest.mark.asyncio
    async def test_create_vm_with_storage_error_raises_runtime_error(self):
        """Test VM creation with storage error raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("create", "storage 'local' does not support vm images")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("storage.*does not support"):
            await vm_tools.create_vm(
                node=params["node"],
                vmid=params["vmid"],
                name="test-vm"
            )

    @pytest.mark.asyncio
    async def test_create_vm_with_insufficient_resources_raises_runtime_error(self):
        """Test VM creation with insufficient resources raises RuntimeError."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("create", "Insufficient memory on node")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with self.assert_runtime_error_raised("Insufficient memory"):
            await vm_tools.create_vm(
                node=params["node"],
                vmid=params["vmid"],
                name="test-vm",
                memory=8192  # Large memory allocation
            )


class TestCreateVMResponseFormat(BaseVMLifecycleTest):
    """Test VM creation response format validation.
    
    Follows SRP - only tests response format compliance.
    """

    @pytest.mark.asyncio
    async def test_create_vm_response_contains_required_fields(self):
        """Test that create VM response contains all required fields."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="test-vm"
        )
        
        # Assert
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        # Verify required response fields
        assert "success" in response_data
        assert "message" in response_data
        assert "vmid" in response_data
        
        # Verify field values
        assert response_data["success"] is True
        assert response_data["vmid"] == params["vmid"]
        assert "created successfully" in response_data["message"]

    @pytest.mark.asyncio
    async def test_create_vm_response_format_matches_api_standard(self):
        """Test that create VM response format matches API standard."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="test-vm"
        )
        
        # Assert
        response_data = json.loads(result[0].text)
        
        # Verify response structure matches expected format
        expected_structure = {
            "success": bool,
            "message": str,
            "vmid": str
        }
        
        for field, expected_type in expected_structure.items():
            assert field in response_data, f"Missing required field: {field}"
            assert isinstance(response_data[field], expected_type), f"Field {field} has wrong type"

    @pytest.mark.asyncio
    async def test_create_vm_response_is_valid_json(self):
        """Test that create VM response is valid JSON format."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="test-vm"
        )
        
        # Assert
        assert len(result) == 1
        
        # Should not raise exception when parsing JSON
        try:
            response_data = json.loads(result[0].text)
            assert isinstance(response_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")


class TestCreateVMEdgeCases(BaseVMLifecycleTest):
    """Test VM creation edge cases and boundary conditions.
    
    Follows SRP - only tests edge cases.
    """

    @pytest.mark.asyncio
    async def test_create_vm_with_minimum_memory_succeeds(self):
        """Test creating VM with minimum memory allocation succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        min_memory = 64  # 64MB minimum
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="test-vm",
            memory=min_memory
        )
        
        # Assert
        self.assert_create_operation_success(result, params["vmid"], "test-vm")

    @pytest.mark.asyncio
    async def test_create_vm_with_maximum_practical_memory_succeeds(self):
        """Test creating VM with large memory allocation succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        large_memory = 32768  # 32GB
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name="test-vm",
            memory=large_memory
        )
        
        # Assert
        self.assert_create_operation_success(result, params["vmid"], "test-vm")

    @pytest.mark.asyncio
    async def test_create_vm_with_special_characters_in_name_succeeds(self):
        """Test creating VM with special characters in name succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        special_name = "test-vm_123.prod"
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=params["vmid"],
            name=special_name
        )
        
        # Assert
        self.assert_create_operation_success(result, params["vmid"], special_name)

    @pytest.mark.asyncio
    async def test_create_vm_with_high_vmid_succeeds(self):
        """Test creating VM with high VMID number succeeds."""
        # Arrange
        mock_proxmox = self.setup_vm_for_create_test()
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        high_vmid = "999999"
        
        # Act
        result = await vm_tools.create_vm(
            node=params["node"],
            vmid=high_vmid,
            name="test-vm"
        )
        
        # Assert
        self.assert_create_operation_success(result, high_vmid, "test-vm")
        
        # Verify high VMID was passed correctly
        mock_proxmox.nodes.return_value.qemu.post.assert_called_once()
        call_args = mock_proxmox.nodes.return_value.qemu.post.call_args
        assert call_args.kwargs["vmid"] == high_vmid