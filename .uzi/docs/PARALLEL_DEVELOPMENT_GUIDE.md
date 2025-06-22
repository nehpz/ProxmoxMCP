# ProxmoxMCP Parallel Development Guide for Uzi

This guide provides strategies for using Uzi to parallelize development on ProxmoxMCP.

## Project Structure Overview

```
src/proxmox_mcp/
├── server.py              # MCP server implementation
├── tools/                 # Tool implementations (main work area)
│   ├── vm.py             # Virtual Machine operations
│   ├── container.py      # LXC Container operations  
│   ├── node.py           # Proxmox node operations
│   ├── cluster.py        # Cluster operations
│   ├── storage.py        # Storage operations
│   └── console/          # Console access functionality
├── core/                  # Core client and utilities
├── config/               # Configuration handling
├── formatting/           # Output formatting
└── utils/                # Utility functions
```

## Parallel Work Strategies

### Strategy 1: Fix All Failing Tests
Each agent works on different test files to maximize coverage:

```bash
uzi prompt --agents claude:6 "Fix failing tests in the ProxmoxMCP project. Check 'pytest -v' output first. Each agent should pick different test files from the tests/ directory to avoid conflicts. Add a comment with your agent name at the top of any test file you're working on."
```

### Strategy 2: Implement Missing Features
Agents self-organize to implement different features:

```bash
uzi prompt --agents claude:5 "Review src/proxmox_mcp/tools/ directory. Each agent should claim a different tool file (vm.py, container.py, node.py, cluster.py, or storage.py) by adding a comment with your name. Implement any TODO items or missing functionality you find. Create corresponding tests."
```

### Strategy 3: Improve Code Quality
Multiple agents work on different aspects of code quality:

```bash
uzi prompt --agents claude:4 "Improve code quality in ProxmoxMCP. Each agent focus on different aspects: 1) Add type hints where missing, 2) Add docstrings to undocumented functions, 3) Fix linting issues (run 'ruff check'), 4) Improve test coverage. Coordinate by checking what others are doing first."
```

### Strategy 4: Targeted Module Development
Assign specific modules after agents are created:

```bash
# Start agents
uzi prompt --agents claude:6 "Wait for specific work assignment via broadcast message"

# Then assign work (check names with 'uzi ls' first)
uzi broadcast "adam - Work on VM operations in src/proxmox_mcp/tools/vm.py. Add snapshot functionality."
uzi broadcast "emily - Work on container operations in src/proxmox_mcp/tools/container.py. Add backup/restore."
uzi broadcast "samuel - Work on console operations in src/proxmox_mcp/tools/console/. Improve command execution."
# etc...
```

### Strategy 5: Test Coverage Competition
Make it a game to see who can improve test coverage the most:

```bash
uzi prompt --agents claude:6 "Competition: Improve test coverage for ProxmoxMCP. Run 'pytest --cov=proxmox_mcp' to see current coverage. Each agent should work on different source files to increase coverage. Report your coverage improvements when done."
```

## Coordination Tips

1. **File Claiming**: Have agents add comments with their name to claim files
2. **Status Updates**: Use `git status` and `git diff` to see what others are doing  
3. **Conflict Avoidance**: Work on different modules or test files
4. **Communication**: Agents can leave TODO comments for each other

## Testing Guidelines

- Follow SOLID principles (see TESTING_GUIDELINES.md)
- Each test should test ONE behavior
- Mock Proxmox API calls - don't hit real servers
- Use fixtures from tests/fixtures/
- Run tests before committing changes

## Code Quality Standards

- Format: `black src/ tests/`
- Type check: `mypy src/`
- Lint: `ruff check src/ tests/`
- Test: `pytest` or `pytest -v`
- Coverage: `pytest --cov=proxmox_mcp`

## Common Areas Needing Work

1. **VM Operations** (src/proxmox_mcp/tools/vm.py)
   - Snapshot management
   - Clone operations
   - Resource scaling

2. **Container Operations** (src/proxmox_mcp/tools/container.py)
   - Backup/restore
   - Template management
   - Resource limits

3. **Console Operations** (src/proxmox_mcp/tools/console/)
   - Output streaming
   - Session management
   - Authentication

4. **Storage Operations** (src/proxmox_mcp/tools/storage.py)
   - ISO management
   - Template storage
   - Usage monitoring

5. **Test Coverage**
   - Integration tests
   - Error handling tests
   - Mock improvements

## Debugging Tips

- Check `proxmox_mcp.log` for detailed logs
- Set `logging.level` to "DEBUG" in config.json
- Use `pytest -v` for verbose test output
- Use `pytest --pdb` to debug test failures
- Run `pytest -k test_name` to run specific tests

## Example Workflow

1. Start agents with a general task
2. Let them self-organize or assign specific work
3. Monitor progress with `uzi ls -w`
4. Check their work with `uzi run "git diff"`
5. Checkpoint good solutions with `uzi checkpoint`
