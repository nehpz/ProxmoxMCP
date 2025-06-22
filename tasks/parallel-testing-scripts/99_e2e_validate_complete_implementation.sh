#!/bin/bash
# E2E Validation Script
# Runs all phases sequentially to validate complete implementation

set -euo pipefail

echo "=== E2E Parallel Testing Implementation Validation ==="
echo "Starting at: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0

# Function to run a phase
run_phase() {
    local phase_num=$1
    local phase_script=$2
    local phase_name=$3
    
    echo -e "${YELLOW}Running Phase $phase_num: $phase_name${NC}"
    echo "=" * 50
    
    if [ -f "$phase_script" ]; then
        if bash "$phase_script"; then
            echo -e "${GREEN}✅ Phase $phase_num: PASSED${NC}"
        else
            echo -e "${RED}❌ Phase $phase_num: FAILED${NC}"
            OVERALL_STATUS=1
            return 1
        fi
    else
        echo -e "${RED}❌ Phase $phase_num script not found: $phase_script${NC}"
        OVERALL_STATUS=1
        return 1
    fi
    
    echo ""
    return 0
}

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Clean previous progress file for fresh run
if [ -f ".parallel_test_progress" ]; then
    echo "Backing up previous progress..."
    mv .parallel_test_progress ".parallel_test_progress.bak.$(date +%Y%m%d_%H%M%S)"
fi

# Run all phases
echo "Starting complete validation..."
echo ""

# Phase 0: Dependencies
if ! run_phase 0 "tasks/parallel-testing-scripts/00_phase0_validate_dependencies.sh" "Dependencies & Configuration"; then
    echo "Stopping due to Phase 0 failure"
    exit 1
fi

# Phase 1: Test Categorization  
if ! run_phase 1 "tasks/parallel-testing-scripts/01_phase1_validate_test_categorization.sh" "Test Categorization"; then
    echo "Stopping due to Phase 1 failure"
    exit 1
fi

# Phase 2: Thread Safety
if ! run_phase 2 "tasks/parallel-testing-scripts/02_phase2_validate_thread_safety.sh" "Thread Safety Implementation"; then
    echo "Stopping due to Phase 2 failure"
    exit 1
fi

# Phase 3: Performance
if ! run_phase 3 "tasks/parallel-testing-scripts/03_phase3_validate_performance.sh" "Performance Validation"; then
    echo "Stopping due to Phase 3 failure"
    exit 1
fi

# Final validation summary
echo "=== E2E Validation Summary ==="
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL PHASES PASSED${NC}"
    echo ""
    echo "Implementation complete! You can now use parallel testing:"
    echo "  - Fast feedback: pytest -m 'unit' -n auto"
    echo "  - Full suite: pytest -n auto"
    echo "  - CI/CD ready: See parallel_optimization_results.json"
    
    # Show performance summary if available
    if [ -f "performance_report.json" ]; then
        echo ""
        echo "Performance Summary:"
        python3 -c "
import json
with open('performance_report.json', 'r') as f:
    report = json.load(f)
    baseline = report['baseline']['duration']
    for key, result in report['parallel'].items():
        if result['exit_code'] == 0:
            improvement = report['analysis'].get(f'improvement_{key}', {}).get('percentage', 0)
            print(f'  {key} workers: {improvement:.1f}% faster')
        "
    fi
else
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo ""
    echo "Check .parallel_test_progress for details on failures"
    echo "Review individual phase outputs above"
fi

echo ""
echo "Completed at: $(date)"

exit $OVERALL_STATUS