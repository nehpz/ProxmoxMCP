# Code Style and Conventions

## General Style
- **Python Version**: 3.12+ (with type hints)
- **Code Formatting**: Black (line length: default)
- **Linting**: Ruff (with configurations in pyproject.toml)
- **Type Checking**: mypy (strict mode enabled)
- **Import Style**: Grouped imports, absolute imports preferred

## Naming Conventions
- **Classes**: PascalCase (e.g., `ProxmoxTool`, `VMTools`, `NodeTools`)
- **Functions/Methods**: snake_case (e.g., `get_vms`, `execute_command`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `GET_VMS_DESC`)
- **Private methods**: Leading underscore (e.g., `_format_response`)

## Documentation Standards
- **Docstrings**: Triple quotes, Google/NumPy style
- **Module docstrings**: Explain module purpose, main components, and usage
- **Class docstrings**: Describe class purpose and key attributes
- **Method docstrings**: Include parameters, returns, and raises sections
- **Type hints**: Required for all function parameters and returns

## Testing Conventions
- **Test Structure**: Mirror source code structure in `tests/` directory
- **Test Files**: Named `test_*.py`
- **Test Classes**: Named `Test{ClassName}`
- **Test Methods**: Named `test_{behavior}_when_{condition}`
- **SOLID Principles**: Single responsibility per test, focused test classes
- **Fixtures**: Use pytest fixtures for setup/teardown
- **Mocking**: Mock external dependencies (Proxmox API calls)

## Error Handling
- Use specific exception types
- Include helpful error messages
- Log errors appropriately
- Return formatted error responses in MCP tools

## Project Structure
```
src/proxmox_mcp/
├── server.py          # Main server implementation
├── config/            # Configuration handling
├── core/              # Core functionality
├── formatting/        # Output formatting
├── tools/             # Tool implementations
│   └── console/       # VM console operations
└── utils/             # Utilities
```

## Key Patterns
- **Base Classes**: All tools inherit from `ProxmoxTool` base class
- **Response Formatting**: Use formatting templates for consistent output
- **Configuration**: Pydantic models for validation
- **Async Support**: Tools can be sync or async
- **Logging**: Structured logging with configurable levels