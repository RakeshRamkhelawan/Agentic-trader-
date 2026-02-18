cd /d c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621
dir /s /b *test*.py pytest.ini setup.cfg pyproject.toml tox.ini 2>nul | findstr /v "__pycache__"