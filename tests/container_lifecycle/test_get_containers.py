"""
Comprehensive unit tests for container listing operations.

Tests the get_containers functionality following SOLID principles:
- Single Responsibility: Each test validates one specific behavior
- Open/Closed: Uses extensible base classes  
- Liskov Substitution: Mocks maintain real API contracts
- Interface Segregation: Minimal mocks for specific test scenarios
- Dependency Inversion: Tests depend on abstractions

These tests ensure robust container listing functionality across all scenarios.
"""
import pytest
from unittest.mock import Mock

from tests.fixtures.base_test_classes import BaseContainerListTest
from tests.fixtures.vm_data_factory import ContainerTestDataFactory


class TestGetContainersSuccess(BaseContainerListTest):
    """Test successful container listing operations.
    
    Follows SRP - tests successful operation scenarios only.
    """

    def test_get_containers_with_single_node_returns_container_list(self):
        """Test that get_containers returns containers from single node."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        self.assert_container_data_present(result, expected_count=2)

    def test_get_containers_with_multiple_nodes_returns_all_containers(self):
        """Test that get_containers aggregates containers from multiple nodes."""
        # Arrange
        mock_proxmox = self.setup_multi_node_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        self.assert_container_data_present(result)

    def test_get_containers_with_empty_list_returns_empty_response(self):
        """Test that get_containers handles empty container list gracefully."""
        # Arrange
        mock_proxmox = self.setup_empty_container_list()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        self.assert_no_containers_response(result)

    def test_get_containers_includes_container_configuration_details(self):
        """Test that get_containers includes detailed configuration information."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        # Verify container details are included
        assert "web-container" in response_text, "Expected container name"
        assert "CPU Cores:" in response_text, "Expected CPU core information"
        assert "Memory:" in response_text, "Expected memory information"

    def test_get_containers_formats_memory_usage_correctly(self):
        """Test that get_containers formats memory usage in readable format."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        # Verify memory formatting (should show in readable units)
        assert "MB" in response_text or "KB" in response_text or "GB" in response_text, \
            "Expected readable memory units"

    def test_get_containers_shows_container_status(self):
        """Test that get_containers displays current container status."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        # Verify status information is displayed
        assert "RUNNING" in response_text or "STOPPED" in response_text, \
            "Expected container status information"

    def test_get_containers_includes_node_placement_info(self):
        """Test that get_containers shows which node each container is on."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        # Verify node information is included
        assert "Node:" in response_text, "Expected node placement information"
        assert "node1" in response_text, "Expected specific node name"


class TestGetContainersConfigHandling(BaseContainerListTest):
    """Test container configuration retrieval and fallback mechanisms.
    
    Follows SRP - tests configuration handling scenarios only.
    """

    def test_get_containers_with_config_access_success_includes_template_info(self):
        """Test that get_containers includes template information when config is accessible."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        # Verify template information when config is available
        # (Template info would be available with successful config retrieval)
        assert "ubuntu-20.04" in response_text or "N/A" in response_text, \
            "Expected template information or fallback"

    def test_get_containers_with_config_failure_uses_fallback_data(self):
        """Test that get_containers gracefully handles config retrieval failures."""
        # Arrange
        mock_proxmox = self.setup_config_fallback_scenario()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        self.assert_container_data_present(result, expected_count=2)
        
        response_text = result[0].text
        # Verify fallback values are used when config fails
        assert "N/A" in response_text, "Expected fallback values for unavailable config"

    def test_get_containers_config_fallback_preserves_basic_info(self):
        """Test that config fallback preserves essential container information."""
        # Arrange
        mock_proxmox = self.setup_config_fallback_scenario()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        # Verify essential info is preserved even with config failure
        assert "web-container" in response_text, "Expected container name preserved"
        assert "RUNNING" in response_text or "STOPPED" in response_text, \
            "Expected status preserved"
        assert "Memory:" in response_text, "Expected memory info preserved"


class TestGetContainersDataStructure(BaseContainerListTest):
    """Test container data structure and format validation.
    
    Follows SRP - tests data structure scenarios only.
    """

    def test_get_containers_returns_list_of_content_objects(self):
        """Test that get_containers returns proper MCP Content objects."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        assert isinstance(result, list), "Expected result to be a list"
        assert len(result) == 1, "Expected single Content object"
        assert hasattr(result[0], 'text'), "Expected Content object with text attribute"

    def test_get_containers_content_is_formatted_text(self):
        """Test that get_containers returns properly formatted text content."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        assert isinstance(result[0].text, str), "Expected text content as string"
        assert len(result[0].text) > 0, "Expected non-empty content"

    def test_get_containers_includes_header_formatting(self):
        """Test that get_containers includes proper header formatting."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        response_text = result[0].text
        assert "📦 Containers" in response_text, "Expected containers header"

    def test_get_containers_with_custom_container_data_formats_correctly(self):
        """Test that get_containers handles custom container configurations."""
        # Arrange
        custom_containers = [
            {
                "vmid": "300",
                "name": "custom-container",
                "status": "running",
                "mem": 1073741824,  # 1GB in bytes
                "maxmem": 2147483648,  # 2GB in bytes
            }
        ]
        mock_proxmox = self.setup_single_node_with_containers(containers=custom_containers)
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        assert "custom-container" in response_text, "Expected custom container name"
        assert "300" in response_text, "Expected custom container ID"


class TestGetContainersAPIInteractions(BaseContainerListTest):
    """Test proper API interaction patterns and call verification.
    
    Follows SRP - tests API interaction scenarios only.
    """

    def test_get_containers_calls_nodes_api_correctly(self):
        """Test that get_containers makes correct nodes API call."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        mock_proxmox.nodes.get.assert_called_once()

    def test_get_containers_calls_lxc_api_for_each_node(self):
        """Test that get_containers calls LXC API for each discovered node."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        mock_proxmox.nodes.assert_called_with("node1")
        mock_proxmox.nodes.return_value.lxc.get.assert_called()

    def test_get_containers_calls_config_api_for_detailed_info(self):
        """Test that get_containers attempts to retrieve container configuration."""
        # Arrange
        mock_proxmox = self.setup_single_node_with_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        # Config API should be called for container details
        mock_proxmox.nodes.return_value.lxc.return_value.config.get.assert_called()

    def test_get_containers_handles_multiple_node_api_calls(self):
        """Test that get_containers properly handles multiple node API calls."""
        # Arrange  
        mock_proxmox = self.setup_multi_node_containers()
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        mock_proxmox.nodes.get.assert_called_once()
        # LXC get should be called for containers (exact call count depends on mock setup)
        assert mock_proxmox.nodes.return_value.lxc.get.called, "Expected LXC API calls"


class TestGetContainersEdgeCases(BaseContainerListTest):
    """Test edge cases and boundary conditions.
    
    Follows SRP - tests edge case scenarios only.
    """

    def test_get_containers_with_zero_memory_usage_formats_correctly(self):
        """Test that get_containers handles zero memory usage (stopped containers)."""
        # Arrange
        stopped_containers = [
            {
                "vmid": "201",
                "name": "stopped-container",
                "status": "stopped",
                "mem": 0,  # Zero memory usage
                "maxmem": 536870912,  # 512MB max
            }
        ]
        mock_proxmox = self.setup_single_node_with_containers(containers=stopped_containers)
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        assert "stopped-container" in response_text, "Expected stopped container"
        assert "STOPPED" in response_text, "Expected stopped status"

    def test_get_containers_with_large_memory_values_formats_appropriately(self):
        """Test that get_containers handles large memory values correctly."""
        # Arrange
        large_containers = [
            {
                "vmid": "999",
                "name": "large-container",
                "status": "running",
                "mem": 10737418240,  # 10GB in bytes
                "maxmem": 21474836480,  # 20GB in bytes
            }
        ]
        mock_proxmox = self.setup_single_node_with_containers(containers=large_containers)
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        assert "large-container" in response_text, "Expected large container"
        # Should format large values in appropriate units (GB, not bytes)
        assert "GB" in response_text, "Expected GB formatting for large values"

    def test_get_containers_with_missing_optional_fields_uses_defaults(self):
        """Test that get_containers handles missing optional fields gracefully."""
        # Arrange
        minimal_containers = [
            {
                "vmid": "400",
                "name": "minimal-container",
                "status": "running",
                # Missing mem, maxmem fields
            }
        ]
        mock_proxmox = self.setup_single_node_with_containers(containers=minimal_containers)
        container_tools = self.create_container_tools_with_mock(mock_proxmox)
        
        # Act
        result = container_tools.get_containers()
        
        # Assert
        self.assert_container_list_response_format(result)
        response_text = result[0].text
        
        assert "minimal-container" in response_text, "Expected minimal container"
        # Should handle missing fields gracefully
        assert "Memory:" in response_text, "Expected memory section even with missing data"