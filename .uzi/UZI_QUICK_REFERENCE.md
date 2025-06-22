# Using Uzi with ProxmoxMCP - Quick Reference

## Setup Complete ✅
- `uzi.yaml` configured for Python development
- Virtual environments auto-created for each agent
- All dependencies auto-installed

## Two Experimental Approaches + Analysis Agent

### 1. Index-Based Division (Specialized Roles)
Each agent works on a different part:
```bash
uzi prompt --agents claude:4 \
"Check pwd for your index. 
0=VM ops, 1=Container ops, 2=Console ops, 3=Tests
Work ONLY on your assigned module."
```

### 2. All-Complete (Competitive Solutions)
All agents do the entire task:
```bash
uzi prompt --agents claude:4 \
"Fix ALL failing tests in ProxmoxMCP. 
Create the best complete solution you can."
```

### 3. Analysis Agent (NEW!) 🤖
AI agent analyzes results and finds optimal combinations:
```bash
uzi prompt --agents claude:1 \
"Analyze experiment results in experiment_results/
Follow UZI_ANALYSIS_AGENT_GUIDE.md"
```

## Complete Experiment Workflow

```bash
# 1. Define task
cat > experiment_results/task_definition.md << EOF
# Task: [Your task here]
## Requirements: ...
## Success Criteria: ...
EOF

# 2. Run automated experiment
./run_full_experiment.sh

# 3. Read analysis
cat experiment_results/analysis/report.md

# 4. Implement optimal solution
# Based on analysis recommendations
```

## Key Files
- **[UZI_EXPERIMENT_INDEX_BASED.md](UZI_EXPERIMENT_INDEX_BASED.md)** - Index-based examples
- **[UZI_EXPERIMENT_ALL_COMPLETE.md](UZI_EXPERIMENT_ALL_COMPLETE.md)** - All-complete examples  
- **[UZI_ANALYSIS_AGENT_GUIDE.md](UZI_ANALYSIS_AGENT_GUIDE.md)** - Analysis agent framework
- **[ANALYSIS_AGENT_EXPLAINED.md](ANALYSIS_AGENT_EXPLAINED.md)** - Why AI analysis matters
- **[COMPLETE_UZI_EXPERIMENT_WORKFLOW.md](COMPLETE_UZI_EXPERIMENT_WORKFLOW.md)** - Full workflow
- **`run_full_experiment.sh`** - Automated experiment runner

## Quick Commands

```bash
# Start experiment
uzi prompt --agents claude:N "Your task here"

# Monitor progress
uzi ls -w

# Check individual agent
cd ~/.local/share/uzi/worktrees/*agentname*/
git diff

# Save good work
uzi checkpoint agentname "description"

# Compare results
./compare_approaches.sh

# Clean up
uzi kill all
```

## Full Experiment Guide
See [UZI_EXPERIMENT_GUIDE.md](UZI_EXPERIMENT_GUIDE.md) for detailed comparison methodology.

## Key Discovery: Agent Indexing
Agents are numbered 0,1,2,3... in their worktree paths!
- `alexandra-claude-project-hash-timestamp-0`
- `brian-claude-project-hash-timestamp-1`  
- `claire-claude-project-hash-timestamp-2`

Use this for automatic work assignment!