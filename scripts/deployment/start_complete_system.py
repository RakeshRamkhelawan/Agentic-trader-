#!/usr/bin/env python
"""Start complete Agentic Trader system - Backend + Frontend.
Uses conflict-free ports to avoid conflicts with SanskritiSetu and other services.
"""
import os
import sys
import subprocess
import time
import webbrowser

def main():
    base_dir = r"C:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621"
    frontend_dir = os.path.join(base_dir, "frontend")

    # Set environment variables for backend (conflict-free ports)
    env = os.environ.copy()
    env['AUTH_DISABLED'] = 'true'
    env['REDIS_URL'] = 'redis://localhost:6380/0'  # Port 6380 instead of 6379
    env['DATABASE_URL'] = 'postgresql+asyncpg://trader:trading_secure@localhost:5433/trading_db'  # Port 5433 instead of 5432
    env['CLICKHOUSE_HOST'] = 'localhost'
    env['CLICKHOUSE_PORT'] = '8124'  # Port 8124 instead of 8123

    print("="*60)
    print("Starting Agentic Trader Platform")
    print("="*60)
    print("\nPort Configuration (Conflict-Free):")
    print("  - Backend API:  http://localhost:8005")
    print("  - Frontend:     http://localhost:3005")
    print("  - Redis:        localhost:6380")
    print("  - PostgreSQL:   localhost:5433")
    print("  - ClickHouse:   localhost:8124")
    print("="*60)

    # Start backend
    print("\n[1/3] Starting Backend on port 8005...")
    backend_proc = subprocess.Popen(
        ['python', '-m', 'uvicorn', 'backend.api.main:app', '--host', '0.0.0.0', '--port', '8005'],
        cwd=base_dir,
        env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    # Wait for backend to start
    time.sleep(5)
    print("[OK] Backend started")

    # Start frontend
    print("\n[2/3] Starting Frontend on port 3005...")
    frontend_proc = subprocess.Popen(
        ['npm', 'run', 'dev', '--', '--port', '3005'],
        cwd=frontend_dir,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    time.sleep(3)
    print("[OK] Frontend started")

    # Open browser
    print("\n[3/3] Opening browser...")
    webbrowser.open('http://localhost:3005')

    print("\n" + "="*60)
    print("System is running!")
    print("  - Frontend: http://localhost:3005")
    print("  - Backend:  http://localhost:8005")
    print("  - API Docs: http://localhost:8005/docs")
    print("="*60)
    print("\nPress Ctrl+C to stop all services...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("[OK] All services stopped")

if __name__ == '__main__':
    main()
