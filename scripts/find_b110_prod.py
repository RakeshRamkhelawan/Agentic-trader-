#!/usr/bin/env python3
"""Find B110 issues in production code."""
import json

with open('bandit_low.json') as f:
    data = json.load(f)

# Find B110 issues in non-test files
b110 = [r for r in data['results'] if r['test_id'] == 'B110' and 'test' not in r['filename'].lower()]
print(f'B110 (try/except/pass) in production code: {len(b110)}')
for r in b110[:15]:
    print(f"  {r['filename']}:{r['line_number']}")
