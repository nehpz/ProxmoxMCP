# Suggested Commands for ProxmoxMCP Development

## Project Setup
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies with dev extras
uv pip install -e ".[dev]"
```

## Running the Server
```bash
# Run the MCP server (requires PROXMOX_MCP_CONFIG env var)
PROXMOX_MCP_CONFIG="proxmox-config/config.json" python -m proxmox_mcp.server

# Alternative: Run as module
python -m proxmox_mcp.server
```

## Testing
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_server.py

# Run with coverage
pytest --cov=proxmox_mcp
```

## Code Quality Tools
```bash
# Format code with Black
black .

# Check formatting without changes
black --check .

# Run linter
ruff .

# Fix linting issues
ruff --fix .

# Type checking
mypy .
```

## Development Workflow
```bash
# Before committing: Run all checks
black --check .
ruff .
mypy .
pytest

# Format and fix issues
black .
ruff --fix .
```

## Git Commands
```bash
# Common git operations
git status
git diff
git add .
git commit -m "message"
git push origin main
```

## Utility Commands (Darwin/macOS)
```bash
# List files
ls -la

# Change directory
cd path/to/directory

# Find files
find . -name "*.py"

# Search in files (use ripgrep if available)
rg "pattern" .
grep -r "pattern" .

# View file content
cat filename
less filename
```

## Configuration
```bash
# Copy config template
cp config/config.example.json proxmox-config/config.json

# Edit config
nano proxmox-config/config.json  # or your preferred editor
```

## Dependencies
```bash
# Update dependencies
uv pip install -U -e ".[dev]"

# Show installed packages
uv pip list
```