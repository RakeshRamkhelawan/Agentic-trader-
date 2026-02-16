cd /d c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\backend
findstr /s /i /n "password.*=.*[\"\'].*[\"\']" *.py | findstr /v "password_hash" | findstr /v "#" | more
findstr /s /i /n "api_key.*=.*[\"\'].*[\"\']" *.py | findstr /v "#" | more
findstr /s /i /n "secret.*=.*[\"\'].*[\"\']" *.py | findstr /v "secret_key" | findstr /v "#" | more