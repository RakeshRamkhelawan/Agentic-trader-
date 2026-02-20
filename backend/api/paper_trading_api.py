"""
Paper Trading API Endpoints
"""

import asyncio
import logging
import os
import subprocess
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.core.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/paper-trading", tags=["paper-trading"])

# Global state
_trading_process: Optional[subprocess.Popen] = None
_trading_logs: list = []


class StartSessionRequest(BaseModel):
    duration: int = 8
    capital: float = 10000.0


@router.get("/status")
async def get_status():
    """Get current paper trading session status."""
    global _trading_process
    
    is_running = _trading_process is not None and _trading_process.poll() is None
    
    # Read latest logs from session log file
    logs = []
    trades = []
    portfolio = None
    stats = None
    
    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "paper_trading_session.log")
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                file_logs = f.readlines()
                logs = file_logs[-50:]  # Last 50 lines
                
                # Parse trades from logs
                def is_trade_line(line: str) -> bool:
                    """Return True if the line matches a trade pattern."""
                    return (
                        '[' in line and
                        ']' in line and
                        ('BUY' in line or 'SELL' in line) and
                        '@ EUR' in line and
                        'Executed' not in line
                    )

                def parse_trade_line(line: str) -> Optional[dict]:
                    """Parse a trade line and return a trade dict or None if parsing fails."""
                    try:
                        # Extract timestamp [HH:MM:SS]
                        ts_start = line.find('[')
                        ts_end = line.find(']', ts_start)
                        timestamp = line[ts_start+1:ts_end]

                        # Extract agent name [AgentName]
                        agent_start = line.find('[', ts_end + 1)
                        agent_end = line.find(']', agent_start)
                        agent = line[agent_start+1:agent_end].strip()

                        # Find BUY or SELL
                        if 'BUY' in line:
                            side = 'buy'
                            side_idx = line.find('BUY')
                        else:
                            side = 'sell'
                            side_idx = line.find('SELL')

                        # Rest of line after side
                        rest = line[side_idx + 4:].strip()
                        parts = rest.split()

                        if len(parts) >= 8:
                            qty = float(parts[0])
                            symbol = parts[1]
                            price = float(parts[4])
                            value = float(parts[7])
                            return {
                                "timestamp": f"2026-02-20T{timestamp}",
                                "symbol": symbol,
                                "side": side,
                                "qty": qty,
                                "price": price,
                                "value": value,
                                "agent": agent,
                                "exchange": "Bitvavo"
                            }
                    except Exception:
                        return None
                    return None

                for line in file_logs:
                    # Parse trade lines like: [01:38:52] [Breakout          ] BUY     90.255737 FET/EUR         @ EUR 0.14 = EUR 12.55
                    if is_trade_line(line):
                        trade = parse_trade_line(line)
                        if trade:
                            trades.append(trade)
                    
                    # Parse status lines for portfolio
                    if 'STATUS |' in line and 'P&L:' in line:
                        try:
                            # Extract P&L info
                            import re
                            pnl_match = re.search(r'P&L:\s*EUR\s*([+-]?[\d.]+)', line)
                            if pnl_match:
                                pnl = float(pnl_match.group(1))
                                # Also check next line for volume
                                idx = file_logs.index(line)
                                if idx + 1 < len(file_logs):
                                    vol_match = re.search(r'Volume:\s*EUR\s*([\d.,]+)', file_logs[idx + 1])
                                    volume = vol_match.group(1).replace(',', '') if vol_match else "0"
                                else:
                                    volume = "0"
                                
                                stats = {
                                    "total_trades": len(trades),
                                    "pnl": pnl,
                                    "volume": volume
                                }
                        except:
                            pass
        except Exception as e:
            logs = [f"Error reading logs: {e}"]
    
    return {
        "is_running": is_running,
        "trading_mode": settings.TRADING_MODE,
        "logs": logs[-30:] if logs else [],
        "trades": trades[-20:] if trades else [],  # Last 20 trades
        "portfolio": portfolio,
        "stats": stats,
        "websocket_url": "/ws/paper-trading"
    }


@router.post("/start")
async def start_paper_trading(request: StartSessionRequest, background_tasks: BackgroundTasks):
    """
    Start a new paper trading session with €10,000 and ALL 400+ assets.
    """
    global _trading_process, _trading_logs
    
    if settings.TRADING_MODE != "paper":
        raise HTTPException(
            status_code=400, 
            detail=f"TRADING_MODE is '{settings.TRADING_MODE}', must be 'paper'"
        )
    
    # Check if already running
    if _trading_process and _trading_process.poll() is None:
        raise HTTPException(status_code=400, detail="Trading session already running")
    
    try:
        # Get the project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Use FAST version (TOP 50 assets for speed)
        script_path = os.path.join(project_root, "scripts", "real_paper_trading_fast.py")
        
        if not os.path.exists(script_path):
            # Fallback to original
            script_path = os.path.join(project_root, "scripts", "real_paper_trading.py")
            if not os.path.exists(script_path):
                script_path = os.path.join(project_root, "backend", "services", "real_paper_trading.py")
        
        logger.info(f"Starting paper trading from: {script_path}")
        
        # Start the trading process
        _trading_logs = []
        
        # Use subprocess.Popen to run in background
        env = os.environ.copy()
        env['PYTHONPATH'] = project_root
        
        # Log files for the subprocess
        log_file = os.path.join(project_root, "paper_trading_session.log")
        
        _trading_process = subprocess.Popen(
            [sys.executable, "-u", script_path, "--duration", str(request.duration), "--capital", str(request.capital)],
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
            cwd=project_root,
            env=env
        )
        
        logger.info(f"Paper trading started with PID: {_trading_process.pid}")
        
        return {
            "status": "started",
            "pid": _trading_process.pid,
            "duration": request.duration,
            "capital": request.capital,
            "message": f"Paper trading started with €{request.capital:,.2f} for {request.duration} hours"
        }
        
    except Exception as e:
        logger.error(f"Failed to start paper trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_paper_trading():
    """Stop the current paper trading session."""
    global _trading_process
    
    if not _trading_process or _trading_process.poll() is not None:
        return {"status": "not_running", "message": "No active session"}
    
    try:
        _trading_process.terminate()
        _trading_process.wait(timeout=5)
        logger.info("Paper trading stopped")
        return {"status": "stopped", "message": "Trading session stopped"}
    except Exception as e:
        # Force kill if needed
        try:
            _trading_process.kill()
        except:
            pass
        return {"status": "error", "message": str(e)}


@router.get("/ws-url")
async def get_websocket_url():
    """Get WebSocket URL."""
    return {
        "websocket_url": "/ws/paper-trading",
        "channels": ["paper_trading.live", "paper_trading.stats"]
    }
