type "c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\HANDOVER_CONTEXT.md" | findstr /i "API endpoint WebSocket SSE /navagraha /market /agent" > temp_api_scan.txt 2>&1
type "c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\docs\kanban\SAMKHYA_MASTER_KANBAN_TDD.md" | findstr /n /i "Phase" > temp_phases.txt 2>&1
type "c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\docs\kanban\FASE_01_CONSCIOUSNESS_OODA_NAVAGRAHA_BRIDGE.md" | findstr /n /i "Microtask Task-1" > temp_fase01.txt 2>&1
type "c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\backend\api\main.py" 2>nul | findstr /i "router FastAPI endpoint" > temp_main_api.txt 2>&1
dir "c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\backend\api\" /b 2>nul
type temp_api_scan.txt
type temp_phases.txt
echo ---
type temp_fase01.txt | findstr /i "1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9"