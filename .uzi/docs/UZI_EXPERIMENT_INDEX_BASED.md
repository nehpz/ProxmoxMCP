# ProxmoxMCP Uzi Experiment: Index-Based Task Division

This approach assigns each agent a specific part of the task based on their index number (0, 1, 2, etc.).

## How It Works

Each agent gets a unique index at the end of their worktree path:
- Agent 0: Gets task part 1
- Agent 1: Gets task part 2
- Agent 2: Gets task part 3
- etc.

## Example 1: Module-Based Division (6 agents)

```bash
uzi prompt --agents claude:6 \
"IMPORTANT: First run 'pwd' to see your worktree path. Your agent index is the last number in the path.

Based on your index number, you are assigned to:
- Index 0: VM Operations - Implement missing features in src/proxmox_mcp/tools/vm.py (snapshots, cloning, resource updates)
- Index 1: Container Operations - Implement missing features in src/proxmox_mcp/tools/container.py (backup/restore, templates)
- Index 2: Console Operations - Fix and improve src/proxmox_mcp/tools/console/ (command execution, output streaming)
- Index 3: Node Operations - Implement monitoring in src/proxmox_mcp/tools/node.py (status, resources, health)
- Index 4: Storage Operations - Implement src/proxmox_mcp/tools/storage.py (list storage, manage ISOs, usage)
- Index 5: Testing - Increase test coverage for your assigned module (write comprehensive tests)

Start by running 'pwd' to confirm your index, then focus ONLY on your assigned module. Add a comment '# Agent {index} working on this module' at the top of your file."
```

## Example 2: Test Fix Division (4 agents)

```bash
# First, see what tests are failing
cd /Users/stephen/Projects/MCP/ProxmoxMCP && pytest -v | grep FAILED

# Then assign by index
uzi prompt --agents claude:4 \
"Check your worktree path with 'pwd'. Your index is the last number.

You are assigned to fix specific failing tests:
- Index 0: Fix all VM-related test failures (tests/test_vm_*.py, tests/vm_lifecycle/)
- Index 1: Fix all container-related test failures (tests/test_container_*.py, tests/container_lifecycle/)
- Index 2: Fix console and server test failures (tests/test_vm_console.py, tests/test_server.py)
- Index 3: Fix any remaining test failures and improve test infrastructure

Run 'pytest -v' to see failures, then fix ONLY your assigned tests."
```

## Example 3: Feature Implementation Division (5 agents)

```bash
uzi prompt --agents claude:5 \
"Check 'pwd' for your index number. Implement these specific features:

- Index 0: VM Snapshot System - Add create_snapshot, list_snapshots, delete_snapshot, rollback_snapshot to vm.py
- Index 1: Container Templates - Add create_template, deploy_from_template, list_templates to container.py  
- Index 2: Resource Monitoring - Add get_cpu_usage, get_memory_usage, get_disk_usage to node.py
- Index 3: Backup System - Add backup_vm, restore_vm, schedule_backup to a new backup.py module
- Index 4: Integration Tests - Create comprehensive integration tests for features implemented by agents 0-3

Document your implementation and create unit tests."
```

## Monitoring Index-Based Work

```bash
# See which agent is working on what
for i in {0..5}; do
  echo "=== Agent $i ==="
  uzi run "grep -l 'Agent $i' src/proxmox_mcp/tools/*.py tests/*.py 2>/dev/null || echo 'No files claimed yet'"
done

# Check progress by module
uzi run "git diff --stat"

# See test results per agent
for i in {0..3}; do
  echo "=== Agent $i test results ==="
  case $i in
    0) uzi run "pytest tests/test_vm*.py tests/vm_lifecycle/ -v --tb=short || true";;
    1) uzi run "pytest tests/test_container*.py tests/container_lifecycle/ -v --tb=short || true";;
    2) uzi run "pytest tests/test_vm_console.py tests/test_server.py -v --tb=short || true";;
    3) uzi run "pytest -v --tb=short || true";;
  esac
done
```

## Advantages of Index-Based Division

1. **No conflicts** - Each agent works on different files
2. **Clear ownership** - Easy to track who did what
3. **Specialized focus** - Agents can deep-dive into their module
4. **Efficient coverage** - No duplicate work

## Disadvantages

1. **No competition** - Can't compare different approaches
2. **Integration issues** - Modules might not work well together
3. **Uneven difficulty** - Some modules might be harder than others
4. **Single point of failure** - If one agent fails, that part is incomplete

## Best Practices

1. Have agents mark their territory immediately:
   ```python
   # Agent 0 - Working on VM operations
   # Started: [timestamp]
   ```

2. Use broadcasts to coordinate:
   ```bash
   uzi broadcast "Agent 0 has finished VM snapshots, available for integration"
   ```

3. Run integration tests at the end:
   ```bash
   uzi run "pytest tests/integration/ -v"
   ```

## Collecting Results

```bash
# After agents finish, collect metrics
echo "=== Index-Based Division Results ==="
echo "Total changes:"
uzi run "git diff --stat" | grep -E "files? changed"

echo -e "\nPer-agent contributions:"
for i in {0..5}; do
  echo "Agent $i:"
  uzi run "git log --oneline --author='Agent $i' 2>/dev/null | wc -l"
done

echo -e "\nTest coverage:"
uzi run "pytest --cov=proxmox_mcp --cov-report=term-missing"

echo -e "\nTime taken:"
# Check worktree creation times
ls -la ~/.local/share/uzi/worktrees/*/
```
