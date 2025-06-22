#!/bin/bash
# Phase 1: Test Categorization Validation Script
# Ensures all 208 tests are properly marked for parallel execution

set -euo pipefail

echo "=== Phase 1: Test Categorization Validation ==="
echo "Starting at: $(date)"

PROGRESS_FILE=".parallel_test_progress"

# Gate 1: Count total test methods
echo "🔍 Gate 1: Counting test methods..."

TOTAL_TESTS=$(python3 -c "
import ast
import pathlib

count = 0
for test_file in pathlib.Path('tests').rglob('test_*.py'):
    with open(test_file, 'r') as f:
        tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith('test_'):
                count += 1
print(count)
")

echo "Found $TOTAL_TESTS test methods"

if [ "$TOTAL_TESTS" -ge 200 ]; then
    echo "✅ Test count validated: $TOTAL_TESTS tests"
    echo "Phase 1 Gate 1: PASSED - Found $TOTAL_TESTS tests (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
else
    echo "❌ Expected ~208 tests, found only $TOTAL_TESTS"
    echo "Phase 1 Gate 1: FAILED - Only $TOTAL_TESTS tests found (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    exit 1
fi

# Gate 2: Add test markers
echo "🏷️  Gate 2: Adding test markers..."

# Run the helper script to add markers
python3 tasks/parallel-testing-scripts/phase1_helper_add_test_markers.py

# Commit the changes
git add tests/ 2>/dev/null || true
if git diff --staged --quiet 2>/dev/null; then
    echo "No changes to commit (markers may already exist)"
else
    git commit -m "feat: Add pytest markers to all test methods" 2>/dev/null || true
    echo "Phase 1 Gate 2: PASSED - Markers added (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
fi

# Gate 3: Validate marker distribution
echo "📊 Gate 3: Validating marker distribution..."

# Count tests by marker
UNIT_COUNT=$(pytest --collect-only -m "unit" -q 2>/dev/null | grep -c "<AsyncFunction" || echo "0")
INTEGRATION_COUNT=$(pytest --collect-only -m "integration" -q 2>/dev/null | grep -c "<AsyncFunction" || echo "0")
SLOW_COUNT=$(pytest --collect-only -m "slow" -q 2>/dev/null | grep -c "<AsyncFunction" || echo "0")

echo "Test distribution:"
echo "  Unit tests: $UNIT_COUNT"
echo "  Integration tests: $INTEGRATION_COUNT"
echo "  Slow tests: $SLOW_COUNT"
echo "  Total marked: $((UNIT_COUNT + INTEGRATION_COUNT + SLOW_COUNT))"

# Validate distribution
if [ "$UNIT_COUNT" -ge 150 ] && [ "$UNIT_COUNT" -le 190 ]; then
    echo "✅ Unit test count in expected range (150-190)"
    echo "Phase 1 Gate 3: PASSED - Good distribution (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
else
    echo "⚠️  Unit test count ($UNIT_COUNT) outside expected range (150-190)"
    echo "Phase 1 Gate 3: WARNING - Distribution suboptimal (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
fi

# Gate 4: Verify all tests are marked
echo "✅ Gate 4: Verifying all tests are marked..."

MARKED_TOTAL=$((UNIT_COUNT + INTEGRATION_COUNT + SLOW_COUNT))
if [ "$MARKED_TOTAL" -eq "$TOTAL_TESTS" ]; then
    echo "✅ All $TOTAL_TESTS tests are properly marked"
    echo "Phase 1 Gate 4: PASSED - All tests marked (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
else
    echo "❌ Marked tests ($MARKED_TOTAL) doesn't match total tests ($TOTAL_TESTS)"
    echo "Phase 1 Gate 4: FAILED - Missing markers (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    exit 1
fi

# Final summary
echo ""
echo "=== Phase 1 Complete ==="
echo "✅ All $TOTAL_TESTS tests are categorized"
echo "✅ Distribution: $UNIT_COUNT unit, $INTEGRATION_COUNT integration, $SLOW_COUNT slow"
echo ""
echo "Next step: Run ./02_phase2_validate_thread_safety.sh"