---
name: multi-ai-handover
description: Manage handover context between AI sessions (Claude, Gemini, Kimi) with automated context generation, status summaries, and project state tracking. Use when updating handover context, preparing for next AI session, summarizing project status, or transferring work between AI assistants. Triggers include "handover context", "update context", "next session", "AI handover", "Gemini summary", "Claude summary", "project status", "work summary", "session handover", "prepare for next AI".
---

# Multi-AI Handover Skill

Manage context handovers between AI sessions (Claude, Gemini, Kimi).

## Overview

When working across multiple AI sessions, maintain continuity with structured handover context.

## Supported Platforms

| Platform | Context File | Use Case |
|----------|--------------|----------|
| Claude | `.claude/context.md` | Claude Desktop/CLI |
| Gemini | `.gemini/context.md` | Gemini CLI |
| Kimi | `.kimi/context.md` | Kimi CLI |
| **Unified** | `HANDOVER_CONTEXT.md` | Cross-platform |

## Quick Start

### Update Handover Context

```bash
# Update with current changes
python .continue/skills/multi-ai-handover/scripts/handover_manager.py update

# Generate summary for specific platform
python .continue/skills/multi-ai-handover/scripts/handover_manager.py update --platform gemini

# Include git diff
python .continue/skills/multi-ai-handover/scripts/handover_manager.py update --with-diff
```

### Prepare for Next Session

```bash
# Generate comprehensive handover
python .continue/skills/multi-ai-handover/scripts/handover_manager.py prepare \
    --next-platform gemini \
    --focus "V18 strategy development" \
    --output handover_for_gemini.md

# Quick status summary
python .continue/skills/multi-ai-handover/scripts/handover_manager.py status
```

### Sync Across Platforms

```bash
# Sync to all platforms
python .continue/skills/multi-ai-handover/scripts/handover_manager.py sync

# Sync to specific platform
python .continue/skills/multi-ai-handover/scripts/handover_manager.py sync --to claude
```

## Handover Context Structure

The `HANDOVER_CONTEXT.md` includes:

```markdown
# Handover Context

## 1. Primary Objective
Current main goal (e.g., "V18 Strategy Development")

## 2. Completed Work
- Epic 10: Standardized Data Layer ✅
- Epic 11: Security Hardening ✅
- V17 Backtest: +6.96% return ✅

## 3. Key Files
- backend/agents/elemental_agent_manager_v17.py
- scripts/backtest_elemental_v17.py

## 4. Reflections
- What worked
- What didn't
- Lessons learned

## 5. Next Steps
- V18: Relax VedAstro filters
- Improve execute rate to 15-25%
```

## CLI Reference

```bash
# Update handover context
python scripts/handover_manager.py update \
    --platform all \
    --with-diff \
    --include-tests

# Generate platform-specific summary
python scripts/handover_manager.py prepare \
    --platform gemini \
    --focus "VedAstro integration" \
    --output gemini_handover.md

# Show current status
python scripts/handover_manager.py status \
    --show-epics \
    --show-versions

# Sync context files
python scripts/handover_manager.py sync \
    --from HANDOVER_CONTEXT.md \
    --to .claude/context.md

# Validate context
python scripts/handover_manager.py validate \
    --check-files \
    --check-completeness
```

## Platform-Specific Formats

### Claude Format
```markdown
# Context for Claude

## Current Focus
[Primary objective]

## What Was Done
[Bullet points]

## Important Files
[Key files]

## Continue With
[Next steps]
```

### Gemini Format
```markdownn# Context for Gemini

## Primary Objective
[Main goal]

## Completed Work
- [Epic/Feature]

## Key Files
- [File paths]

## Next Steps
- [Action items]
```

### Kimi Format
```markdown
# Context for Kimi

## 主目标 (Primary Objective)
[Goal]

## 已完成工作 (Completed Work)
[List]

## 关键文件 (Key Files)
[Paths]

## 下一步 (Next Steps)
[Actions]
```

## Automated Workflows

### Git Hook Integration

```bash
# Auto-update on commit
# .git/hooks/post-commit
python scripts/handover_manager.py update --quiet
```

### CI/CD Integration

```yaml
# .github/workflows/handover.yml
- name: Update Handover
  run: |
    python scripts/handover_manager.py update
    python scripts/handover_manager.py validate
```

## Status Dashboard

Generate comprehensive project status:

```bash
python scripts/handover_manager.py dashboard \
    --output status_report.md \
    --include-charts
```

Output includes:
- Epic completion status
- Version history
- Test results
- Security status
- Infrastructure health

## Best Practices

### 1. Update Regularly
- Update after significant changes
- Include before long breaks
- Sync before switching AIs

### 2. Be Specific
- Include file paths
- Mention specific errors
- Note environment details

### 3. Prioritize
- Primary objective first
- Completed work second
- Next steps third

### 4. Platform Awareness
- Claude: Detailed, technical
- Gemini: Concise, structured
- Kimi: Clear, actionable

## Integration with Other Skills

```bash
# After backtest, update context
python scripts/backtest_analyzer.py --latest
python scripts/handover_manager.py update --note "V17 backtest complete"

# After creating V18
python scripts/version_manager.py --create v18 --from v17
python scripts/handover_manager.py update --focus "V18 development"
```

## References

- `references/handover_patterns.md` - Handover templates
- `references/platform_formats.md` - Platform-specific formats
- `HANDOVER_CONTEXT.md` - Current handover file
