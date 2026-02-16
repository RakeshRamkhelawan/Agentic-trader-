type "c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\docs\kanban\SAMKHYA_MASTER_KANBAN_TDD.md" > master_full.txt 2>&1
type "c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\docs\kanban\FASE_01_CONSCIOUSNESS_OODA_NAVAGRAHA_BRIDGE.md" > fase01_full.txt 2>&1
type "c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\HANDOVER_CONTEXT.md" > handover_full.txt 2>&1
type "c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\docs\reports\EPIC_01_CODE_REVIEW.md" > epic01_full.txt 2>&1
echo Files captured
dir *.txt /b | findstr "master_full fase01_full handover_full epic01_full"