# ProxmoxMCP Uzi Experiment: Index-Based vs All-Complete Comparison

This experiment compares two different approaches for parallel development using Uzi:

1. **Index-Based Division** - Each agent gets a specific part of the task
2. **All-Agents Complete** - Every agent attempts the entire task

## Quick Start: Run Both Experiments

### Test 1: Fixing All Failing Tests

```bash
# First, check current test status
cd /Users/stephen/Projects/MCP/ProxmoxMCP
pytest --tb=short | grep -E "(failed|passed)" | tail -1

# Approach 1: Index-Based Division (4 agents)
uzi prompt --agents claude:4 \
"Check your worktree path with 'pwd'. Your index is the last number.
Fix failing tests based on your index:
- Index 0: Fix VM-related test failures (tests/test_vm*.py, tests/vm_lifecycle/)
- Index 1: Fix container test failures (tests/test_container*.py, tests/container_lifecycle/)
- Index 2: Fix console/server test failures (tests/test_vm_console.py, tests/test_server.py)
- Index 3: Fix any remaining test failures and test infrastructure
Run 'pytest -v' first, then fix ONLY your assigned tests."

# Monitor progress
uzi ls -w

# After completion, save results
mkdir -p experiment_results/test_fix_indexed
uzi run "pytest --tb=short" > experiment_results/test_fix_indexed/results.txt
uzi run "git diff --stat" > experiment_results/test_fix_indexed/changes.txt

# Kill all agents
uzi kill all

# Approach 2: All-Agents Complete (4 agents)
uzi prompt --agents claude:4 \
"Fix ALL failing tests in the ProxmoxMCP project.
1. Run 'pytest -v' to see all failures
2. Fix as many failing tests as possible
3. Ensure your fixes don't break other tests
4. Run 'pytest' at the end to verify
Work independently to create a complete solution."

# Monitor progress
uzi ls -w

# After completion, save results
mkdir -p experiment_results/test_fix_all_complete
for agent in $(uzi ls | grep -v AGENT | awk '{print $1}'); do
  echo "=== Agent: $agent ===" >> experiment_results/test_fix_all_complete/results.txt
  cd ~/.local/share/uzi/worktrees/*$agent*/
  pytest --tb=short | grep -E "(failed|passed)" | tail -1 >> experiment_results/test_fix_all_complete/results.txt
  git diff --stat >> experiment_results/test_fix_all_complete/results.txt
  echo "" >> experiment_results/test_fix_all_complete/results.txt
done
```

### Test 2: Implementing VM Snapshot Feature

```bash
# Approach 1: Index-Based Division (3 agents)
uzi prompt --agents claude:3 \
"Check 'pwd' for your index number. Work on VM snapshots based on your role:
- Index 0: Implement core snapshot functions in src/proxmox_mcp/tools/vm.py
  (create_snapshot, delete_snapshot, list_snapshots, rollback_snapshot)
- Index 1: Create comprehensive tests in tests/test_vm_snapshots.py
- Index 2: Add error handling, logging, and documentation
Each agent focuses ONLY on their assigned part."

# Save results after completion
mkdir -p experiment_results/snapshot_indexed
uzi run "pytest tests/test_vm_snapshots.py" > experiment_results/snapshot_indexed/results.txt
uzi run "git diff --stat" > experiment_results/snapshot_indexed/changes.txt

# Kill all and try complete approach
uzi kill all

# Approach 2: All-Agents Complete (3 agents)
uzi prompt --agents claude:3 \
"Implement a complete VM snapshot system for ProxmoxMCP:
1. Add snapshot methods to src/proxmox_mcp/tools/vm.py
2. Create tests in tests/test_vm_snapshots.py
3. Add documentation and error handling
4. Ensure all tests pass
Create your own complete implementation independently."

# Save results
mkdir -p experiment_results/snapshot_all_complete
# ... similar collection as above
```

## Automated Comparison Script

<function_calls>
<invoke name="desktop-commander:write_file">
<parameter name="content">#!/bin/bash
# compare_approaches.sh - Compare index-based vs all-complete approaches

echo "=== ProxmoxMCP Uzi Experiment Results ==="
echo "Date: $(date)"
echo ""

# Function to analyze results
analyze_results() {
    local approach=$1
    local dir=$2

    echo "=== $approach Approach ==="

    if [[ "$approach" == "Index-Based" ]]; then
        # For index-based, we have one combined result
        echo "Combined Results:"
        if [ -f "$dir/results.txt" ]; then
            grep -E "(passed|failed)" "$dir/results.txt" | tail -1
            echo "Total changes:"
            grep "files changed" "$dir/changes.txt" | tail -1
        fi
    else
        # For all-complete, analyze each agent
        echo "Individual Agent Results:"
        if [ -f "$dir/results.txt" ]; then
            grep -B1 -E "(passed|failed)" "$dir/results.txt"
        fi

        # Find best performer
        echo -e "\nBest Performer:"
        # Extract pass rates and find highest
        grep -E "[0-9]+ passed" "$dir/results.txt" | sort -nr | head -1
    fi

    echo ""
}

# Compare test fixing approaches
if [ -d "experiment_results/test_fix_indexed" ] && [ -d "experiment_results/test_fix_all_complete" ]; then
    echo "### Test Fixing Comparison ###"
    analyze_results "Index-Based" "experiment_results/test_fix_indexed"
    analyze_results "All-Complete" "experiment_results/test_fix_all_complete"
fi

# Compare feature implementation approaches
if [ -d "experiment_results/snapshot_indexed" ] && [ -d "experiment_results/snapshot_all_complete" ]; then
    echo "### Snapshot Feature Comparison ###"
    analyze_results "Index-Based" "experiment_results/snapshot_indexed"
    analyze_results "All-Complete" "experiment_results/snapshot_all_complete"
fi

# Time analysis (if we tracked it)
echo "### Efficiency Analysis ###"
echo "Index-Based Approach:"
echo "- Pros: No duplicate work, clear ownership, less merge conflicts"
echo "- Cons: No alternative solutions, potential integration issues"
echo ""
echo "All-Complete Approach:"echo "- Pros: Multiple solutions to compare, best practices emerge, redundancy"
echo "- Cons: Duplicate work, resource intensive, harder to coordinate"
echo ""

# Code quality comparison
echo "### Code Quality Metrics ###"
for dir in experiment_results/*/; do
    if [ -d "$dir" ]; then
        echo "$(basename $dir):"
        # Count test files created
        echo -n "  Test files created: "
        grep -c "create mode.*test" "$dir/changes.txt" 2>/dev/null || echo "0"
        # Count lines of code
        echo -n "  Total lines changed: "
        grep -oE "[0-9]+ insertions" "$dir/changes.txt" | grep -oE "[0-9]+" | paste -sd+ | bc 2>/dev/null || echo "0"
    fi
done

echo ""
echo "### Recommendations ###"
echo "Use Index-Based when:"
echo "- Task has clear, separable components"
echo "- Time is limited"
echo "- Team members have different expertise"
echo ""
echo "Use All-Complete when:"
echo "- Exploring different solutions"
echo "- Quality is more important than efficiency"
echo "- Task is complex with many valid approaches"