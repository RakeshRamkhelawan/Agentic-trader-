cd /d c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621
dir /b backend 2>nul
tree /f /a backend | findstr /v "__pycache__" | more