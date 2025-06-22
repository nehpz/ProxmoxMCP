# ProxmoxMCP Uzi Analysis Agent Guide

This guide is for an AI agent tasked with analyzing and comparing results from parallel development experiments.

## Analysis Agent Prompt

```bash
# Start a dedicated analysis agent after experiments complete
uzi prompt --agents claude:1 \
"You are the Analysis Agent for ProxmoxMCP parallel development experiments. Your task is to analyze results from two approaches: Index-Based (divided work) and All-Complete (everyone does everything).

Your analysis should cover:

1. **Implementation Quality Assessment**
   - Review code changes in experiment_results/ directories
   - Check each agent's work in ~/.local/share/uzi/worktrees/
   - Evaluate: Does the implementation match the requirements?
   - Rate code quality, error handling, test coverage
   - Identify any missing features or edge cases

2. **Alignment to Expectations**
   - Original task: [INSERT ORIGINAL TASK HERE]
   - Expected outcomes: [INSERT EXPECTATIONS HERE]
   - For each approach, rate how well the result meets expectations (1-10)
   - Document any deviations or unexpected innovations

3. **Cherry-Picking Analysis** (All-Complete Only)
   - Identify the BEST parts from each agent's solution
   - Propose optimal combinations (e.g., Emily's error handling + Adam's core logic + Sam's tests)
   - Create a cherry-picking plan with specific git commits
   - Estimate effort to integrate the best parts

4. **Integration Assessment** (Index-Based Only)
   - Check if the divided parts work together properly
   - Run integration tests
   - Identify any gaps between modules
   - Rate integration success (1-10)

5. **Comprehensive Comparison**
   - Which approach produced better results for THIS specific task?
   - Time efficiency vs quality trade-offs
   - Maintainability of resulting code
   - Recommendations for future tasks

Please start by examining the experiment_results/ directory, then investigate each agent's worktree. Provide a detailed analysis report."
```

## Structured Analysis Report Template

```markdown
# ProxmoxMCP Parallel Development Analysis Report

## Task Overview
- **Original Task**: [Brief description]
- **Date**: [Date]
- **Approaches Tested**: Index-Based (N agents) vs All-Complete (N agents)

## 1. Implementation Quality Assessment

### Index-Based Approach
| Agent | Index | Module | Quality | Tests | Coverage | Notes |
|-------|-------|--------|---------|-------|----------|-------|
| alex  | 0     | VM     | 8/10    | 12    | 85%      | Good error handling |
| brian | 1     | Container | 6/10 | 8     | 70%      | Missing edge cases |

**Overall Quality**: 7/10
**Strengths**: Clear separation, focused implementations
**Weaknesses**: Integration gaps between modules

### All-Complete Approach  
| Agent | Tests Passed | Quality | Innovation | Cherry-Pick Value |
|-------|--------------|---------|------------|-------------------|
| emily | 48/50        | 9/10    | High       | Error handling, logging |
| adam  | 50/50        | 8/10    | Medium     | Core algorithm |
| sam   | 45/50        | 7/10    | Low        | Test structure |

**Best Complete Solution**: adam (50/50 tests, clean implementation)

## 2. Alignment to Expectations

### Original Requirements
- ✅ Requirement 1: [Met/Not Met]
- ⚠️  Requirement 2: [Partially Met - explanation]
- ❌ Requirement 3: [Not Met - explanation]

### Index-Based Alignment: 7/10
- Each module well-implemented in isolation
- Integration requirements partially met
- Missing: [specific gaps]

### All-Complete Alignment: 9/10  
- Best agent (adam) meets all requirements
- Multiple valid approaches discovered
- Bonus: emily found elegant solution for [X]

## 3. Cherry-Picking Opportunities (All-Complete)

### Optimal Combination Identified
```bash
# Base: Adam's core implementation
git checkout adam-branch

# Cherry-pick Emily's error handling
git cherry-pick emily-commit-hash-1
git cherry-pick emily-commit-hash-2

# Cherry-pick Sam's comprehensive test suite  
git cherry-pick sam-commit-hash-3

# Result: Best of all worlds
```

### Integration Effort
- Estimated time: 30 minutes
- Conflicts expected: Minimal (different files)
- Result quality: 10/10 (better than any individual)

## 4. Integration Assessment (Index-Based)

### Integration Test Results
```
pytest tests/integration/ -v
Result: 3 passed, 2 failed
```

### Gap Analysis
- Module A ← → Module B: Missing interface for [X]
- Module B ← → Module C: Incompatible error types
- Fix effort: 2 hours estimated

## 5. Recommendations

### For This Task Type (Feature Implementation)
**Winner: All-Complete with Cherry-Picking**
- Reason: Complex feature benefited from multiple approaches
- Cherry-picked solution superior to any individual effort
- Time penalty (20% slower) worth the quality gain

### Decision Framework
Use **Index-Based** when:
- [ ] Clear module boundaries exist
- [ ] Integration is well-defined
- [ ] Time is critical
- [ ] Team has specialized expertise

Use **All-Complete** when:
- [X] Multiple valid solutions possible
- [X] Quality is paramount
- [X] Integration is complex
- [X] Want to discover best practices

### Future Improvements
1. Hybrid approach: All-Complete for design, Index-Based for implementation
2. Pair agents on complex modules
3. Add integration agent for Index-Based approach

## 6. Detailed Code Analysis

### Best Practices Discovered
- Emily's error handling pattern:
  ```python
  # Excellent pattern found in emily's solution
  try:
      result = await self._api_call(...)
  except ProxmoxAPIError as e:
      logger.error(f"API call failed: {e}", extra={"vm_id": vm_id})
      raise VMOperationError(f"Failed to {operation}: {e}") from e
  ```

### Anti-patterns to Avoid
- Sam's issue: Overly complex test fixtures
- Brian's issue: Tight coupling between modules

## 7. Metrics Summary

| Metric | Index-Based | All-Complete | Winner |
|--------|-------------|--------------|---------|
| Time | 25 min | 30 min | Index |
| Quality | 7/10 | 9/10 | Complete |
| Tests | 45/50 | 50/50 | Complete |
| Coverage | 78% | 85% | Complete |
| Maintainability | 8/10 | 9/10 | Complete |
| Integration | 6/10 | N/A | - |

## Final Recommendation
For this task: **All-Complete with Cherry-Picking**
```

## Analysis Agent Tools

The analysis agent should have access to:

```bash
# 1. View experiment structure
find experiment_results -type f -name "*.txt" | sort

# 2. Compare implementations
for agent in $(ls ~/.local/share/uzi/worktrees/); do
  echo "=== Agent: $agent ==="
  cd ~/.local/share/uzi/worktrees/$agent
  git log --oneline -5
  git diff --stat
done

# 3. Run integration tests
cd ~/.local/share/uzi/worktrees/[agent]/
pytest tests/integration/ -v

# 4. Generate diffs between solutions
diff -u <(cd worktree1 && git show) <(cd worktree2 && git show)

# 5. Test cherry-pick combinations
git checkout -b analysis-branch
git cherry-pick --no-commit commit1
git cherry-pick --no-commit commit2
pytest
```

## Starting the Analysis

```bash
# After running both experiments
# Start analysis agent with context
uzi prompt --agents claude:1 \
"You are analyzing ProxmoxMCP experiment results. 
Task was: 'Implement VM snapshot feature'
Expected: Working create/list/delete/rollback with tests
Index-Based: 4 agents divided work
All-Complete: 4 agents each did everything
Analyze per the framework in UZI_ANALYSIS_AGENT_GUIDE.md"

# Agent will produce comprehensive analysis
# Save the analysis
uzi checkpoint analysis-agent "experiment analysis: VM snapshots"
```

## Advanced Analysis Patterns

### 1. Multi-Stage Analysis
```bash
# Stage 1: Quick assessment
"First, do a quick pass to identify obviously best solutions"

# Stage 2: Deep dive
"Now examine the top 2 solutions in detail"

# Stage 3: Integration planning
"Create a detailed plan to combine the best elements"
```

### 2. Comparative Code Review
```bash
# Have agent compare specific implementations
"Compare how each agent implemented error handling in create_snapshot()"
```

### 3. Test Suite Analysis
```bash
# Evaluate test quality, not just quantity
"Which agent wrote the most maintainable tests? Consider clarity, coverage, and edge cases"
```

This analysis agent approach provides the intelligent evaluation that scripts cannot achieve!