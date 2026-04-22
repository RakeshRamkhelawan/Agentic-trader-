"""Move loose root-level scripts to scripts/one-off/ directory."""
import os
import shutil

ONE_OFF = 'scripts/one-off'
os.makedirs(ONE_OFF, exist_ok=True)

scripts_to_move = [
    'analyze_v11_performance.py',
    'analyze_v12_performance.py',
    'create_user.py',
    'create_user_workaround.py',
    'demo_conscious_agents.py',
    'fix_index_html.py',
    'fix_public_paths.py',
    'inject_config_inline.py',
    'patch_backend.py',
    'patch_main.py',
    'run_backtest_analysis.py',
    'run_fast_shadow_test.py',
    'run_integration_tests.py',
    'run_shadow_mode.py',
    'run_v12_all_agents_backtest.py',
    'run_v12_backtest_detailed_logger.py',
    'run_v12_backtest_detailed_logger_v2.py',
    'run_v12_backtest_emergency.py',
    'run_v12_backtest_final.py',
    'run_v12_backtest_series.py',
    'run_v12_enhanced_backtest.py',
    'run_v12_full_backtest.py',
    'run_v12_godtier_test.py',
    'run_v12_llm_reflection_test.py',
    'run_v12_self_improving_test.py',
    'run_v13_evolution_test.py',
    'run_wiring_tests_sqlite.py',
    'setup_auth.py',
    'setup_auth_simple.py',
    'test_backend_direct.py',
    'test_db_connection.py',
    'test_deepseek.py',
    'test_deepseek_debug.py',
    'test_exchange_apis.py',
    'test_exchange_simple.py',
    'test_master_prompts.py',
    'test_meta_orchestrator.py',
    'test_ollama_connection.py',
    'test_ollama_status.py',
    'test_routes_simple.py',
    'test_wiring_real.py',
    'fix_security_middleware.py',
    'fix_utcnow.py',
]

moved = 0
skipped = 0
for script in scripts_to_move:
    if os.path.exists(script):
        dest = os.path.join(ONE_OFF, script)
        shutil.move(script, dest)
        moved += 1
    else:
        skipped += 1

print(f'Moved {moved} scripts to {ONE_OFF}/ ({skipped} not found)')

# Verify root is clean
remaining = [f for f in os.listdir('.') if f.endswith('.py') and f not in ('alembic.ini',)]
print(f'Remaining .py files in root: {remaining}')
