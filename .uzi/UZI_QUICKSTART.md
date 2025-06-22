# Using Uzi with ProxmoxMCP

Quick guide for parallel development on ProxmoxMCP using Uzi.

## 🆕 Experiment Guides Available!

Compare two different approaches for parallel development:

1. **[Index-Based Division](UZI_EXPERIMENT_INDEX_BASED.md)** - Each agent gets part of the task
2. **[All-Complete](UZI_EXPERIMENT_ALL_COMPLETE.md)** - All agents do the full task
3. **[Comparison Guide](UZI_EXPERIMENT_GUIDE.md)** - Run experiments to compare approaches

## Setup

1. Ensure uzi.yaml is in the project root (already configured)
2. Install Uzi if not already: `go install github.com/devflowinc/uzi@latest`

## Important: How Uzi Works

**Uzi assigns random names to agents** (like emily, samuel, adam, etc). You cannot pre-assign specific work to "Agent 1" or "Agent 2" in the config. Instead, you must either:

1. Give all agents the same task and let them self-organize
2. Use `uzi broadcast` to assign work after seeing agent names
3. Have agents claim work by adding their name to files

## Quick Start Examples

### Fix Failing Tests (Recommended First Task)

```bash
# Start 6 agents to fix different failing tests
uzi prompt --agents claude:6 \
  "Fix failing tests in ProxmoxMCP. Run 'pytest -v' first to see failures. Each agent should pick different test files to work on. Add '# Working on this - [your_agent_name]' at the top of your chosen test file."
```

### Implement Missing Features

```bash
# Start 5 agents to implement features in different modules
uzi prompt --agents claude:5 \
  "Check src/proxmox_mcp/tools/ for TODO comments and missing features. Each agent claim a different file (vm.py, container.py, etc) by adding a comment. Implement missing functionality with tests."
```

### Improve Test Coverage

```bash
# Start 4 agents to improve test coverage
uzi prompt --agents claude:4 \
  "Run 'pytest --cov=proxmox_mcp' to see coverage. Each agent work on testing different untested modules. Focus on getting coverage above 80%."
```

### Targeted Work Assignment

```bash
# Start agents first
uzi prompt --agents claude:5 "Wait for work assignment via broadcast"

# Check agent names
uzi ls

# Then assign specific work
uzi broadcast "emily - Work on VM operations in src/proxmox_mcp/tools/vm.py"
uzi broadcast "samuel - Work on container operations in src/proxmox_mcp/tools/container.py"
uzi broadcast "adam - Improve test coverage for node operations"
```

## Monitoring Progress

```bash
# List all agents and their status
uzi ls

# Watch agents in real-time
uzi ls -w

# Check what an agent is doing
uzi run "git status"
uzi run "git diff --stat"

# See test results across all agents
uzi run "pytest --tb=short || true"
```

## Saving Good Work

```bash
# When an agent does good work
uzi checkpoint agent-name "feat: add VM snapshot functionality"

# Kill all agents when done
uzi kill all
```

## Tips

1. **Self-organization works best** - Let agents claim files with comments
2. **Use broadcast for coordination** - After agents start, guide them with broadcasts
3. **Monitor for conflicts** - Use `uzi ls -w` to watch for agents working on same files
4. **Each agent is isolated** - They have separate git worktrees and Python environments
5. **Check the guides** - See PARALLEL_DEVELOPMENT_GUIDE.md for detailed strategies

## Common Commands Inside Agent Sessions

- `pytest` - Run all tests
- `pytest -v` - Verbose test output
- `pytest tests/test_vm_console.py` - Run specific test
- `pytest --cov=proxmox_mcp` - Test coverage
- `black src/ tests/` - Format code
- `mypy src/` - Type check
- `ruff check` - Lint code

## Agent Worktree Locations

Agents work in: `~/.local/share/uzi/worktrees/[agent-name]-[project]-[hash]/`

You can manually check an agent's work:

```bash
cd ~/.local/share/uzi/worktrees/emily-proxmoxmcp-*/
git diff
```
