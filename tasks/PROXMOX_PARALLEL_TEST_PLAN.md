# ProxmoxMCP Parallel Test Implementation Plan

## Project-Specific Context

This plan implements parallel testing for ProxmoxMCP following the methodology in [PARALLEL_TESTING_GUIDE.md](./PARALLEL_TESTING_GUIDE.md).

### Current State

- **208 test methods** across 19 files
- **4,676 lines** of test code
- **Runtime**: ~25-35 seconds (sequential)
- **Excellent test isolation** already established

### Target State

- **Runtime**: ~6-10 seconds (70-80% improvement)
- **Zero test failures** from parallelization
- **Gate-level commit tracking** for implementation audit

## Package Manager Requirements

**IMPORTANT FOR AI AGENTS**: This project uses UV package manager.

### UV Requirements

- **DO NOT** use Poetry, pip, or pipenv commands
- **DO NOT** add Poetry-specific sections to pyproject.toml
- **ALWAYS** use `uv` commands for dependency management
- **ALWAYS** ensure `.venv` directory exists before running UV commands

### Virtual Environment Setup

```bash
# Create and activate virtual environment (REQUIRED)
uv venv
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate  # Windows

# Sync dependencies
uv sync --all-extras
```

## Implementation Scripts

All scripts are located in `docs/parallel-testing-scripts/`:

### Main Implementation Scripts (Run in Order)

1. `00_phase0_validate_dependencies.sh` - Install pytest-xdist, configure markers
2. `01_phase1_validate_test_categorization.sh` - Mark all 208 tests
3. `02_phase2_validate_thread_safety.sh` - Implement fixture isolation
4. `03_phase3_validate_performance.sh` - Measure and validate improvements
5. `99_e2e_validate_complete_implementation.sh` - Final validation

### Helper Scripts (Called by Main Scripts)

- `phase1_helper_add_test_markers.py` - Automated test marking
- `phase2_helper_validate_thread_safety.py` - Thread safety validation
- `phase3_helper_measure_performance.py` - Performance benchmarking
- `phase3_helper_optimize_parallel_config.py` - Worker optimization
- `phase3_helper_validate_parallel_execution.sh` - Result consistency check

## Phase-Specific Requirements

### Phase 0: Dependencies

Update `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    # ... existing dependencies ...
    "pytest-xdist>=3.0.0,<4.0.0",      # Parallel execution
    "pytest-benchmark>=4.0.0,<5.0.0",  # Performance monitoring
]

[tool.pytest.ini_options]
markers = [
    "unit: Fast unit tests safe for high parallelism (<100ms, single API call)",
    "integration: Multi-step workflow tests requiring limited parallelism",
    "slow: Tests taking >5 seconds or requiring special handling"
]
```

### Phase 1: Test Distribution Targets

- **Unit tests**: 180-190 (high parallelism, -n auto)
- **Integration tests**: 15-25 (limited parallelism, -n 2)
- **Slow tests**: 1-5 (sequential execution)

### Phase 2: ProxmoxMCP-Specific Thread Safety

Key areas requiring attention:

- `ProxmoxAPIMockBuilder` instances must be independent
- VM/Container IDs must be process-unique
- Mock fixture scope must be `function` level

### Phase 3: Performance Targets

- **Unit tests**: < 5 seconds
- **Full suite**: < 10 seconds
- **Minimum improvement**: 50% reduction

## Running the Implementation

### Option 1: Complete Implementation

```bash
cd docs/parallel-testing-scripts
./00_phase0_validate_dependencies.sh
./01_phase1_validate_test_categorization.sh
./02_phase2_validate_thread_safety.sh
./03_phase3_validate_performance.sh
./99_e2e_validate_complete_implementation.sh
```

### Option 2: Use Helper Scripts Directly

```bash
# After manual dependency installation
python phase1_helper_add_test_markers.py
python phase2_helper_validate_thread_safety.py
# etc.
```

## Progress Tracking

The implementation creates `.parallel_test_progress` file:

```
Phase 0 Gate 1: PASSED (commit: abc123)
Phase 0 Gate 2: PASSED (commit: def456)
...
```

## Rollback Plan

```bash
git checkout HEAD~1 pyproject.toml
git checkout HEAD~1 tests/conftest.py
git checkout HEAD~1 uv.lock
uv sync --all-extras
```

## Success Criteria

- [ ] All 4 phases complete with passing gates
- [ ] 50%+ performance improvement achieved
- [ ] All tests pass in parallel execution
- [ ] E2E validation script passes
- [ ] Gate-level commits provide clear audit trail
