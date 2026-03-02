import os
import subprocess
import sys
import time

import requests


def start_server():
    print("Starting Uvicorn server...")
    # Using relative path from root
    # set PYTHONPATH=. ensures backend is discoverable
    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    # Path to venv python
    python_exe = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")

    # Run uvicorn as a module using the venv python
    cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "backend.api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]

    # Open log file
    with open("startup.log", "w") as f:
        process = subprocess.Popen(cmd, stdout=f, stderr=f, env=env)
        return process


def verify_server():
    url = "http://localhost:8000/health"
    max_retries = 10
    print(f"Verifying server at {url}...")
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"Server is UP! Response: {response.json()}")
                return True
        except requests.exceptions.RequestException:
            print(f"Retrying... ({i+1}/{max_retries})")
            time.sleep(3)
    return False


if __name__ == "__main__":
    process = None
    try:
        process = start_server()
        # Give it a bit more time to initialize (lifespan can be slow)
        time.sleep(10)

        if verify_server():
            print("Verification SUCCESSFUL")
            # Keep it running for a few more seconds to collect logs
            time.sleep(5)
            sys.exit(0)
        else:
            print("Verification FAILED")
            # Read logs
            with open("startup.log", "r") as f:
                print("--- Startup Logs ---")
                print(f.read())
            sys.exit(1)
    finally:
        if process:
            print("Stopping server process...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
