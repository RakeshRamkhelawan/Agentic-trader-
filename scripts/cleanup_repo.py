"""
Repository Cleanup Script - SAFE VERSION

Verplaatst files naar juiste directories met backups.
"""

import shutil
import os
from pathlib import Path
from datetime import datetime

# Backup dir
BACKUP_DIR = Path(f"data/backup/cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

def ensure_dirs():
    """Maak directory structuur."""
    dirs = ['backtest_results', 'logs', 'reports', 'data/backup', '.tmp']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def move_with_backup(src: Path, dest_dir: Path) -> bool:
    """Verplaats file met backup."""
    try:
        # Backup
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / src.name
        shutil.copy2(src, backup_path)

        # Destination
        dest = dest_dir / src.name
        if dest.exists():
            # Rename if exists
            dest = dest_dir / f"{src.stem}_{datetime.now().strftime('%H%M%S')}{src.suffix}"

        shutil.move(src, dest)
        return True
    except Exception as e:
        print(f"  Error moving {src}: {e}")
        return False

def cleanup():
    """Main cleanup."""
    print("=" * 60)
    print("REPOSITORY CLEANUP - SAFE MODE")
    print("=" * 60)
    print(f"Backup: {BACKUP_DIR}")
    print()

    ensure_dirs()

    moved = 0
    total_mb = 0

    # 1. Backtest files
    backtest_patterns = ['backtest_*.json', 'elemental_backtest_*.json',
                        'elemental_backtest_*.csv', 'enterprise_backtest_*.json',
                        'enterprise_backtest_*.csv']

    for pattern in backtest_patterns:
        for file in Path('.').glob(pattern):
            if file.is_file() and not str(file).startswith('venv'):
                if move_with_backup(file, Path('backtest_results')):
                    mb = file.stat().st_size / (1024 * 1024)
                    total_mb += mb
                    moved += 1
                    print(f"✓ {file.name[:45]:45} → backtest_results/ ({mb:.1f} MB)")

    # 2. Bandit reports
    for file in Path('.').glob('bandit*.json'):
        if file.is_file():
            if move_with_backup(file, Path('reports')):
                mb = file.stat().st_size / (1024 * 1024)
                total_mb += mb
                moved += 1
                print(f"✓ {file.name[:45]:45} → reports/ ({mb:.1f} MB)")

    # 3. Log files
    log_patterns = ['*.log', 'debug_*.txt', 'filtered_*.txt', 'verify_*.log',
                   'fase01_full.txt', 'project_files_list.txt']

    for pattern in log_patterns:
        for file in Path('.').glob(pattern):
            if file.is_file() and file.stat().st_size > 1000:  # > 1KB
                if move_with_backup(file, Path('logs')):
                    mb = file.stat().st_size / (1024 * 1024)
                    total_mb += mb
                    moved += 1
                    print(f"✓ {file.name[:45]:45} → logs/ ({mb:.1f} MB)")

    # 4. Safety report
    if Path('safety_report.json').exists():
        if move_with_backup(Path('safety_report.json'), Path('reports')):
            mb = Path('safety_report.json').stat().st_size / (1024 * 1024)
            total_mb += mb
            moved += 1
            print(f"✓ safety_report.json → reports/ ({mb:.1f} MB)")

    # Summary
    print()
    print("=" * 60)
    print(f"SUMMARY: {moved} files moved, {total_mb:.1f} MB freed")
    print(f"Backup: {BACKUP_DIR}")
    print("=" * 60)
    print()
    print("NEXT STEPS:")
    print("1. Verify: python -c 'import backend'")
    print("2. Update .gitignore")
    print("3. Test: python scripts/summarize_batches.py")

if __name__ == "__main__":
    response = input("Move files with backup? (yes/no): ")
    if response.lower() == "yes":
        cleanup()
    else:
        print("Cancelled.")
