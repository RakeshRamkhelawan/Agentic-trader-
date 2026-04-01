import subprocess
import json

res = subprocess.run(['python', '-m', 'ruff', 'check', 'backend/', '--output-format=json'], capture_output=True, text=True, encoding='utf-8')
data = json.loads(res.stdout)
errors = [(d['filename'].split('\\')[-1], d['location']['row'], d['message']) for d in data if 'F841' in d.get('code', '')]
for fn, row, msg in errors:
    print(f"{fn}:{row} | {msg}")
print(f"\nTotal F841 errors: {len(errors)}")
