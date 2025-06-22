# ProxmoxMCP Uzi Experiment: All Agents Complete Full Task

This approach has every agent attempt to complete the entire task independently, allowing comparison of different solutions.

## How It Works

All agents receive the same complete assignment and work in parallel to solve it. This creates multiple solutions that can be compared for quality, approach, and completeness.

## Example 1: Complete Test Suite Fix (6 agents)

```bash
uzi prompt --agents claude:6 \
"Fix ALL failing tests in the ProxmoxMCP project. Each agent should:
1. Run 'pytest -v' to see all failures
2. Fix as many failing tests as possible
3. Ensure your fixes don't break other tests
4. Add comments explaining what you fixed and why
5. Run 'pytest' at the end to verify your work

Work independently to create a complete solution. Try different approaches if your first attempt doesn't work."
```

## Example 2: Complete Feature Implementation (5 agents)

```bash
uzi prompt --agents claude:5 \
"Implement a complete VM snapshot system for ProxmoxMCP. Requirements:
1. Add snapshot methods to src/proxmox_mcp/tools/vm.py:
   - create_snapshot(vm_id, name, description)
   - list_snapshots(vm_id)
   - delete_snapshot(vm_id, snapshot_name)
   - rollback_snapshot(vm_id, snapshot_name)
2. Add complete test coverage in tests/test_vm_snapshots.py
3. Update documentation
4. Ensure all tests pass

Create your own complete implementation. Be creative with error handling and edge cases."
```

## Example 3: Code Quality Improvement (4 agents)

```bash
uzi prompt --agents claude:4 \
"Improve the overall code quality of ProxmoxMCP:
1. Add comprehensive type hints to all functions
2. Add missing docstrings with examples
3. Fix all linting issues (run 'ruff check')
4. Improve test coverage to >80% (check with pytest --cov)
5. Refactor any code smells you find

Each agent should review the entire codebase and make improvements. Focus on making the code more maintainable and robust."
```

## Example 4: Full Module Implementation (5 agents)

```bash
uzi prompt --agents claude:5 \
"Implement a complete backup/restore system for ProxmoxMCP:
1. Create src/proxmox_mcp/tools/backup.py with:
   - backup_vm(vm_id, storage, compression='zstd')
   - backup_container(ct_id, storage, compression='zstd') 
   - list_backups(storage=None)
   - restore_vm(backup_id, new_id=None, storage=None)
   - restore_container(backup_id, new_id=None, storage=None)
   - delete_backup(backup_id)
   - schedule_backup(resource_id, schedule, retention)
2. Create comprehensive tests in tests/test_backup.py
3. Add integration with existing VM and container tools
4. Include error handling and logging

Create a complete, production-ready implementation."
```

## Monitoring All-Agents Work

```bash
# Watch all agents' progress
uzi ls -w

# Compare approaches - see what files each agent is modifying
uzi run "git status --short"

# Check test results across all agents
uzi run "pytest --tb=short | grep -E '(passed|failed|errors)' | tail -1"

# See different implementation approaches
echo "=== Comparing implementations ==="
for agent in $(uzi ls | grep -v AGENT | awk '{print $1}'); do
  echo -e "\n--- Agent: $agent ---"
  uzi run "git diff --stat" | grep "$agent"
done
```

## Comparing Solutions

```bash
# After agents complete, compare their approaches

# 1. Test success rates
echo "=== Test Results Comparison ==="
for agent in $(uzi ls | grep -v AGENT | awk '{print $1}'); do
  echo -n "$agent: "
  cd ~/.local/share/uzi/worktrees/*$agent*/
  pytest --tb=no | grep -E "(passed|failed)" | tail -1
done

# 2. Code changes
echo -e "\n=== Code Volume Comparison ==="
for agent in $(uzi ls | grep -v AGENT | awk '{print $1}'); do
  echo -n "$agent: "
  cd ~/.local/share/uzi/worktrees/*$agent*/
  git diff --stat | tail -1
done

# 3. Approach differences
echo -e "\n=== Implementation Approaches ==="
# Compare how different agents implemented the same feature
for agent in $(uzi ls | grep -v AGENT | awk '{print $1}'); do
  echo -e "\n--- $agent approach ---"
  cd ~/.local/share/uzi/worktrees/*$agent*/
  # Example: Check how they implemented create_snapshot
  git diff | grep -A 10 "def create_snapshot" | head -15
done
```

## Quality Metrics Comparison

Create a comparison script to evaluate solutions:

```bash
# Save as compare_solutions.sh
#!/bin/bash

echo "Agent,Tests Passed,Tests Failed,Coverage,Lines Added,Lines Removed,Pylint Score"

for dir in ~/.local/share/uzi/worktrees/*proxmoxmcp*/; do
  agent=$(basename $dir | cut -d'-' -f1)
  cd $dir
  
  # Test results
  test_output=$(pytest --tb=no 2>&1 | grep -E "(passed|failed)" | tail -1)
  passed=$(echo $test_output | grep -oE "[0-9]+ passed" | grep -oE "[0-9]+")
  failed=$(echo $test_output | grep -oE "[0-9]+ failed" | grep -oE "[0-9]+")
  
  # Coverage
  coverage=$(pytest --cov=proxmox_mcp --cov-report=term | grep "TOTAL" | awk '{print $4}')
  
  # Code changes
  stats=$(git diff --stat | tail -1)
  added=$(echo $stats | grep -oE "[0-9]+ insertion" | grep -oE "[0-9]+")
  removed=$(echo $stats | grep -oE "[0-9]+ deletion" | grep -oE "[0-9]+")
  
  # Code quality (if pylint available)
  pylint_score=$(pylint src/proxmox_mcp 2>/dev/null | grep "rated at" | grep -oE "[0-9]+\.[0-9]+" || echo "N/A")
  
  echo "$agent,$passed,$failed,$coverage,$added,$removed,$pylint_score"
done
```

## Advantages of All-Agents-Complete Approach

1. **Multiple solutions** - Compare different approaches
2. **Quality competition** - Agents may try harder knowing others are doing the same
3. **Redundancy** - If one fails, others might succeed
4. **Learning opportunity** - See various ways to solve the same problem
5. **Best-of-breed** - Can cherry-pick the best parts from each solution

## Disadvantages

1. **Duplicate work** - Inefficient use of resources
2. **Merge conflicts** - Harder to integrate multiple complete solutions
3. **Inconsistent approaches** - Different coding styles and patterns
4. **Harder to track** - More complex to monitor who's doing what

## Best Practices

1. Let agents work independently without coordination
2. Don't use broadcasts that might influence approaches
3. Set a time limit for fair comparison
4. Use the same starting commit for all agents
5. Evaluate based on objective metrics

## Selecting the Best Solution

After all agents complete:

```bash
# 1. Run automated comparison
./compare_solutions.sh > results.csv

# 2. Manual code review of top performers
# Review the agent with highest test pass rate
best_agent=$(./compare_solutions.sh | sort -t',' -k2 -nr | head -2 | tail -1 | cut -d',' -f1)
cd ~/.local/share/uzi/worktrees/*$best_agent*/
git diff

# 3. Cherry-pick best implementations
# If different agents excelled at different parts
uzi checkpoint $agent1 "feat: excellent snapshot implementation"
uzi checkpoint $agent2 "feat: superior error handling"

# 4. Or checkpoint the overall best solution
uzi checkpoint $best_agent "feat: best complete implementation"
```

## Results Analysis Template

```markdown
## All-Agents Complete Task Results

### Task: [Description]
### Number of Agents: X
### Time Limit: Y minutes

### Results Summary

| Agent | Tests Passed | Coverage | Approach | Time Taken | Notes |
|-------|--------------|----------|----------|------------|-------|
| adam  | 45/50        | 85%      | OOP      | 25 min     | Best error handling |
| emily | 48/50        | 82%      | Functional | 22 min   | Most concise |
| sam   | 50/50        | 90%      | Mixed    | 28 min     | Most complete |

### Best Practices Observed
- [What worked well]

### Common Pitfalls
- [What multiple agents struggled with]

### Recommended Solution
Agent [X] because [reasons]
```
