#!/usr/bin/env python3
"""
Multi-AI Handover Manager - Manage context between AI sessions.

Usage:
    python handover_manager.py update
    python handover_manager.py prepare --platform gemini
    python handover_manager.py status
    python handover_manager.py sync --to claude
"""

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_git_changes(since: str = "HEAD~5") -> list[dict]:
    """Get recent git changes."""
    try:
        result = subprocess.run(
            ['git', 'log', since, '--oneline', '--name-status'],
            capture_output=True,
            text=True
        )

        changes = []
        current_commit = None

        for line in result.stdout.split('\n'):
            if not line.strip():
                continue

            # Commit hash line
            if ' ' in line and len(line.split()[0]) == 7:
                current_commit = {
                    'hash': line.split()[0],
                    'message': ' '.join(line.split()[1:]),
                    'files': []
                }
                changes.append(current_commit)
            # File change line
            elif current_commit and line[0] in 'AMD':
                current_commit['files'].append({
                    'status': line[0],
                    'path': line[2:].strip()
                })

        return changes
    except Exception as e:
        return [{'error': str(e)}]


def get_current_branch() -> str:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except:
        return 'unknown'


def get_modified_files() -> list[str]:
    """Get list of modified files."""
    try:
        result = subprocess.run(
            ['git', 'status', '--short'],
            capture_output=True,
            text=True
        )
        files = []
        for line in result.stdout.split('\n'):
            if line.strip():
                files.append(line[3:].strip())
        return files
    except:
        return []


def parse_existing_handover() -> dict:
    """Parse existing HANDOVER_CONTEXT.md."""
    filepath = Path('HANDOVER_CONTEXT.md')

    if not filepath.exists():
        return {}

    with open(filepath, 'r') as f:
        content = f.read()

    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section] = '\n'.join(current_content)

    return sections


def detect_epic_status() -> list[dict]:
    """Detect epic completion status from files."""
    epics = []

    # Check for epic markers in files
    epic_markers = [
        ('Epic 10', 'backend/data/repository.py', 'Standardized Data'),
        ('Epic 11', 'backend/governance/agent_gatekeeper.py', 'Security Hardening'),
        ('Epic 12', 'backend/core/telemetry', 'Production Monitoring'),
        ('Epic 13', 'backend/scripts/ops', 'Cleanup'),
    ]

    for epic_name, marker_file, description in epic_markers:
        exists = Path(marker_file).exists()
        epics.append({
            'name': epic_name,
            'description': description,
            'status': '[DONE]' if exists else '[PENDING]',
            'marker': marker_file
        })

    return epics


def detect_strategy_versions() -> list[dict]:
    """Detect strategy versions in repo."""
    versions = []

    for ver in ['v13', 'v14', 'v15', 'v16', 'v17', 'v18']:
        agent_file = Path(f'backend/agents/elemental_agent_manager_{ver}.py')
        summary_file = Path(f'VERSION_SUMMARY_{ver.upper()}.md') if ver == 'v18' else Path(f'V{ver.upper()}_RESULTS_SUMMARY.md')

        status = '[OK]' if agent_file.exists() else '[MISSING]'
        has_results = '[OK]' if summary_file.exists() else '[MISSING]'

        versions.append({
            'version': ver.upper(),
            'agent': status,
            'results': has_results
        })

    return versions


def update_handover(platform: str = 'all', with_diff: bool = False):
    """Update handover context file."""

    print(f"\n{'='*70}")
    print(f"Updating Handover Context")
    print(f"{'='*70}")

    # Gather data
    existing = parse_existing_handover()
    branch = get_current_branch()
    modified = get_modified_files()
    epics = detect_epic_status()
    versions = detect_strategy_versions()

    # Build new content
    content = f"""# Handover Context

> Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> Branch: {branch}

## 1. Primary Objective
{existing.get('1. Primary Objective', 'Continue V18 strategy development to improve execute rate')}

## 2. Completed Work
"""

    # Add epic status
    for epic in epics:
        content += f"- {epic['status']} **{epic['name']}**: {epic['description']}\n"

    # Add recent commits
    changes = get_git_changes(since='HEAD~10')
    if changes:
        content += "\n### Recent Commits\n"
        for commit in changes[:5]:
            if 'hash' in commit:
                content += f"- `{commit['hash']}` {commit['message']}\n"

    content += f"""
## 3. Key Files
- `backend/agents/elemental_agent_manager_v17.py` (VedAstro hybrid)
- `scripts/backtest_elemental_v17.py` (Backtest runner)
- `HANDOVER_CONTEXT.md` (This file)

### Modified Files ({len(modified)})
"""

    for f in modified[:10]:
        content += f"- `{f}`\n"

    if len(modified) > 10:
        content += f"- ... and {len(modified) - 10} more\n"

    content += f"""
## 4. Strategy Versions
| Version | Agent | Results | Status |
|---------|-------|---------|--------|
"""

    for v in versions:
        content += f"| {v['version']} | {v['agent']} | {v['results']} | - |\n"

    content += f"""
## 5. Reflections
{existing.get('5. Reflections', '''- **Layered Security**: Moving from role-assignment to enforcement in OrderExecutor provides robust defense
- **VedAstro Integration**: 100% VedAstro-driven entries improved quality but reduced quantity
- **Execute Rate Challenge**: Quality signals do not guarantee quantity trades
''')}

## 6. Next Steps
{existing.get('6. Next Steps', '''1. **V18 Development**: Relax VedAstro filters (50% -> 40% confidence)
2. **Improve Execute Rate**: Target 15-25% (currently 6.34%)
3. **Increase Trade Count**: Target 800-1500 trades (currently 331)
4. **Test Changes**: Run smoke test, then full backtest
5. **Update Documentation**: V18_RESULTS_SUMMARY.md
''')}

## 7. Environment Notes
- Python: 3.13+
- Docker: Required for services
- API Keys: Bitvavo (paper trading), DeepSeek (LLM)

## 8. Useful Commands
```bash
# Run backtest
python scripts/backtest_elemental_v17.py

# Paper trading
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR --auto 20

# Check status
python .continue/skills/multi-ai-handover/scripts/handover_manager.py status
```
"""

    # Strip unicode and write file
    content = strip_unicode(content)
    with open('HANDOVER_CONTEXT.md', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[DONE] Updated HANDOVER_CONTEXT.md")

    # Sync to platforms if requested
    if platform in ['all', 'claude']:
        sync_to_platform('claude', content)
    if platform in ['all', 'gemini']:
        sync_to_platform('gemini', content)
    if platform in ['all', 'kimi']:
        sync_to_platform('kimi', content)


def strip_unicode(text: str) -> str:
    """Remove unicode characters that cause encoding issues."""
    # Replace common unicode characters
    replacements = {
        '\u2192': '->',  # →
        '\u23f3': '[PENDING]',  # ⏳
        '\u2705': '[DONE]',  # ✅
        '\u274c': '[MISSING]',  # ❌
        '\u26a0': '[WARNING]',  # ⚠️
        '\ud83d\udcca': '[CHART]',  # 📊
        '\ud83d\udcc1': '[FOLDER]',  # 📁
        '\ud83d\udcdd': '[NOTES]',  # 📝
        '\ud83d\udd10': '[LOCK]',  # 🔐
    }
    for uni, ascii in replacements.items():
        text = text.replace(uni, ascii)
    return text


def sync_to_platform(platform: str, content: str):
    """Sync handover to specific platform."""

    platform_dir = Path(f'.{platform}')
    platform_dir.mkdir(exist_ok=True)

    filepath = platform_dir / 'context.md'

    # Format for platform
    if platform == 'gemini':
        formatted = format_for_gemini(content)
    elif platform == 'claude':
        formatted = format_for_claude(content)
    elif platform == 'kimi':
        formatted = format_for_kimi(content)
    else:
        formatted = content

    # Strip unicode to avoid encoding issues
    formatted = strip_unicode(formatted)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(formatted)

    print(f"[DONE] Synced to {filepath}")


def format_for_claude(content: str) -> str:
    """Format content for Claude."""
    return f"""# Context for Claude

## Current Focus
Continue V18 strategy development to improve execute rate from 6.34% to 15-25%.

## What Was Done Recently
{extract_section(content, '2. Completed Work')}

## Important Files
- `backend/agents/elemental_agent_manager_v17.py` - Current production agent
- `scripts/backtest_elemental_v17.py` - Backtest runner
- `V17_RESULTS_SUMMARY.md` - Latest results

## Continue With
{extract_section(content, '6. Next Steps')}

## Reflections
{extract_section(content, '5. Reflections')}

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""


def format_for_gemini(content: str) -> str:
    """Format content for Gemini."""
    return f"""# Context for Gemini

## Primary Objective
Continue V18 strategy development to improve execute rate.

## Completed Work
{extract_section(content, '2. Completed Work')}

## Key Files
- backend/agents/elemental_agent_manager_v17.py
- scripts/backtest_elemental_v17.py
- V17_RESULTS_SUMMARY.md

## Next Steps
{extract_section(content, '6. Next Steps')}

## Commands
```bash
# Backtest
python scripts/backtest_elemental_v17.py

# Paper trading
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR --auto 20
```

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""


def format_for_kimi(content: str) -> str:
    """Format content for Kimi."""
    return f"""# Context for Kimi

## 主目标 (Primary Objective)
继续V18策略开发，将执行率从6.34%提高到15-25%。

## 已完成工作 (Completed Work)
{extract_section(content, '2. Completed Work')}

## 关键文件 (Key Files)
- backend/agents/elemental_agent_manager_v17.py
- scripts/backtest_elemental_v17.py

## 下一步 (Next Steps)
{extract_section(content, '6. Next Steps')}

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""


def extract_section(content: str, section_name: str) -> str:
    """Extract a section from markdown content."""
    lines = content.split('\n')
    capturing = False
    result = []

    for line in lines:
        if line.startswith(f'## {section_name}'):
            capturing = True
            continue
        if capturing and line.startswith('## '):
            break
        if capturing:
            result.append(line)

    return '\n'.join(result).strip()


def prepare_handover(platform: str, focus: str, output: Optional[str] = None):
    """Prepare handover for specific platform."""

    existing = parse_existing_handover()

    content = f"""# Handover for {platform.title()}

## Focus
{focus}

## Current Status
{existing.get('1. Primary Objective', 'V18 Development')}

## Completed
{existing.get('2. Completed Work', '- V17 complete (+6.96% return)')}

## Next Steps
{existing.get('6. Next Steps', '1. Create V18\n2. Relax VedAstro filters\n3. Run backtest')}

## Key Context
- Execute rate: 6.34% -> target 15-25%
- Trade count: 331 -> target 800-1500
- VedAstro filters: 50% -> 40% confidence

---
*Prepared: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    if output:
        with open(output, 'w') as f:
            f.write(content)
        print(f"[DONE] Handover saved to {output}")
    else:
        print(content)


def show_status(show_epics: bool = False, show_versions: bool = False):
    """Show current project status."""

    print(f"\n{'='*70}")
    print(f"Project Status - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")

    branch = get_current_branch()
    modified = get_modified_files()

    print(f"\n[REPOSITORY]")
    print(f"   Branch: {branch}")
    print(f"   Modified files: {len(modified)}")

    if show_epics:
        print(f"\n[EPICS]")
        for epic in detect_epic_status():
            print(f"   {epic['status']} {epic['name']}: {epic['description']}")

    if show_versions:
        print(f"\n[STRATEGY VERSIONS]")
        for v in detect_strategy_versions():
            print(f"   {v['version']}: Agent {v['agent']} | Results {v['results']}")

    # Recent commits
    changes = get_git_changes(since='HEAD~5')
    if changes:
        print(f"\n[RECENT COMMITS]")
        for commit in changes[:5]:
            if 'hash' in commit:
                print(f"   {commit['hash']} {commit['message']}")


def sync_context(from_file: str, to_file: str):
    """Sync context between files."""

    from_path = Path(from_file)
    to_path = Path(to_file)

    if not from_path.exists():
        print(f"[ERROR] Source file not found: {from_file}")
        return

    with open(from_path, 'r') as f:
        content = f.read()

    to_path.parent.mkdir(parents=True, exist_ok=True)

    with open(to_path, 'w') as f:
        f.write(content)

    print(f"[DONE] Synced {from_file} -> {to_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Multi-AI Handover Manager'
    )
    subparsers = parser.add_subparsers(dest='command')

    # Update
    update_parser = subparsers.add_parser('update', help='Update handover context')
    update_parser.add_argument('--platform', '-p', default='all',
                              choices=['all', 'claude', 'gemini', 'kimi'])
    update_parser.add_argument('--with-diff', '-d', action='store_true')

    # Prepare
    prepare_parser = subparsers.add_parser('prepare', help='Prepare handover for platform')
    prepare_parser.add_argument('--platform', '-p', required=True,
                               choices=['claude', 'gemini', 'kimi'])
    prepare_parser.add_argument('--focus', '-f', default='Continue development')
    prepare_parser.add_argument('--output', '-o')

    # Status
    status_parser = subparsers.add_parser('status', help='Show status')
    status_parser.add_argument('--show-epics', '-e', action='store_true')
    status_parser.add_argument('--show-versions', '-v', action='store_true')

    # Sync
    sync_parser = subparsers.add_parser('sync', help='Sync context files')
    sync_parser.add_argument('--from', dest='from_file', default='HANDOVER_CONTEXT.md')
    sync_parser.add_argument('--to', required=True)

    args = parser.parse_args()

    if args.command == 'update':
        update_handover(args.platform, args.with_diff)

    elif args.command == 'prepare':
        prepare_handover(args.platform, args.focus, args.output)

    elif args.command == 'status':
        show_status(args.show_epics, args.show_versions)

    elif args.command == 'sync':
        sync_context(args.from_file, args.to)

    else:
        parser.print_help()
        print("\n💡 Examples:")
        print("   python handover_manager.py update")
        print("   python handover_manager.py prepare --platform gemini --focus 'V18 dev'")
        print("   python handover_manager.py status --show-epics --show-versions")
        print("   python handover_manager.py sync --to .claude/context.md")


if __name__ == '__main__':
    main()
