# Testing Guidelines - SOLID Principles & Clean Code

This document outlines the testing standards and expectations for the ProxmoxMCP project, based on SOLID principles and clean code practices.

## SOLID Principles in Testing

### Single Responsibility Principle (SRP)
**"Each test should have one reason to change"**

✅ **DO:**
- Test exactly one behavior per test method
- Create focused test classes for specific VM operations
- Use single-purpose test utilities and helpers

❌ **DON'T:**
- Test multiple VM operations in one test method
- Mix setup, testing, and validation concerns
- Create monolithic test classes that test everything

**Example:**
```python
# ✅ GOOD - Single responsibility
def test_start_vm_success(self):
    """Test that start_vm successfully starts a stopped VM."""
    
def test_start_vm_already_running_raises_error(self):
    """Test that start_vm raises error when VM is already running."""

# ❌ BAD - Multiple responsibilities
def test_vm_lifecycle_operations(self):
    """Test start, stop, restart, and delete operations."""
```

### Open/Closed Principle (OCP)
**"Tests should be open for extension, closed for modification"**

✅ **DO:**
- Create base test classes that can be extended
- Use configurable test fixtures
- Design test helpers that accept parameters for different scenarios

❌ **DON'T:**
- Modify existing tests when adding new features
- Hardcode test data that prevents extension
- Create tightly coupled test dependencies

**Example:**
```python
# ✅ GOOD - Extensible base class
class BaseVMOperationTest:
    def setup_vm_mock(self, status="stopped", **kwargs):
        # Configurable setup that can be extended
        
class TestStartVM(BaseVMOperationTest):
    def test_start_stopped_vm(self):
        vm_mock = self.setup_vm_mock(status="stopped")
```

### Liskov Substitution Principle (LSP)
**"Mocks should be substitutable for real objects"**

✅ **DO:**
- Ensure mocks implement the same interface as real objects
- Use consistent return types and structures
- Maintain behavioral contracts in test doubles

❌ **DON'T:**
- Create mocks that behave differently than real implementations
- Use simplified mocks that break interface contracts
- Return mock data that doesn't match real API responses

**Example:**
```python
# ✅ GOOD - Mock maintains real API contract
def mock_proxmox_api_response(self):
    return {
        "success": True,
        "message": "VM 100 started successfully", 
        "upid": "UPID:node1:000123:456789:timestamp:qmstart:100:user"
    }

# ❌ BAD - Simplified mock that breaks contract
def mock_proxmox_api_response(self):
    return "started"  # Real API returns structured response
```

### Interface Segregation Principle (ISP)
**"Tests should only depend on methods they use"**

✅ **DO:**
- Create minimal, focused mock configurations
- Use specific test fixtures for each test scenario
- Mock only the methods/attributes actually used in the test

❌ **DON'T:**
- Create large, monolithic test fixtures
- Mock entire objects when only specific methods are needed
- Force tests to depend on unused mock setup

**Example:**
```python
# ✅ GOOD - Minimal mock for specific test
def test_start_vm_success(self):
    mock_proxmox = Mock()
    mock_proxmox.nodes().qemu().status.current.get.return_value = {"status": "stopped"}
    mock_proxmox.nodes().qemu().status.start.post.return_value = "task_id"

# ❌ BAD - Over-mocked with unused methods
def test_start_vm_success(self):
    mock_proxmox = create_full_proxmox_mock()  # Mocks 50+ methods, uses 2
```

### Dependency Inversion Principle (DIP)
**"Tests should depend on abstractions, not concretions"**

✅ **DO:**
- Mock at the interface/abstraction level
- Use dependency injection for test configurations
- Abstract test data creation through factories

❌ **DON'T:**
- Mock low-level implementation details
- Hardcode dependencies in test setup
- Couple tests to specific implementation classes

**Example:**
```python
# ✅ GOOD - Mock at interface level
class TestVMTools:
    def setUp(self):
        self.mock_proxmox_api = Mock(spec=ProxmoxAPI)
        self.vm_tools = VMTools(self.mock_proxmox_api)

# ❌ BAD - Mock implementation details
class TestVMTools:
    def setUp(self):
        self.mock_http_client = Mock()
        self.mock_auth_handler = Mock()
        # Tightly coupled to implementation
```

## Clean Code Principles for Tests

### Test Structure (Arrange-Act-Assert)
```python
def test_vm_operation(self):
    # Arrange - Set up test data and mocks
    mock_proxmox = self.create_mock_proxmox()
    vm_tools = VMTools(mock_proxmox)
    
    # Act - Execute the operation being tested
    result = vm_tools.start_vm("node1", "100")
    
    # Assert - Verify the expected outcome
    self.assertEqual(result[0].text, expected_json)
    mock_proxmox.nodes().qemu().status.start.post.assert_called_once()
```

### Test Naming Convention
- Use descriptive names that explain the scenario and expected outcome
- Format: `test_[method]_[scenario]_[expected_result]`
- Examples:
  - `test_start_vm_with_stopped_vm_returns_success`
  - `test_start_vm_with_running_vm_raises_value_error`
  - `test_create_vm_with_existing_vmid_raises_value_error`

### Test Categories

#### 1. Unit Tests (Atomic & Idempotent)
- Test individual methods in isolation
- Use mocks for all external dependencies
- Focus on business logic and edge cases
- Should run fast (< 100ms per test)

#### 2. Integration Tests (Minimal)
- Test interaction between components
- Use real objects where possible, mock external systems
- Focus on critical workflows
- Acceptable to run slower (< 5s per test)

#### 3. Error Handling Tests
- Test all error conditions and exceptions
- Verify proper error messages and types
- Test edge cases and boundary conditions

### Test Data Management

#### Factory Pattern for Test Data
```python
class VMTestDataFactory:
    @staticmethod
    def create_vm_config(vmid="100", name="test-vm", status="stopped", **overrides):
        config = {
            "vmid": vmid,
            "name": name, 
            "status": status,
            "memory": 512,
            "cores": 1
        }
        config.update(overrides)
        return config
```

#### Test Isolation
- Each test must be independent
- No shared state between tests
- Use `setUp()` and `tearDown()` for consistent test environment
- Tests should pass when run individually or in any order

### Mock Guidelines

#### Mock Strategy
1. **Mock at the API boundary** - Mock ProxmoxAPI interface, not HTTP clients
2. **Use `spec` parameter** - Ensures mocks match real interface
3. **Verify interactions** - Use `assert_called_with()` to verify correct API calls
4. **Return realistic data** - Mock responses should match real API responses

#### Mock Example
```python
def setUp(self):
    self.mock_proxmox = Mock(spec=ProxmoxAPI)
    self.vm_tools = VMTools(self.mock_proxmox)
    
def test_start_vm_success(self):
    # Setup mock behavior
    self.mock_proxmox.nodes().qemu().status.current.get.return_value = {
        "status": "stopped"
    }
    self.mock_proxmox.nodes().qemu().status.start.post.return_value = "UPID:task123"
    
    # Test execution
    result = self.vm_tools.start_vm("node1", "100")
    
    # Verify behavior
    self.mock_proxmox.nodes.assert_called_with("node1")
    self.mock_proxmox.nodes().qemu.assert_called_with("100")
```

## Code Quality Standards

### Complexity Metrics
- **Cyclomatic Complexity**: ≤ 3 per test method
- **Test Method Length**: ≤ 20 lines
- **Setup Method Length**: ≤ 30 lines

### Coverage Requirements
- **Unit Test Coverage**: ≥ 95% for VM lifecycle operations
- **Error Path Coverage**: ≥ 90% for exception handling
- **Integration Coverage**: ≥ 80% for critical workflows

### Performance Standards
- **Unit Tests**: < 100ms per test
- **Integration Tests**: < 5s per test
- **Full Test Suite**: < 30s total runtime

## Existing Project Structure Analysis

### Current Test Organization
```
tests/
├── __init__.py              # Test suite initialization
├── test_server.py           # Server integration tests (13 test methods)
└── test_vm_console.py       # VM console command execution tests (5 test methods)
```

### Pytest Configuration (pyproject.toml)
```toml
[tool.pytest.ini_options]
asyncio_mode = "strict"       # Enforces strict asyncio testing
testpaths = ["tests"]         # Test discovery path
python_files = ["test_*.py"]  # Test file naming pattern
addopts = "-v"               # Verbose output by default
```

### Current Testing Patterns Observed

#### ✅ **Good Patterns in Existing Tests**
1. **Fixture-based setup** - Uses `@pytest.fixture` for reusable test setup
2. **Mock isolation** - Properly mocks external dependencies (ProxmoxAPI)
3. **Async testing** - Uses `@pytest.mark.asyncio` for async operations
4. **Parameter validation** - Tests missing/invalid parameters with `ToolError`
5. **Error scenarios** - Tests error conditions and edge cases
6. **API call verification** - Uses `assert_called_with()` to verify mock interactions

#### ⚠️ **Areas for Improvement**
1. **Mixed responsibilities** - Some tests verify multiple behaviors
2. **No test data factories** - Test data is inline in test methods
3. **Limited test organization** - All server tests in one large file
4. **Missing import issue** - `test_vm_console.py` has broken import path

### Existing Pattern Examples to Follow

#### ✅ **Fixture Pattern** (from test_server.py)
```python
@pytest.fixture
def mock_proxmox():
    """Fixture to mock ProxmoxAPI."""
    with patch("proxmox_mcp.core.proxmox.ProxmoxAPI") as mock:
        mock.return_value.nodes.get.return_value = [
            {"node": "node1", "status": "online"}
        ]
        yield mock

@pytest.fixture  
def server(mock_env_vars, mock_proxmox):
    """Fixture to create a ProxmoxMCPServer instance."""
    return ProxmoxMCPServer()
```

#### ✅ **Async Test Pattern** (from test_server.py)
```python
@pytest.mark.asyncio
async def test_get_nodes(server, mock_proxmox):
    """Test get_nodes tool."""
    response = await server.mcp.call_tool("get_nodes", {})
    result = json.loads(response[0].text)
    
    assert len(result) == 2
    assert result[0]["node"] == "node1"
```

#### ✅ **Error Testing Pattern** (from test_server.py)
```python
@pytest.mark.asyncio
async def test_get_node_status_missing_parameter(server):
    """Test get_node_status tool with missing parameter."""
    with pytest.raises(ToolError, match="Field required"):
        await server.mcp.call_tool("get_node_status", {})
```

#### ✅ **Mock Verification Pattern** (from test_vm_console.py)
```python
@pytest.mark.asyncio
async def test_execute_command_success(vm_console, mock_proxmox):
    """Test successful command execution."""
    result = await vm_console.execute_command("node1", "100", "ls -l")
    
    # Verify behavior
    assert result["success"] is True
    
    # Verify API calls
    mock_proxmox.nodes.return_value.qemu.assert_called_with("100")
```

#### ⚠️ **Import Pattern Issue to Fix**
```python
# ❌ BROKEN - Current import in test_vm_console.py
from proxmox_mcp.tools.vm_console import VMConsoleManager

# ✅ CORRECT - Should be
from proxmox_mcp.tools.console.manager import VMConsoleManager
```

### Recommended File Organization (Updated)

Building on existing patterns, here's the updated structure:

```
tests/
├── __init__.py                    # Existing - Test suite initialization
├── conftest.py                    # NEW - Shared fixtures and configuration
├── test_server.py                 # Existing - Keep for server integration tests
├── test_vm_console.py            # Existing - Fix import path
├── vm_lifecycle/                  # NEW - VM lifecycle test organization
│   ├── __init__.py
│   ├── test_create_vm.py         # Atomic tests for VM creation
│   ├── test_start_vm.py          # Atomic tests for VM starting
│   ├── test_stop_vm.py           # Atomic tests for VM stopping
│   ├── test_shutdown_vm.py       # Atomic tests for VM shutdown
│   ├── test_restart_vm.py        # Atomic tests for VM restart
│   ├── test_delete_vm.py         # Atomic tests for VM deletion
│   └── test_vm_lifecycle_integration.py  # End-to-end workflow tests
└── fixtures/                      # NEW - Shared test utilities
    ├── __init__.py
    ├── vm_data_factory.py         # Test data creation factories
    ├── mock_helpers.py            # Reusable mock configurations
    └── base_test_classes.py       # Base classes following existing patterns
```

## Enforcement

### Pre-commit Hooks
- Run test suite on commit
- Enforce code coverage thresholds
- Validate test naming conventions

### Code Review Checklist
- [ ] Tests follow SRP (one behavior per test)
- [ ] Mocks implement proper interfaces (LSP)
- [ ] Test setup is minimal and focused (ISP)
- [ ] Tests are independent and idempotent
- [ ] Error cases are tested
- [ ] Test names are descriptive
- [ ] Coverage requirements are met

## Examples of Good vs Bad Tests

### ✅ Good Test Example
```python
class TestStartVM(BaseVMTest):
    def test_start_vm_with_stopped_vm_returns_success_response(self):
        # Arrange
        self.setup_vm_mock(status="stopped")
        self.mock_proxmox.nodes().qemu().status.start.post.return_value = "UPID:123"
        
        # Act
        result = self.vm_tools.start_vm("node1", "100")
        
        # Assert
        response_data = json.loads(result[0].text)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "VM 100 started successfully")
        self.assertEqual(response_data["upid"], "UPID:123")
```

### ❌ Bad Test Example
```python
def test_vm_operations(self):
    # Multiple responsibilities, not atomic, hard to debug
    vm_tools = VMTools(real_proxmox_connection)  # Not mocked
    vm_tools.create_vm("node1", "100", "test")   # Side effects
    vm_tools.start_vm("node1", "100")
    vm_tools.stop_vm("node1", "100") 
    vm_tools.delete_vm("node1", "100")
    # No specific assertions, tests everything at once
```

---

*Following these guidelines ensures our tests are maintainable, reliable, and support long-term code evolution.*