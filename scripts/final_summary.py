#!/usr/bin/env python3
"""Final security summary."""
import json

with open('bandit_final.json') as f:
    data = json.load(f)

totals = data['metrics']['_totals']

print('='*70)
print('FINAL SECURITY SCAN RESULTS')
print('='*70)
print()
print('OVERALL:')
print(f"  HIGH:   {totals['SEVERITY.HIGH']:4d}  {'FIXED!' if totals['SEVERITY.HIGH'] == 0 else 'FAILED'}")
print(f"  MEDIUM: {totals['SEVERITY.MEDIUM']:4d}  {'Acceptable' if totals['SEVERITY.MEDIUM'] < 50 else 'WARNING'}")
print(f"  LOW:    {totals['SEVERITY.LOW']:4d}  {'Acceptable' if totals['SEVERITY.LOW'] < 5000 else 'WARNING'}")
print()
print(f"Lines of code: {totals['loc']:,}")
print(f"Skipped tests: {totals['skipped_tests']}")
print()

# Group by code
from collections import defaultdict
by_code = defaultdict(int)
for r in data.get('results', []):
    by_code[r['test_id']] += 1

print('TOP 10 ISSUE CODES:')
for code, count in sorted(by_code.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {code}: {count}")

print()
print('='*70)
print('SECURITY GRADE: ', end='')
if totals['SEVERITY.HIGH'] == 0 and totals['SEVERITY.MEDIUM'] < 30:
    print('A (Production Ready)')
elif totals['SEVERITY.HIGH'] == 0:
    print('B (Good)')
else:
    print('F (Failed)')
print('='*70)
