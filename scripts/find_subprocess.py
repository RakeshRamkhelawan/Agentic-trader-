#!/usr/bin/env python3
"""Find subprocess issues."""
import json

with open('bandit_low.json') as f:
    data = json.load(f)

for code in ['B603', 'B607', 'B404']:
    issues = [r for r in data['results'] if r['test_id'] == code and 'test' not in r['filename'].lower()]
    print(f'{code}: {len(issues)} issues')
    for r in issues[:10]:
        print(f"  {r['filename']}:{r['line_number']}")
    print()
