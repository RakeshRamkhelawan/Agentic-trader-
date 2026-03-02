import sys
import os

sys.path.insert(0, os.getcwd())

try:
    from backend.services.trading_service import TradingService
    print("Import successful!")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
