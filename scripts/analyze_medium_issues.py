#!/usr/bin/env python3
"""Analyze MEDIUM severity Bandit issues."""
import json
from collections import defaultdict

def main():
    with open('bandit_medium.json', 'r') as f:
        data = json.load(f)

    results = data.get('results', [])

    # Group by issue code
    by_code = defaultdict(list)
    by_file = defaultdict(list)

    for r in results:
        if r['issue_severity'] == 'MEDIUM':
            by_code[r['test_id']].append(r)
            by_file[r['filename']].append(r)

    print('='*80)
    print('MEDIUM SEVERITY ISSUES BREAKDOWN')
    print('='*80)

    print(f"\nTotal MEDIUM issues: {len([r for r in results if r['issue_severity'] == 'MEDIUM'])}")

    print('\n' + '='*80)
    print('BY ISSUE CODE')
    print('='*80)
    for code in sorted(by_code.keys()):
        issues = by_code[code]
        print(f"\n{code}: {len(issues)} occurrences")
        print(f"  Description: {issues[0]['issue_text'][:60]}...")
        for i in issues[:3]:  # Show first 3
            print(f"    - {i['filename']}:{i['line_number']}")
        if len(issues) > 3:
            print(f"    ... and {len(issues)-3} more")

    print('\n' + '='*80)
    print('FILES WITH MOST ISSUES')
    print('='*80)
    for fname in sorted(by_file.keys(), key=lambda x: len(by_file[x]), reverse=True)[:10]:
        count = len(by_file[fname])
        print(f"  {count:2d} - {fname}")

if __name__ == '__main__':
    main()
