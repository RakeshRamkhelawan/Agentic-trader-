#!/usr/bin/env python3
"""Analyze LOW severity Bandit issues."""
import json
from collections import defaultdict

def main():
    with open('bandit_low.json', 'r') as f:
        data = json.load(f)
    
    results = [r for r in data.get('results', []) if r['issue_severity'] == 'LOW']
    
    # Group by issue code
    by_code = defaultdict(list)
    by_file = defaultdict(list)
    
    for r in results:
        by_code[r['test_id']].append(r)
        by_file[r['filename']].append(r)
    
    print('='*80)
    print(f'LOW SEVERITY ISSUES BREAKDOWN ({len(results)} total)')
    print('='*80)
    
    print('\nBY ISSUE CODE:')
    print('-'*80)
    for code in sorted(by_code.keys(), key=lambda x: len(by_code[x]), reverse=True):
        issues = by_code[code]
        print(f"\n{code}: {len(issues)} occurrences")
        print(f"  {issues[0]['issue_text'][:70]}...")
        # Show first 2 examples
        for i in issues[:2]:
            print(f"    - {i['filename'].split('/')[-1]}:{i['line_number']}")
        if len(issues) > 2:
            print(f"    ... and {len(issues)-2} more")
    
    print('\n' + '='*80)
    print('TOP 10 FILES WITH MOST LOW ISSUES:')
    print('-'*80)
    for fname in sorted(by_file.keys(), key=lambda x: len(by_file[x]), reverse=True)[:10]:
        count = len(by_file[fname])
        codes = set(r['test_id'] for r in by_file[fname])
        print(f"  {count:4d} - {fname.split('/')[-1]} ({', '.join(codes)})")

if __name__ == '__main__':
    main()
