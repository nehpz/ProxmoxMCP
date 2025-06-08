"""
Shared pytest fixtures for ProxmoxMCP tests.

Provides common fixtures following SOLID principles that can be used
across different test modules.
"""
import pytest
from unittest.mock import Mock

from tests.fixtures.mock_helpers import ProxmoxAPIMockBuilder, VMToolsMockHelper
from tests.fixtures.vm_data_factory import VMTestDataFactory


@pytest.fixture
def vm_data_factory():
    """Provide VM test data factory instance.
    
    Returns:
        VMTestDataFactory instance for creating test data
    """
    return VMTestDataFactory()


@pytest.fixture
def mock_builder():
    """Provide ProxmoxAPI mock builder instance.
    
    Returns:
        ProxmoxAPIMockBuilder for creating focused mocks
    """
    return ProxmoxAPIMockBuilder()


@pytest.fixture
def default_vm_config(vm_data_factory):
    """Provide default VM configuration for tests.
    
    Args:
        vm_data_factory: VM data factory fixture
        
    Returns:
        Dict with default VM configuration
    """
    return vm_data_factory.create_vm_config()


@pytest.fixture
def mock_proxmox_basic():
    """Provide basic ProxmoxAPI mock with minimal configuration.
    
    Returns:
        Mock ProxmoxAPI instance with basic structure
    """
    return ProxmoxAPIMockBuilder().build()


@pytest.fixture
def vm_tools_basic(mock_proxmox_basic):
    """Provide VMTools instance with basic mock.
    
    Args:
        mock_proxmox_basic: Basic ProxmoxAPI mock
        
    Returns:
        VMTools instance with mock dependency
    """
    return VMToolsMockHelper.create_vm_tools_with_mock(mock_proxmox_basic)


@pytest.fixture
def test_vm_params():
    """Provide standard test VM parameters.
    
    Returns:
        Dict with standard node and vmid for testing
    """
    return {
        "node": "node1",
        "vmid": "100"
    }


@pytest.fixture
def test_vm_creation_params():
    """Provide standard test VM creation parameters.
    
    Returns:
        Dict with standard VM creation parameters
    """
    return {
        "node": "node1",
        "vmid": "100", 
        "name": "test-vm",
        "memory": 512,
        "cores": 1
    }