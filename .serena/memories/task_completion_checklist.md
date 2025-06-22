# Task Completion Checklist

When completing a coding task in ProxmoxMCP, always ensure you:

## 1. Code Quality Checks
- [ ] Run Black formatter: `black .`
- [ ] Run Ruff linter: `ruff .`
- [ ] Run mypy type checker: `mypy .`
- [ ] Fix any issues reported by the above tools

## 2. Testing
- [ ] Run all tests: `pytest`
- [ ] Ensure all tests pass
- [ ] Add new tests for new functionality
- [ ] Update existing tests if behavior changed

## 3. Documentation
- [ ] Update docstrings for new/modified functions
- [ ] Include type hints for all parameters and returns
- [ ] Update module docstrings if scope changed
- [ ] Add inline comments for complex logic (if needed)

## 4. Code Review
- [ ] Check that code follows project conventions
- [ ] Verify error handling is appropriate
- [ ] Ensure logging is used correctly
- [ ] Validate that formatting templates are used for output

## 5. Testing Guidelines
- [ ] Each test has single responsibility
- [ ] Test classes are focused on specific operations
- [ ] Mock external dependencies (Proxmox API)
- [ ] Use descriptive test names
- [ ] Follow SOLID principles in test design

## 6. Final Verification
- [ ] Code runs without errors
- [ ] No hardcoded values or secrets
- [ ] No commented-out code left
- [ ] Changes are focused and don't break existing functionality

## Quick Command Sequence
```bash
# Run all checks in order
black .
ruff . 
mypy .
pytest
```

If all checks pass, the task is ready for review/commit.