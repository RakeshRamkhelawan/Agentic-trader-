#!/usr/bin/env python3
import shutil
from pathlib import Path
from datetime import datetime
import os

BACKUP_DIR = Path(f"data/backup/cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

Path('backtest_results').mkdir(exist_ok=True)
Path('logs').mkdir(exist_ok=True)
Path('reports').mkdir(exist_ok=True)

moved = 0
total_mb = 0

print("=" * 60)
print("CLEANUP: Moving files to proper directories")
print("=" * 60)
print(f"Backup: {BACKUP_DIR}")
print()

# Move backtest files
for pattern in ['backtest_*.json', 'elemental_backtest_*.json', 'elemental_backtest_*.csv', 'enterprise_backtest_*.json']:
    for file in list(Path('.').glob(pattern)):
        if file.is_file() and not str(file).startswith('venv') and file.exists():
            try:
                # Get size before moving
                size = file.stat().st_size
                mb = size / (1024*1024)

                # Backup
                backup = BACKUP_DIR / file.name
                shutil.copy2(file, backup)

                # Move
                dest = Path('backtest_results') / file.name
                if dest.exists():
                    dest = Path('backtest_results') / f"{file.stem}_2{file.suffix}"

                shutil.move(str(file), str(dest))
                moved += 1
                total_mb += mb
                print(f"[OK] {file.name[:45]:45} ({mb:.1f} MB)")
            except Exception as e:
                print(f"[ERR] {file.name}: {e}")

print()
print("=" * 60)
print(f"DONE: {moved} files moved, {total_mb:.1f} MB")
print(f"Backup location: {BACKUP_DIR}")
print("=" * 60)
