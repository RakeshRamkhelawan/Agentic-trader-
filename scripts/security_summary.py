#!/usr/bin/env python3
"""Security scan summary script."""
import json
import sys

def main():
    with open('bandit_final_report.json', 'r') as f:
        data = json.load(f)
    
    print('='*60)
    print('BANDIT SECURITY SCAN RESULTS')
    print('='*60)
    
    totals = data['metrics']['_totals']
    total_issues = totals['SEVERITY.HIGH'] + totals['SEVERITY.MEDIUM'] + totals['SEVERITY.LOW']
    
    print(f'Total issues: {total_issues}')
    print(f'  HIGH:   {totals["SEVERITY.HIGH"]}')
    print(f'  MEDIUM: {totals["SEVERITY.MEDIUM"]}')
    print(f'  LOW:    {totals["SEVERITY.LOW"]}')
    print(f'Lines of code: {totals["loc"]}')
    
    # Results by file for HIGH severity
    print('\n' + '='*60)
    print('HIGH SEVERITY BREAKDOWN')
    print('='*60)
    
    high_issues = [r for r in data.get('results', []) if r['issue_severity'] == 'HIGH']
    
    if not high_issues:
        print('No HIGH severity issues found!')
    else:
        for issue in high_issues:
            print(f"\n{issue['filename']}:{issue['line_number']}")
            print(f"  {issue['issue_text']}")
            print(f"  CWE: {issue.get('issue_cwe', {}).get('id', 'N/A')}")
    
    print('\n' + '='*60)
    print('SECURITY SCORE')
    print('='*60)
    
    if totals['SEVERITY.HIGH'] == 0:
        print('Status: PASS (No high severity issues)')
        return 0
    else:
        print(f'Status: FAIL ({totals["SEVERITY.HIGH"]} high severity issues)')
        return 1

if __name__ == '__main__':
    sys.exit(main())
