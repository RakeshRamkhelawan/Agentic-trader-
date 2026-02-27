# Handover Patterns

Patterns for effective AI-to-AI context handovers.

## Core Principles

### 1. Primary Objective First
Always state the main goal clearly at the top.

```markdown
## Primary Objective
Implement V18 strategy with relaxed VedAstro filters to improve 
execute rate from 6.34% to 15-25%.
```

### 2. Context Hierarchy

```
1. What (Primary Objective)
2. What Was Done (Completed Work)
3. Where (Key Files)
4. Lessons (Reflections)
5. What's Next (Next Steps)
```

### 3. Specific File References
Always include full paths:

```markdown
## Key Files
- `backend/agents/elemental_agent_manager_v17.py` - Current agent
- `scripts/backtest_elemental_v17.py` - Backtest runner
- `V17_RESULTS_SUMMARY.md` - Results documentation
```

### 4. Environment State

```markdown
## Environment
- Python: 3.13.7
- Branch: main
- Docker: Running (api-server, postgres, redis)
- API Keys: Configured (Bitvavo, DeepSeek)
```

## Platform Differences

### Claude
- Prefers detailed technical context
- Handles long context well
- Good for complex reasoning

### Gemini
- Prefers concise, structured format
- Bullet points over paragraphs
- Good for quick summaries

### Kimi
- Prefers clear action items
- Step-by-step instructions
- Good for execution-focused tasks

## Template: New Feature

```markdown
## Primary Objective
Implement [FEATURE NAME]

## Background
[Why this feature is needed]

## Completed
- [x] Step 1
- [x] Step 2

## In Progress
- [ ] Step 3 (50% complete)

## Blockers
- [Issue description]

## Next Steps
1. Complete step 3
2. Test implementation
3. Update documentation

## Key Files
- `path/to/file.py`
- `path/to/config.yaml`
```

## Template: Bug Fix

```markdown
## Issue
[Brief description of bug]

## Root Cause
[What caused the bug]

## Fix Applied
[What was changed]

## Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [ ] E2E tests (pending)

## Files Modified
- `path/to/fixed_file.py`
- `path/to/test_file.py`

## Verification
```bash
# Run this to verify
python -m pytest tests/test_fix.py -v
```
```

## Template: Optimization

```markdown
## Optimization Target
[What is being optimized]

## Baseline Performance
- Metric: X
- Before: Y

## Changes Made
1. [Change 1]
2. [Change 2]

## Results
- Metric: X
- After: Z (N% improvement)

## Trade-offs
- [Pros]
- [Cons]
```

## Anti-Patterns

### ❌ Don't
- Vague descriptions ("fixed some stuff")
- Missing file paths
- Outdated information
- Assumed knowledge

### ✅ Do
- Specific commit hashes
- Full file paths
- Current timestamps
- Clear next actions
