# ProxmoxMCP Project Structure

## Root Directory
```
ProxmoxMCP/
├── .venv/                    # Virtual environment (created by uv)
├── alembic/                  # Database migrations (if used)
├── docs/                     # Documentation and scripts
├── graphics/                 # Project graphics/images
├── logs/                     # Log files directory
├── proxmox-config/           # Configuration files
│   └── config.json          # Main config (from template)
├── src/                     # Source code
│   └── proxmox_mcp/         # Main package
├── tests/                   # Test suite
├── .gitignore              # Git ignore rules
├── alembic.ini             # Alembic configuration
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # Project documentation
├── TESTING_GUIDELINES.md   # Testing standards
└── uv.lock                 # Dependency lock file
```

## Source Code Structure
```
src/proxmox_mcp/
├── __init__.py
├── server.py               # Main MCP server implementation
├── config/                 # Configuration handling
│   ├── __init__.py
│   ├── loader.py          # Config loading logic
│   └── models.py          # Pydantic config models
├── core/                   # Core functionality
│   ├── __init__.py
│   ├── logging.py         # Logging setup
│   └── proxmox.py         # Proxmox API manager
├── formatting/             # Output formatting
│   ├── __init__.py
│   ├── colors.py          # Color definitions
│   ├── components.py      # UI components
│   ├── formatters.py      # Format functions
│   ├── templates.py       # Output templates
│   └── theme.py           # Theme management
├── tools/                  # MCP tool implementations
│   ├── __init__.py
│   ├── base.py           # Base tool class
│   ├── definitions.py     # Tool descriptions
│   ├── cluster.py        # Cluster operations
│   ├── container.py      # Container management
│   ├── node.py           # Node operations
│   ├── storage.py        # Storage management
│   ├── vm.py             # VM operations
│   └── console/          # Console operations
│       ├── __init__.py
│       └── manager.py    # Console command execution
└── utils/                  # Utilities
    ├── __init__.py
    ├── auth.py            # Authentication helpers
    └── logging.py         # Logging utilities
```

## Test Structure
```
tests/
├── __init__.py
├── conftest.py             # Pytest configuration and fixtures
├── test_server.py          # Server tests
├── test_vm_console.py      # Console operation tests
├── fixtures/               # Test fixtures and mocks
├── container_lifecycle/    # Container lifecycle tests
└── vm_lifecycle/           # VM lifecycle tests
```

## Key Files
- `server.py`: Entry point, MCP server setup, tool registration
- `config/models.py`: Configuration schema with Pydantic
- `core/proxmox.py`: Proxmox API connection management
- `tools/base.py`: Base class for all tool implementations
- `formatting/templates.py`: Output formatting templates
- `conftest.py`: Shared test fixtures and configuration