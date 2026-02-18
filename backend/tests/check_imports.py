import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    print("Attempting to import app from backend.api.main...")

    print("Success!")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
