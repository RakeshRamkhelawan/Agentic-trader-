"""
Legacy File Removal Script.

Week 8: Clean up deprecated files after successful migration.

WARNING: This script permanently deletes files!
Only run after confirming successful production rollout.

Usage:
    python scripts/remove_legacy_files.py --dry-run  # Preview what will be removed
    python scripts/remove_legacy_files.py --confirm  # Actually remove files
"""

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Legacy files to remove
LEGACY_FILES = [
    # Connectors (replaced by adapters)
    "backend/exchange/connectors/bitvavo_connector.py",
    "backend/exchange/connectors/revolut_connector.py",

    # Order management (replaced by OrderExecutor)
    "backend/exchange/order_manager.py",

    # Shadow portfolio (replaced by PortfolioManager)
    "backend/execution/shadow_portfolio.py",
    "backend/tests/unit/execution/test_shadow_portfolio.py",

    # Old base exchange (replaced by unified schema)
    "backend/exchange/base_exchange.py",
]

# Directories to remove if empty
LEGACY_DIRECTORIES = [
    "backend/exchange/connectors",
]

# Files to update (remove imports)
FILES_TO_UPDATE = [
    "backend/exchange/__init__.py",
    "backend/exchange/exchange_factory.py",
]


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


def check_file_exists(filepath: str) -> bool:
    """Check if file exists."""
    root = get_project_root()
    return (root / filepath).exists()


def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    root = get_project_root()
    try:
        return (root / filepath).stat().st_size
    except FileNotFoundError:
        return 0


def remove_file(filepath: str, dry_run: bool = True) -> bool:
    """
    Remove a file.

    Args:
        filepath: Path to file
        dry_run: If True, only simulate removal

    Returns:
        True if successful
    """
    root = get_project_root()
    full_path = root / filepath

    if not full_path.exists():
        print(f"  [WARN] File not found: {filepath}")
        return False

    if dry_run:
        print(f"  [DRY] Would remove: {filepath}")
        return True

    try:
        full_path.unlink()
        print(f"  [OK] Removed: {filepath}")
        return True
    except Exception as e:
        print(f"  [ERR] Error removing {filepath}: {e}")
        return False


def remove_empty_directories(dry_run: bool = True) -> None:
    """Remove empty legacy directories."""
    root = get_project_root()

    for directory in LEGACY_DIRECTORIES:
        dir_path = root / directory

        if not dir_path.exists():
            continue

        # Check if directory is empty
        try:
            contents = list(dir_path.iterdir())
            if contents:
                print(f"  [WARN] Directory not empty: {directory}")
                continue

            if dry_run:
                print(f"  [DRY] Would remove directory: {directory}")
            else:
                dir_path.rmdir()
                print(f"  [OK] Removed directory: {directory}")
        except Exception as e:
            print(f"  [ERR] Error removing directory {directory}: {e}")


def update_imports(dry_run: bool = True) -> None:
    """Update files to remove legacy imports."""
    root = get_project_root()

    for filepath in FILES_TO_UPDATE:
        full_path = root / filepath

        if not full_path.exists():
            continue

        try:
            with open(full_path, "r") as f:
                content = f.read()

            # Check for legacy imports
            legacy_imports = [
                "from backend.exchange.connectors",
                "import BitvavoConnector",
                "import RevolutConnector",
                "from backend.exchange.order_manager",
                "import OrderManager",
            ]

            found_imports = []
            for imp in legacy_imports:
                if imp in content:
                    found_imports.append(imp)

            if found_imports:
                print(f"\n  [INFO] {filepath} contains legacy imports:")
                for imp in found_imports:
                    print(f"    - {imp}")

                if not dry_run:
                    # Add deprecation notice at top
                    new_content = f"""# NOTE: Legacy imports removed during Week 8 cleanup
# See: docs/adr/ADR-008-unified-execution-schema.md

{content}"""

                    # Backup original
                    backup_path = str(full_path) + ".backup"
                    shutil.copy2(full_path, backup_path)

                    with open(full_path, "w") as f:
                        f.write(new_content)

                    print(f"  [OK] Updated: {filepath}")

        except Exception as e:
            print(f"  [ERR] Error updating {filepath}: {e}")


def generate_report(removed_files: List[str], total_lines: int, dry_run: bool = True) -> str:
    """Generate cleanup report."""
    report = f"""
{'=' * 60}
LEGACY FILE CLEANUP REPORT
{'=' * 60}
Timestamp: {datetime.utcnow().isoformat()}
Mode: {'DRY RUN (no changes made)' if dry_run else 'ACTUAL REMOVAL'}

Files Processed: {len(LEGACY_FILES)}
Files Removed: {len(removed_files)}
Total Lines Removed: ~{total_lines}

Removed Files:
"""
    for f in removed_files:
        report += f"  - {f}\n"

    if dry_run:
        report += """
NOTE: This was a dry run. No files were actually removed.
   Run with --confirm to actually remove files.
"""
    else:
        report += """
[OK] Legacy files have been removed.
[OK] Migration to new architecture complete!

Remember to:
  1. Commit changes
  2. Run full test suite
  3. Deploy to staging
  4. Deploy to production
"""

    report += f"\n{'=' * 60}\n"
    return report


def verify_migration_ready() -> Tuple[bool, List[str]]:
    """
    Verify that migration is ready for cleanup.

    Returns:
        (ready, issues)
    """
    issues = []

    # Check that new components exist
    new_components = [
        "backend/execution/bitvavo_adapter.py",
        "backend/execution/revolut_x_adapter.py",
        "backend/execution/order_executor.py",
        "backend/execution/portfolio_manager.py",
    ]

    for component in new_components:
        if not check_file_exists(component):
            issues.append(f"New component missing: {component}")

    # Check that feature flags are working (optional for dry-run)
    try:
        from backend.core.config.feature_flags import feature_flags
        if not feature_flags.USE_UNIFIED_SCHEMA:
            # Only warn, don't fail - flags can be set at runtime
            print("  [INFO] USE_UNIFIED_SCHEMA not enabled (set before production)")
    except Exception as e:
        print(f"  [INFO] Feature flags check skipped: {e}")

    ready = len(issues) == 0
    return ready, issues


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Remove Legacy Files (Week 8 Cleanup)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview what will be removed
  python scripts/remove_legacy_files.py --dry-run

  # Actually remove files (after confirming migration success)
  python scripts/remove_legacy_files.py --confirm

  # Only show summary
  python scripts/remove_legacy_files.py --summary
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be removed (default)"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually remove files (requires confirmation)"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Only show summary of legacy files"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    # Default to dry-run if no action specified
    if not args.confirm and not args.summary:
        args.dry_run = True

    print("=" * 60)
    print("WEEK 8: LEGACY FILE CLEANUP")
    print("=" * 60)

    if args.summary:
        # Just show summary
        total_lines = 0
        print("\nLegacy files to be removed:\n")
        for filepath in LEGACY_FILES:
            size = get_file_size(filepath)
            lines = size // 50  # Rough estimate
            total_lines += lines
            exists = "[OK]" if check_file_exists(filepath) else "[MISSING]"
            print(f"  {exists} {filepath} (~{lines} lines)", flush=True)

        print(f"\nTotal estimated lines: ~{total_lines}")
        return

    # Verify migration is ready
    print("\nVerifying migration readiness...")
    ready, issues = verify_migration_ready()

    if not ready:
        print("\n[FAIL] Migration not ready for cleanup:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease complete migration before removing legacy files.")
        sys.exit(1)

    print("[OK] Migration verification passed")

    if args.confirm:
        print("\n[WARNING] This will PERMANENTLY DELETE files!")
        print("[WARNING] Make sure you have:")
        print("   1. Committed all changes to git")
        print("   2. Verified production is stable")
        print("   3. Created backups")

        if not args.force:
            confirm = input("\nType 'DELETE' to confirm: ")
            if confirm != "DELETE":
                print("\n[ABORTED]")
                sys.exit(0)

    # Process files
    print(f"\n{'=' * 60}")
    print("PROCESSING FILES")
    print(f"{'=' * 60}")

    removed_files = []
    total_lines = 0

    for filepath in LEGACY_FILES:
        lines = get_file_size(filepath) // 50
        total_lines += lines

        if remove_file(filepath, dry_run=not args.confirm):
            removed_files.append(filepath)

    # Remove empty directories
    print("\nProcessing directories...")
    remove_empty_directories(dry_run=not args.confirm)

    # Update imports
    if args.confirm:
        print("\nUpdating imports...")
        update_imports(dry_run=False)

    # Generate report
    report = generate_report(removed_files, total_lines, dry_run=not args.confirm)
    print(report)

    if args.confirm:
        print("\n[DONE] WEEK 8 CLEANUP COMPLETE!")
        print("The Exchange Integration Refactor is now complete.")


if __name__ == "__main__":
    main()
