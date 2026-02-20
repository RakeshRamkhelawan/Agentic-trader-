#!/bin/bash
# Start 8-hour paper trading session

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOGFILE="paper_trading_8h_$TIMESTAMP.log"

echo "Starting 8-hour Ultimate Paper Trading Session"
echo "Log file: $LOGFILE"
echo ""
echo "Session Details:"
echo "  - Duration: 8 hours"
echo "  - Capital: EUR 10,000"
echo "  - Exchanges: Bitvavo + Revolut X"
echo "  - Symbols: All available pairs"
echo ""
echo "Press Ctrl+C to stop (or let it run for 8 hours)"
echo ""

# Start the trading session
python scripts/ultimate_paper_trading.py --duration 8 --capital 10000 2>&1 | tee "$LOGFILE"

echo ""
echo "Session complete! Check $LOGFILE for details"
