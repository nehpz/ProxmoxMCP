# Complete Uzi Experiment Workflow

This document provides the complete workflow for running parallel development experiments with intelligent analysis.

## Overview

1. **Define Task** → 2. **Run Experiments** → 3. **Analyze Results** → 4. **Implement Optimal Solution**

## Step-by-Step Workflow

### Step 1: Prepare Task Definition
```bash
mkdir -p experiment_results
cat > experiment_results/task_definition.md << 'EOF'
# Task: [Your Task Name]

## Requirements
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

## Success Criteria
- [ ] All tests pass
- [ ] Coverage > X%
- [ ] Specific features work
- [ ] Error handling complete

## Constraints
- Time limit: X minutes
- Must integrate with existing code
- Follow project conventions
EOF
```

### Step 2: Run Experiments

#### Option A: Manual Execution
```bash
# Save baseline
./run_full_experiment.sh

# Follow prompts to run index-based experiment
# Follow prompts to run all-complete experiment
# Follow prompts to run analysis agent
```

#### Option B: Step-by-Step
```bash
# 1. Baseline
pytest --tb=no > experiment_results/baseline/tests.txt

# 2. Index-Based (specialized roles)
uzi prompt --agents claude:3 "[Index-based prompt]"
# Wait for completion
# Collect results

# 3. Reset and All-Complete  
git reset --hard && uzi kill all
uzi prompt --agents claude:3 "[All-complete prompt]"
# Wait and collect

# 4. Analysis Agent
uzi prompt --agents claude:1 "[Analysis prompt]"
```

### Step 3: Review Analysis

The analysis agent creates `experiment_results/analysis/report.md` with:
- Quality scores for each approach
- Alignment with requirements
- Cherry-picking opportunities
- Integration assessment
- Clear winner and rationale

### Step 4: Implement Recommendations

Based on analysis, either:

#### A. Cherry-Pick (if all-complete won)
```bash
# Analysis provides specific commits to combine
git checkout best-base-branch
git cherry-pick emily-error-handling-commit
git cherry-pick adam-tests-commit
pytest  # Verify combination works
```

#### B. Integrate (if index-based won)
```bash
# Fix integration issues identified
# Implement glue code between modules
# Run integration tests
```

#### C. Hybrid Approach
Sometimes analysis suggests using index-based findings to improve all-complete solution or vice versa.

## Example: VM Snapshot Feature

### 1. Task Definition
```markdown
# Task: Implement VM Snapshot Feature

## Requirements
1. CRUD operations for VM snapshots
2. Error handling for edge cases
3. 90%+ test coverage
4. Integration with existing VM tool

## Success Criteria
- [ ] All snapshot operations work
- [ ] Tests pass
- [ ] Clean API design
- [ ] Proper documentation
```

### 2. Run Experiments
```bash
# Index-based: 0=core, 1=tests, 2=errors
# All-complete: everyone does everything
./run_full_experiment.sh
```

### 3. Analysis Results
```markdown
Winner: All-Complete with Cherry-Picking
- Emily: Best error handling
- Adam: Cleanest core implementation  
- Sam: Most thorough tests

Cherry-pick plan provided...
```

### 4. Final Implementation
Combined best parts → 10/10 quality (better than any individual)

## Tips for Success

1. **Clear Task Definition**: The better defined, the better the results
2. **Equal Time**: Give both approaches same time limit
3. **Let Agents Work**: Don't interrupt or guide during experiments
4. **Trust Analysis**: The AI agent often finds non-obvious optimizations
5. **Document Results**: Save everything for future reference

## Automation Tools

- `run_full_experiment.sh` - Orchestrates entire workflow
- `compare_approaches.sh` - Basic metrics comparison
- Analysis Agent - Intelligent evaluation and recommendations

## Decision Tree

```
Is task clearly divisible?
├─ Yes → Try index-based first
│   └─ Did parts integrate well?
│       ├─ Yes → Index-based wins
│       └─ No → Try all-complete
└─ No → Try all-complete first
    └─ Multiple good solutions?
        ├─ Yes → Cherry-pick optimal
        └─ No → Use best complete

Always: Run analysis agent for insights
```

## Further Reading

- [Index-Based Examples](UZI_EXPERIMENT_INDEX_BASED.md)
- [All-Complete Examples](UZI_EXPERIMENT_ALL_COMPLETE.md)
- [Analysis Agent Guide](UZI_ANALYSIS_AGENT_GUIDE.md)
- [Why Analysis Matters](ANALYSIS_AGENT_EXPLAINED.md)

Remember: The goal isn't just to complete the task, but to discover the optimal approach and implementation through parallel experimentation and intelligent analysis.