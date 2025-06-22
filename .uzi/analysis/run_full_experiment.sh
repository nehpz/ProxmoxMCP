#!/bin/bash
# run_full_experiment.sh - Automates the complete experiment workflow

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ProxmoxMCP Uzi Experiment Runner ===${NC}"

# Check if task definition exists
if [ ! -f "experiment_results/task_definition.md" ]; then
    echo -e "${YELLOW}Please create experiment_results/task_definition.md first${NC}"
    exit 1
fi

# Function to wait for agents
wait_for_agents() {
    echo -e "${YELLOW}Waiting for agents to complete...${NC}"
    echo "Monitor with: uzi ls -w"
    echo "Press ENTER when agents are done"
    read
}

# 1. Save baseline
echo -e "${GREEN}1. Saving baseline state...${NC}"
mkdir -p experiment_results/{baseline,index_based,all_complete,analysis}
git rev-parse HEAD > experiment_results/baseline/commit.txt
pytest --tb=no | tee experiment_results/baseline/tests.txt
pytest --cov=proxmox_mcp --cov-report=term | tee experiment_results/baseline/coverage.txt

# 2. Run index-based
echo -e "${GREEN}2. Starting index-based experiment...${NC}"
cat << 'EOF'
Run this command:

uzi prompt --agents claude:3 \
"Read experiment_results/task_definition.md first.
Check pwd for your index (last number in path):
- Index 0: Implement core functions in vm.py
- Index 1: Create comprehensive tests
- Index 2: Add error handling and documentation
Work ONLY on your assigned part."
EOF

wait_for_agents

echo "Collecting index-based results..."
uzi run "pytest tests/test_vm_snapshots.py -v" > experiment_results/index_based/tests.txt 2>&1 || true
uzi run "git diff --stat" > experiment_results/index_based/changes.txt
uzi run "git log --oneline -10" > experiment_results/index_based/commits.txt
echo "Index-based experiment complete"

# 3. Reset and run all-complete
echo -e "${GREEN}3. Resetting for all-complete experiment...${NC}"
uzi kill all
git reset --hard $(cat experiment_results/baseline/commit.txt)

cat << 'EOF'
Run this command:

uzi prompt --agents claude:3 \
"Read experiment_results/task_definition.md.
Implement the COMPLETE VM snapshot feature.
Create your own full solution including all requirements."
EOF

wait_for_agents

echo "Collecting all-complete results..."
for agent in $(uzi ls | grep -v AGENT | awk '{print $1}'); do
  echo "Processing $agent..."
  mkdir -p experiment_results/all_complete/$agent

  # Find agent's worktree
  worktree=$(find ~/.local/share/uzi/worktrees -name "*-$agent-*" -type d | head -1)
  if [ -d "$worktree" ]; then
    cd "$worktree"
    pytest tests/test_vm_snapshots.py -v > "$OLDPWD/experiment_results/all_complete/$agent/tests.txt" 2>&1 || true
    git diff > "$OLDPWD/experiment_results/all_complete/$agent/implementation.diff"
    git diff --stat > "$OLDPWD/experiment_results/all_complete/$agent/stats.txt"
    cd "$OLDPWD"
  fi
done

# 4. Launch analysis
echo -e "${GREEN}4. Starting analysis agent...${NC}"
cat << 'EOF'
Run this command:

uzi prompt --agents claude:1 \
"You are the Analysis Agent. Analyze experiment results in experiment_results/
comparing Index-Based vs All-Complete approaches. Follow the analysis
framework in UZI_ANALYSIS_AGENT_GUIDE.md. Save your detailed report as
experiment_results/analysis/report.md"
EOF

wait_for_agents

echo -e "${GREEN}Experiment complete!${NC}"
echo "Check: experiment_results/analysis/report.md"

# 5. Generate summary
echo -e "${GREEN}5. Generating summary...${NC}"
cat > experiment_results/summary.txt << EOF
Experiment Summary
==================
Date: $(date)
Task: $(head -1 experiment_results/task_definition.md)

Index-Based Results:
$(grep -E "passed|failed" experiment_results/index_based/tests.txt | tail -1 || echo "No test results")

All-Complete Results:
EOF

for agent in experiment_results/all_complete/*/; do
  if [ -d "$agent" ]; then
    agent_name=$(basename "$agent")
    echo -n "$agent_name: "
    grep -E "passed|failed" "$agent/tests.txt" | tail -1 || echo "No test results"
  fi
done >> experiment_results/summary.txt

echo -e "\nAnalysis report available: experiment_results/analysis/report.md" >> experiment_results/summary.txt

cat experiment_results/summary.txt