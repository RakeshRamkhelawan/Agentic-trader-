# Versioning Strategy

## Git Tags vs Filename Versioning

### ❌ Old Approach (Deprecated)
Previously, the codebase used filename versioning like:
```
elemental_agent_manager_v2.py
elemental_agent_manager_v3.py
...
elemental_agent_manager_v17.py
```

**Problems:**
- Import confusion (which version is active?)
- Search pollution (grep finds multiple versions)
- Codebase bloat (15+ versions of same file)
- No clear history of changes

### ✅ New Approach (Git Tags)
Now using **Git tags** for versioning:
```
git tag -a v17.0 -m "Version 17.0: Data Pre-fetch Agent + Live Paper Trading"
```

**Benefits:**
- Single source of truth (one file per module)
- Clear version history via git log
- Easy rollback to any version
- Clean imports (no version numbers in filenames)
- Archive folder for old versions (if needed for reference)

## How to Create a New Version

```bash
# 1. Commit all changes
git add .
git commit -m "Your changes description"

# 2. Create annotated tag
git tag -a v18.0 -m "Version 18.0: Description of changes"

# 3. Push tag to remote
git push origin v18.0
```

## How to View Version History

```bash
# List all tags
git tag -l

# Show tag details
git show v17.0

# Compare versions
git diff v16.0 v17.0

# Checkout specific version
git checkout v17.0
```

## Archive Folder

Old versions (v2-v15) are stored in:
```
backend/agents/archive/
```

These are kept for reference only. Do not import from archive.

## Current Active Versions

| Module | Current Version | File |
|--------|----------------|------|
| Elemental Agent Manager | v17.0 | `backend/agents/elemental_agent_manager.py` |
| Trading Agents | v2.0 | `backend/services/trading_agents_v2.py` |
| Real Paper Trading | v2.0 | `backend/services/real_paper_trading_v2.py` |

## When to Create a Tag

Create a new tag when:
1. Major feature is complete
2. Bug fix is verified in production
3. Release is ready for deployment
4. Breaking changes are introduced

## Best Practices

1. **Use semantic versioning**: `vMAJOR.MINOR.PATCH`
   - MAJOR: Breaking changes
   - MINOR: New features (backward compatible)
   - PATCH: Bug fixes

2. **Write descriptive tag messages**: Explain what changed

3. **Don't commit versioned filenames**: Use Git tags instead

4. **Clean up regularly**: Archive old versions, delete obsolete code
