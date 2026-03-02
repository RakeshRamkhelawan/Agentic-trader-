import sys
import os
from pprint import pprint

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from backend.api.main import app

print("Inspecting API Routes:")
found = False
for route in app.routes:
    if hasattr(route, 'path') and '/analytics/metrics' in route.path:
        print(f"Found route: {route.path}")
        print(f"Response Model: {route.response_model}")
        found = True

if not found:
    print("Route /analytics/metrics NOT FOUND")
else:
    print("Route found.")
