"""Bulk-fix datetime.utcnow() -> datetime.now(UTC) in backend/api/ files."""
import os
import re

TARGET_DIR = 'backend/api'

files_to_fix = [
    'websocket_manager.py',
    'paper_trading_ws_simple.py',
    'paper_trading_api.py',
    'kyc_api.py',
    'health.py',
    'approval_api.py',
]

NEEDS_UTC_IMPORT = re.compile(r'^from datetime import.*UTC', re.MULTILINE)
NEEDS_TIMEZONE_IMPORT = re.compile(r'^from datetime import.*timezone', re.MULTILINE)

for fname in files_to_fix:
    path = os.path.join(TARGET_DIR, fname)
    if not os.path.exists(path):
        print(f'SKIP (not found): {fname}')
        continue

    with open(path, encoding='utf-8') as f:
        src = f.read()

    if 'datetime.utcnow()' not in src:
        print(f'OK (no utcnow): {fname}')
        continue

    # Replace utcnow() calls
    src = src.replace('datetime.utcnow()', 'datetime.now(UTC)')

    # Ensure UTC is imported - add it if missing
    if not NEEDS_UTC_IMPORT.search(src):
        # Try to add UTC to existing datetime import
        src = re.sub(
            r'(from datetime import\s+)([^\n]+)',
            lambda m: m.group(0) if 'UTC' in m.group(0) else m.group(1) + m.group(2).rstrip() + ', UTC',
            src,
            count=1
        )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)

    # Verify syntax
    import ast
    try:
        ast.parse(src)
        count = src.count('datetime.utcnow()')
        print(f'FIXED {fname} (remaining utcnow: {count})')
    except SyntaxError as e:
        print(f'SYNTAX ERROR in {fname}: {e}')

# Also fix routers
router_files = ['routers/health.py', 'routers/backtest.py', 'routers/trading_legacy.py']
for fname in router_files:
    path = os.path.join(TARGET_DIR, fname)
    if not os.path.exists(path):
        print(f'SKIP (not found): {fname}')
        continue

    with open(path, encoding='utf-8') as f:
        src = f.read()

    if 'datetime.utcnow()' not in src:
        print(f'OK (no utcnow): {fname}')
        continue

    src = src.replace('datetime.utcnow()', 'datetime.now(UTC)')

    if not NEEDS_UTC_IMPORT.search(src):
        src = re.sub(
            r'(from datetime import\s+)([^\n]+)',
            lambda m: m.group(0) if 'UTC' in m.group(0) else m.group(1) + m.group(2).rstrip() + ', UTC',
            src,
            count=1
        )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)

    import ast
    try:
        ast.parse(src)
        count = src.count('datetime.utcnow()')
        print(f'FIXED {fname} (remaining utcnow: {count})')
    except SyntaxError as e:
        print(f'SYNTAX ERROR in {fname}: {e}')

print('Done.')
