#!/usr/bin/env python3
"""Find hardcoded password issues."""
import json

with open('bandit_low.json') as f:
    data = json.load(f)

for code in ['B105', 'B106', 'B107']:
    issues = [r for r in data['results'] if r['test_id'] == code and 'test' not in r['filename'].lower()]
    print(f'{code}: {len(issues)} issues')
    for r in issues:
        print(f"  {r['filename']}:{r['line_number']} - {r['issue_text'][:60]}")
    print()
