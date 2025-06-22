#!/bin/bash
# Phase 3: Performance Validation Script
# Measures and validates parallel execution performance

set -euo pipefail

echo "=== Phase 3: Performance Validation ==="
echo "Starting at: $(date)"

PROGRESS_FILE=".parallel_test_progress"

# Gate 1: Measure baseline performance
echo "⏱️  Gate 1: Measuring baseline performance..."

# Run performance measurement
python3 tasks/parallel-testing-scripts/phase3_helper_measure_performance.py
PERF_EXIT=$?

if [ $PERF_EXIT -eq 0 ]; then
    echo "✅ Performance measurement complete"
    echo "Phase 3 Gate 1: PASSED - Baseline measured (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
else
    echo "❌ Performance measurement failed"
    echo "Phase 3 Gate 1: FAILED - Measurement error (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    exit 1
fi

# Gate 2: Validate performance improvement
echo "📊 Gate 2: Validating performance improvement..."

# Check if we meet the 50% improvement target
IMPROVEMENT=$(python3 -c "
import json
with open('performance_report.json', 'r') as f:
    report = json.load(f)
    
best_improvement = 0
for key, analysis in report['analysis'].items():
    if key.startswith('improvement_'):
        improvement = analysis.get('percentage', 0)
        if improvement > best_improvement:
            best_improvement = improvement
            
print(int(best_improvement))
")

echo "Best performance improvement: ${IMPROVEMENT}%"

if [ "$IMPROVEMENT" -ge 50 ]; then
    echo "✅ Performance target met (${IMPROVEMENT}% > 50%)"
    echo "Phase 3 Gate 2: PASSED - ${IMPROVEMENT}% improvement (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
else
    echo "❌ Performance target not met (${IMPROVEMENT}% < 50%)"
    echo "Phase 3 Gate 2: FAILED - Only ${IMPROVEMENT}% improvement (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    exit 1
fi

# Gate 3: Optimize configuration
echo "🔧 Gate 3: Optimizing parallel configuration..."

# Run optimization
python3 tasks/parallel-testing-scripts/phase3_helper_optimize_parallel_config.py

if [ -f "parallel_optimization_results.json" ]; then
    echo "✅ Configuration optimization complete"
    echo "Phase 3 Gate 3: PASSED - Config optimized (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    
    # Show recommendations
    echo ""
    echo "Recommended configurations:"
    python3 -c "
import json
with open('parallel_optimization_results.json', 'r') as f:
    results = json.load(f)
    for purpose, cmd in results['recommendations']['pytest_commands'].items():
        print(f'  {purpose}: {cmd}')
    "
else
    echo "❌ Configuration optimization failed"
    echo "Phase 3 Gate 3: FAILED - No optimization (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    exit 1
fi

# Gate 4: Validate parallel execution consistency
echo "🔍 Gate 4: Validating execution consistency..."

# Run validation script
bash tasks/parallel-testing-scripts/phase3_helper_validate_parallel_execution.sh
CONSISTENCY_EXIT=$?

if [ $CONSISTENCY_EXIT -eq 0 ]; then
    echo "✅ Parallel execution is consistent"
    echo "Phase 3 Gate 4: PASSED - Consistent results (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
else
    echo "❌ Parallel execution inconsistency detected"
    echo "Phase 3 Gate 4: FAILED - Inconsistent results (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    exit 1
fi

# Final summary
echo ""
echo "=== Phase 3 Complete ==="
echo "✅ Performance improvement: ${IMPROVEMENT}%"
echo "✅ Optimal configuration determined"
echo "✅ Parallel execution validated"
echo ""
echo "Next step: Run ./99_e2e_validate_complete_implementation.sh for final validation"