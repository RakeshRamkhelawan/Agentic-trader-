import sys
import os
import json

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Verify we can import from backend
try:
    from backend.api.main import app
except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)


def export_openapi():
    print("Generating OpenAPI schema...")
    openapi_data = app.openapi()
    output_path = os.path.join(project_root, "backend", "openapi.json")

    with open(output_path, "w") as f:
        json.dump(openapi_data, f, indent=2)
    print(f"OpenAPI spec exported to {output_path}")


if __name__ == "__main__":
    export_openapi()
