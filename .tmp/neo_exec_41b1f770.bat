cd /d c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\backend
python -m bandit -r . -f json -o bandit_results.json 2>nul
python -m bandit -r . -ll