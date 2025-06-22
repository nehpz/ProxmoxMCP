#!/bin/bash
# Phase 0: Dependencies & Configuration Validation Script
# Installs pytest-xdist and validates parallel testing setup

set -euo pipefail

echo "=== Phase 0: Dependencies & Configuration Validation ==="
echo "Starting at: $(date)"

# Check for .venv directory
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run 'uv venv' first."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "❌ Virtual environment not activated. Please activate it first."
    exit 1
fi

# Progress tracking file
PROGRESS_FILE=".parallel_test_progress"

# Gate 1: Install pytest-xdist
echo "🔧 Gate 1: Installing pytest-xdist..."

# Update pyproject.toml with pytest-xdist
if ! grep -q "pytest-xdist" pyproject.toml; then
    echo "Adding pytest-xdist to pyproject.toml..."
    # This is a placeholder - in real implementation, you'd properly edit the TOML
    echo "⚠️  Please manually add to pyproject.toml under [project.optional-dependencies] dev section:"
    echo '    "pytest-xdist>=3.0.0,<4.0.0",      # Parallel execution'
    echo '    "pytest-benchmark>=4.0.0,<5.0.0",  # Performance monitoring'
    echo ""
    echo "Then run: uv sync --all-extras"
    echo "Press Enter when complete..."
    read -r
fi

# Install dependencies using UV
echo "Installing dependencies with UV..."
uv sync --all-extras

# Verify installation
if python -c "import pytest_xdist" 2>/dev/null; then
    echo "✅ pytest-xdist installed successfully"
    echo "Phase 0 Gate 1: PASSED (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    git add pyproject.toml uv.lock 2>/dev/null || true
    git commit -m "feat: Add pytest-xdist dependency for parallel testing" 2>/dev/null || true
else
    echo "❌ pytest-xdist installation failed"
    echo "Phase 0 Gate 1: FAILED (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    exit 1
fi

# Gate 2: Configure pytest markers
echo "🔧 Gate 2: Configuring pytest markers..."

# Check if markers already exist in pyproject.toml
if ! grep -q "markers =" pyproject.toml; then
    echo "⚠️  Please add the following to pyproject.toml under [tool.pytest.ini_options]:"
    echo 'markers = ['
    echo '    "unit: Fast unit tests safe for high parallelism (<100ms, single API call)",'
    echo '    "integration: Multi-step workflow tests requiring limited parallelism",'
    echo '    "slow: Tests taking >5 seconds or requiring special handling"'
    echo ']'
    echo ""
    echo "Press Enter when complete..."
    read -r
fi

# Verify markers are configured
if python -c "
import subprocess
result = subprocess.run(['pytest', '--markers'], capture_output=True, text=True)
markers = ['unit:', 'integration:', 'slow:']
if all(marker in result.stdout for marker in markers):
    exit(0)
else:
    exit(1)
" 2>/dev/null; then
    echo "✅ Pytest markers configured successfully"
    echo "Phase 0 Gate 2: PASSED (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    git add pyproject.toml 2>/dev/null || true
    git commit -m "feat: Configure pytest markers for test categorization" 2>/dev/null || true
else
    echo "❌ Pytest markers configuration failed"
    echo "Phase 0 Gate 2: FAILED (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    exit 1
fi

# Gate 3: Validate pytest-xdist plugin detection
echo "🔧 Gate 3: Validating pytest-xdist plugin..."

if pytest --version 2>&1 | grep -q "pytest-xdist"; then
    echo "✅ pytest-xdist plugin detected"
    echo "Phase 0 Gate 3: PASSED (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
else
    echo "❌ pytest-xdist plugin not detected"
    echo "Phase 0 Gate 3: FAILED (commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git'))" >> "$PROGRESS_FILE"
    exit 1
fi

# Final summary
echo ""
echo "=== Phase 0 Complete ==="
echo "✅ All dependencies installed and configured"
echo "✅ Ready for Phase 1: Test Categorization"
echo ""
echo "Next step: Run ./01_phase1_validate_test_categorization.sh"