"""
Comprehensive error handling and edge case tests for VM operations.

Tests error scenarios and edge cases following SOLID principles:
- Single Responsibility: Each test validates one specific error condition
- Open/Closed: Uses extensible base classes
- Interface Segregation: Focused error scenarios
- Dependency Inversion: Tests depend on abstractions

These tests ensure robust error handling across all VM operations.
"""
import pytest
import json
from unittest.mock import Mock, patch
from proxmoxer import ResourceException

from tests.fixtures.base_test_classes import BaseVMErrorTest


class TestVMOperationNetworkErrors(BaseVMErrorTest):
    """Test VM operations network and connectivity error handling.
    
    Follows SRP - tests network-related error scenarios.
    """

    @pytest.mark.asyncio
    async def test_vm_operations_handle_connection_timeout(self):
        """Test that VM operations handle connection timeout gracefully."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
            ResourceException("Connection timeout")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert - All operations should handle timeout
        operations = [
            ("start_vm", vm_tools.start_vm),
            ("stop_vm", vm_tools.stop_vm),
            ("restart_vm", vm_tools.restart_vm),
            ("shutdown_vm", vm_tools.shutdown_vm),
            ("delete_vm", vm_tools.delete_vm)
        ]
        
        for op_name, operation in operations:
            with pytest.raises(RuntimeError, match="Connection timeout"):
                await operation(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_handle_network_unreachable(self):
        """Test that VM operations handle network unreachable errors."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
            ResourceException("Network is unreachable")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Network is unreachable"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_handle_authentication_failure(self):
        """Test that VM operations handle authentication failures."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
            ResourceException("Authentication failed")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Authentication failed"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_handle_permission_denied(self):
        """Test that VM operations handle permission denied errors."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
            ResourceException("Permission denied")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Permission denied"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])


class TestVMOperationResourceErrors(BaseVMErrorTest):
    """Test VM operations resource-related error handling.
    
    Follows SRP - tests resource constraint error scenarios.
    """

    @pytest.mark.asyncio
    async def test_vm_operations_handle_insufficient_memory(self):
        """Test that VM operations handle insufficient memory errors."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("start", "Insufficient memory on node")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Insufficient memory"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_handle_disk_space_exhausted(self):
        """Test that VM operations handle disk space exhausted errors."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("create", "No space left on device")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="No space left on device"):
            await vm_tools.create_vm(
                node=params["node"],
                vmid=params["vmid"],
                name="test-vm"
            )

    @pytest.mark.asyncio
    async def test_vm_operations_handle_cpu_limit_exceeded(self):
        """Test that VM operations handle CPU limit exceeded errors."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("start", "CPU limit exceeded")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="CPU limit exceeded"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_handle_storage_unavailable(self):
        """Test that VM operations handle storage unavailable errors."""
        # Arrange
        storage_errors = [
            "Storage 'local-zfs' is not available",
            "Storage pool 'rbd' is offline",
            "Cannot access storage 'nfs-backup'"
        ]
        
        vm_tools = self.create_vm_tools_with_mock(Mock())
        params = self.get_default_test_params()
        
        for error_msg in storage_errors:
            mock_proxmox = self.setup_operation_failure_error("start", error_msg)
            vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
            
            # Act & Assert
            with pytest.raises(RuntimeError, match="Storage.*not available|offline|Cannot access"):
                await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])


class TestVMOperationConcurrencyErrors(BaseVMErrorTest):
    """Test VM operations concurrency and locking error handling.
    
    Follows SRP - tests concurrency-related error scenarios.
    """

    @pytest.mark.asyncio
    async def test_vm_operations_handle_vm_locked_errors(self):
        """Test that VM operations handle VM locked errors appropriately."""
        # Arrange
        vm_tools = self.create_vm_tools_with_mock(Mock())
        params = self.get_default_test_params()
        
        operations_and_errors = [
            ("start", "VM is locked"),
            ("stop", "VM configuration is locked"),
            ("restart", "VM is locked by another process"),
            ("shutdown", "VM locked for migration"),
            ("delete", "VM is locked for backup")
        ]
        
        for operation, error_msg in operations_and_errors:
            mock_proxmox = self.setup_operation_failure_error(operation, error_msg)
            vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
            
            # Get operation method
            operation_method = getattr(vm_tools, f"{operation}_vm")
            
            # Act & Assert
            with pytest.raises(RuntimeError, match="locked"):
                await operation_method(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_handle_concurrent_modification(self):
        """Test that VM operations handle concurrent modification errors."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("start", "VM configuration changed during operation")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="configuration changed"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_handle_migration_in_progress(self):
        """Test that VM operations handle migration in progress errors."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("stop", "VM migration in progress")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="migration in progress"):
            await vm_tools.stop_vm(node=params["node"], vmid=params["vmid"])


class TestVMOperationInputValidation(BaseVMErrorTest):
    """Test VM operations input validation and sanitization.
    
    Follows SRP - tests input validation error scenarios.
    """

    @pytest.mark.asyncio
    async def test_vm_operations_handle_invalid_node_names(self):
        """Test that VM operations handle invalid node names appropriately."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
            ResourceException("Node 'invalid-node' does not exist")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        invalid_nodes = ["", "invalid-node", "node with spaces", "node@special"]
        
        for invalid_node in invalid_nodes:
            # Act & Assert
            with pytest.raises(RuntimeError, match="does not exist|invalid"):
                await vm_tools.start_vm(node=invalid_node, vmid="100")

    @pytest.mark.asyncio
    async def test_vm_operations_handle_invalid_vmid_formats(self):
        """Test that VM operations handle invalid VMID formats."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
            ResourceException("Invalid VM ID format")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        invalid_vmids = ["", "abc", "vm100", "100.5", "-100"]
        
        for invalid_vmid in invalid_vmids:
            # Act & Assert
            with pytest.raises(RuntimeError, match="Invalid.*format"):
                await vm_tools.start_vm(node="node1", vmid=invalid_vmid)

    @pytest.mark.asyncio
    async def test_create_vm_handles_invalid_memory_values(self):
        """Test that create VM handles invalid memory values."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
            ResourceException("VM not found")  # VM doesn't exist, good for create
        mock_proxmox.nodes.return_value.qemu.post.side_effect = \
            ResourceException("Invalid memory value")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        invalid_memory_values = [0, -512, "abc", 99999999]
        
        for invalid_memory in invalid_memory_values:
            # Act & Assert
            with pytest.raises(RuntimeError, match="Invalid memory"):
                await vm_tools.create_vm(
                    node=params["node"],
                    vmid=params["vmid"],
                    name="test-vm",
                    memory=invalid_memory
                )

    @pytest.mark.asyncio
    async def test_create_vm_handles_invalid_cpu_cores(self):
        """Test that create VM handles invalid CPU core values."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
            ResourceException("VM not found")  # VM doesn't exist, good for create
        mock_proxmox.nodes.return_value.qemu.post.side_effect = \
            ResourceException("Invalid CPU cores value")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        invalid_cores_values = [0, -4, "abc", 999]
        
        for invalid_cores in invalid_cores_values:
            # Act & Assert
            with pytest.raises(RuntimeError, match="Invalid.*cores"):
                await vm_tools.create_vm(
                    node=params["node"],
                    vmid=params["vmid"],
                    name="test-vm",
                    cores=invalid_cores
                )


class TestVMOperationStateConsistency(BaseVMErrorTest):
    """Test VM operations state consistency and validation.
    
    Follows SRP - tests state consistency error scenarios.
    """

    @pytest.mark.asyncio
    async def test_vm_operations_detect_state_corruption(self):
        """Test that VM operations detect and handle state corruption."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
            ResourceException("VM state is corrupted")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="corrupted"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_handle_inconsistent_status_reporting(self):
        """Test that VM operations handle inconsistent status reporting."""
        # Arrange - Mock returns different status on subsequent calls
        mock_proxmox = Mock()
        status_responses = [
            {"status": "running"},
            {"status": "stopped"},  # Inconsistent status
        ]
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = status_responses
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert - Should handle inconsistent status gracefully
        with pytest.raises(ValueError, match="already running"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_handle_unknown_vm_states(self):
        """Test that VM operations handle unknown VM states."""
        # Arrange
        mock_proxmox = Mock()
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.return_value = \
            {"status": "unknown"}
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert - Should handle unknown states appropriately
        with pytest.raises(RuntimeError, match="Unknown.*state|Unexpected.*status"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])


class TestVMOperationRecoveryMechanisms(BaseVMErrorTest):
    """Test VM operations recovery and retry mechanisms.
    
    Follows SRP - tests recovery mechanism scenarios.
    """

    @pytest.mark.asyncio
    async def test_vm_operations_provide_clear_error_messages(self):
        """Test that VM operations provide clear, actionable error messages."""
        # Arrange
        error_scenarios = [
            ("VM not found", "VM.*not found"),
            ("Insufficient memory", "Insufficient memory|Not enough memory"),
            ("Storage unavailable", "Storage.*unavailable|Storage.*not available"),
            ("Permission denied", "Permission denied|Access denied"),
            ("VM is locked", "VM.*locked|locked.*VM")
        ]
        
        vm_tools = self.create_vm_tools_with_mock(Mock())
        params = self.get_default_test_params()
        
        for error_msg, expected_pattern in error_scenarios:
            mock_proxmox = self.setup_operation_failure_error("start", error_msg)
            vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
            
            # Act & Assert
            with pytest.raises(RuntimeError, match=expected_pattern):
                await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])

    @pytest.mark.asyncio
    async def test_vm_operations_maintain_error_context(self):
        """Test that VM operations maintain context in error messages."""
        # Arrange
        mock_proxmox = self.setup_operation_failure_error("start", "Custom error message")
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert - Error should include operation context
        with pytest.raises(RuntimeError) as exc_info:
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])
        
        error_str = str(exc_info.value)
        assert "Custom error message" in error_str

    @pytest.mark.asyncio
    async def test_vm_operations_handle_partial_failures_gracefully(self):
        """Test that VM operations handle partial failures gracefully."""
        # Arrange - Mock that fails on second operation call
        mock_proxmox = Mock()
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"status": "stopped"}  # First call succeeds
            else:
                raise ResourceException("Operation failed partially")
        
        mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = side_effect
        mock_proxmox.nodes.return_value.qemu.return_value.status.start.post.side_effect = \
            ResourceException("Start operation failed")
        
        vm_tools = self.create_vm_tools_with_mock(mock_proxmox)
        params = self.get_default_test_params()
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Start operation failed"):
            await vm_tools.start_vm(node=params["node"], vmid=params["vmid"])