import sys
import os

# Add project root
sys.path.insert(0, os.getcwd())

try:
    from backend.core.auth.context import set_current_tenant
    print("Import successful!")
    print(set_current_tenant)
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
