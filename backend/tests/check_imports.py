
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    print("Attempting to import app from backend.api.main...")
    from backend.api.main import app
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
