# ProxmoxMCP Parallel Development Experiment Guide

Compare two different approaches for using Uzi to parallelize development work.

## 🆕 Analysis Agent Enhancement

We now use an AI Analysis Agent to provide intelligent evaluation beyond what scripts can measure. See:
- [Analysis Agent Guide](UZI_ANALYSIS_AGENT_GUIDE.md) - How to use the analysis agent
- [Analysis Agent Explained](ANALYSIS_AGENT_EXPLAINED.md) - Why AI analysis is crucial
- [Complete Workflow](COMPLETE_UZI_EXPERIMENT_WORKFLOW.md) - Full experiment with analysis

## Experiment Overview

We're testing two hypotheses:
1. **Division of Labor** (Index-Based) - Specialized agents working on different parts produce better integrated results
2. **Competitive Redundancy** (All-Complete) - Multiple agents solving the entire problem produce higher quality through competition

## The Two Approaches

### 1. Index-Based Task Division
- Each agent gets a unique piece based on their index (0, 1, 2, etc.)
- No overlap, no competition
- Similar to a traditional team with assigned roles
- See: [UZI_EXPERIMENT_INDEX_BASED.md](UZI_EXPERIMENT_INDEX_BASED.md)

### 2. All Agents Complete Task  
- Every agent attempts the full task
- Creates multiple complete solutions
- Best solution wins
- See: [UZI_EXPERIMENT_ALL_COMPLETE.md](UZI_EXPERIMENT_ALL_COMPLETE.md)

## Quick Experiment: Test Fixing Challenge

### Setup
```bash
cd /Users/stephen/Projects/MCP/ProxmoxMCP
# Record starting state
pytest --tb=no | tee experiment_results/baseline.txt
```

### Round 1: Index-Based Approach
```bash
# Start 4 agents with divided work
uzi prompt --agents claude:4 \
"Check 'pwd' for your index (last number in path).
Index 0: Fix tests/vm_lifecycle/ tests
Index 1: Fix tests/container_lifecycle/ tests  
Index 2: Fix tests/test_vm_console.py
Index 3: Fix tests/test_server.py
Focus ONLY on your assigned tests."

# Wait for completion (monitor with: uzi ls -w)
# Then collect results
./compare_approaches.sh
```

### Round 2: All-Complete Approach
```bash
# Reset to baseline
git reset --hard

# Start 4 agents with same task
uzi prompt --agents claude:4 \
"Fix ALL failing tests in ProxmoxMCP. Create the most comprehensive solution possible."

# Wait and collect results
./compare_approaches.sh
```

## Metrics to Compare

### Quantitative Metrics
1. **Test Pass Rate** - How many tests were fixed?
2. **Code Volume** - Lines added/removed
3. **Time to Complete** - How long did each approach take?
4. **Test Coverage** - Did coverage improve?

### Qualitative Metrics
1. **Code Quality** - Which produces cleaner code?
2. **Integration** - Do the pieces work together?
3. **Innovation** - Which approach found creative solutions?
4. **Completeness** - Which left fewer edge cases?

## Running Your Own Experiment

### Step 1: Choose a Task
Good tasks for comparison:
- Fix all failing tests
- Implement a new feature (like snapshots)
- Improve code quality (add types, docs, etc.)
- Increase test coverage

### Step 2: Prepare Baseline
```bash
# Create experiment directory
mkdir -p experiment_results/your_experiment/{indexed,all_complete}

# Save baseline state
git rev-parse HEAD > experiment_results/your_experiment/baseline_commit.txt
pytest --tb=no > experiment_results/your_experiment/baseline_tests.txt
pytest --cov=proxmox_mcp --cov-report=term > experiment_results/your_experiment/baseline_coverage.txt
```

### Step 3: Run Index-Based
```bash
# Start agents with clear division
uzi prompt --agents claude:N "YOUR_INDEXED_PROMPT"

# Monitor
uzi ls -w

# Collect results
uzi run "pytest --tb=no" > experiment_results/your_experiment/indexed/tests.txt
uzi run "git diff --stat" > experiment_results/your_experiment/indexed/changes.txt
# Save best solution
uzi checkpoint best-agent "feat: index-based solution"
```

### Step 4: Reset and Run All-Complete
```bash
# Reset to baseline
git reset --hard $(cat experiment_results/your_experiment/baseline_commit.txt)
uzi kill all

# Start agents with full task
uzi prompt --agents claude:N "YOUR_COMPLETE_PROMPT"

# Collect individual results
for agent in $(uzi ls | grep -v AGENT | awk '{print $1}'); do
  mkdir -p experiment_results/your_experiment/all_complete/$agent
  cd ~/.local/share/uzi/worktrees/*$agent*/
  pytest --tb=no > experiment_results/your_experiment/all_complete/$agent/tests.txt
  git diff --stat > experiment_results/your_experiment/all_complete/$agent/changes.txt
done
```

### Step 5: Analyze Results
```bash
./compare_approaches.sh
```

## Example Results Format

```markdown
# Experiment: Fix All Failing Tests
Date: 2025-06-22
Agents: 4 Claude

## Index-Based Results
- Time: 25 minutes
- Tests Fixed: 18/24 (75%)
- Lines Changed: +245 -89
- Coverage: 78%
- Notes: Good separation, but integration test failed

## All-Complete Results  
- Time: 30 minutes
- Best Agent: emily
  - Tests Fixed: 22/24 (92%)
  - Lines Changed: +312 -124
  - Coverage: 85%
- Worst Agent: sam  
  - Tests Fixed: 15/24 (62%)
- Average: 19/24 (79%)

## Conclusion
All-Complete produced better individual results but took longer.
Best solution came from competitive approach.
```

## Tips for Fair Comparison

1. **Same Starting Point** - Always reset to same commit
2. **Same Time Limit** - Give both approaches equal time
3. **Same Agent Count** - Use same number of agents
4. **Same Model** - Use same AI model (e.g., all Claude)
5. **Clear Metrics** - Define success criteria upfront

## Which Approach to Use?

### Use Index-Based When:
- Task naturally divides into components
- Integration is straightforward
- Time is critical
- You want predictable results

### Use All-Complete When:
- Best quality is critical
- Multiple valid approaches exist
- You want to learn different solutions
- Integration is complex

## Advanced: Hybrid Approach

```bash
# Stage 1: All-Complete for exploration (2 agents)
uzi prompt --agents claude:2 "Explore solutions for VM snapshot feature"

# Analyze approaches
# Pick best approach

# Stage 2: Index-Based for implementation (4 agents)
uzi prompt --agents claude:4 "Implement VM snapshots using approach X:
Index 0: Core functions
Index 1: Tests
Index 2: Error handling
Index 3: Documentation"
```

## Automation Tools

- `compare_approaches.sh` - Analyze results
- `experiment_results/` - Store all results
- See guides for detailed examples:
  - [Index-Based Examples](UZI_EXPERIMENT_INDEX_BASED.md)
  - [All-Complete Examples](UZI_EXPERIMENT_ALL_COMPLETE.md)

## Share Your Results!

Document your experiments to help others learn which approach works best for different scenarios.