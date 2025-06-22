#!/bin/bash
# Parallel execution consistency validation script

echo "=== Parallel Execution Validation ==="

# Test 1: Correctness - Parallel results match sequential
echo "🔍 Testing result consistency..."

TEMP_DIR=$(mktemp -d)
SEQ_RESULTS="$TEMP_DIR/sequential.txt"
PAR_RESULTS="$TEMP_DIR/parallel.txt"

# Run sequential tests
pytest tests/ --tb=no -v > "$SEQ_RESULTS" 2>&1
SEQ_EXIT=$?

# Run parallel tests  
pytest tests/ -n auto --tb=no -v > "$PAR_RESULTS" 2>&1
PAR_EXIT=$?

# Compare exit codes
if [ $SEQ_EXIT -eq $PAR_EXIT ]; then
    echo "✅ Exit codes match (sequential: $SEQ_EXIT, parallel: $PAR_EXIT)"
else
    echo "❌ Exit codes differ (sequential: $SEQ_EXIT, parallel: $PAR_EXIT)"
    exit 1
fi

# Compare test counts
SEQ_COUNT=$(grep -c "PASSED\|FAILED" "$SEQ_RESULTS")
PAR_COUNT=$(grep -c "PASSED\|FAILED" "$PAR_RESULTS")

if [ $SEQ_COUNT -eq $PAR_COUNT ]; then
    echo "✅ Test counts match ($SEQ_COUNT tests)"
else
    echo "❌ Test counts differ (sequential: $SEQ_COUNT, parallel: $PAR_COUNT)"
    exit 1
fi

# Test 2: Performance - Must be at least 50% faster
echo "🚀 Testing performance improvement..."

python3 tasks/parallel-testing-scripts/phase3_helper_measure_performance.py
PERF_EXIT=$?

if [ $PERF_EXIT -eq 0 ]; then
    # Check if best improvement meets threshold
    BEST_IMPROVEMENT=$(python3 -c "
import json
with open('performance_report.json', 'r') as f:
    report = json.load(f)
    
improvements = [analysis.get('percentage', 0) 
               for key, analysis in report['analysis'].items() 
               if key.startswith('improvement_')]
               
if improvements:
    print(max(improvements))
else:
    print(0)
")

    if (( $(echo "$BEST_IMPROVEMENT > 50" | bc -l) )); then
        echo "✅ Performance improvement: ${BEST_IMPROVEMENT}% (exceeds 50% threshold)"
    else
        echo "❌ Performance improvement: ${BEST_IMPROVEMENT}% (below 50% threshold)"
        exit 1
    fi
else
    echo "❌ Performance measurement failed"
    exit 1
fi

# Test 3: Category-specific performance
echo "📊 Testing category-specific execution..."

# Unit tests should run well with high parallelism
UNIT_TIME=$(pytest tests/ -m "unit" -n auto --tb=no -q 2>&1 | grep -o "[0-9.]*s" | tail -1 | sed 's/s//')
if (( $(echo "$UNIT_TIME < 5" | bc -l) )); then
    echo "✅ Unit tests complete in ${UNIT_TIME}s (under 5s threshold)"
else
    echo "⚠️  Unit tests took ${UNIT_TIME}s (over 5s threshold)"
fi

# Integration tests should still improve with limited parallelism  
INTEGRATION_SEQ=$(pytest tests/ -m "integration" --tb=no -q 2>&1 | grep -o "[0-9.]*s" | tail -1 | sed 's/s//')
INTEGRATION_PAR=$(pytest tests/ -m "integration" -n 2 --tb=no -q 2>&1 | grep -o "[0-9.]*s" | tail -1 | sed 's/s//')

if (( $(echo "$INTEGRATION_PAR < $INTEGRATION_SEQ" | bc -l) )); then
    echo "✅ Integration tests improved with limited parallelism"
else
    echo "⚠️  Integration tests not improved with parallelism"
fi

echo "🎉 Parallel execution validation complete"

# Clean up
rm -rf "$TEMP_DIR"