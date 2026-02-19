import os
import subprocess
import sys

import docker


def run_command(command, cwd=None):
    process = subprocess.run(
        command,
        shell=True,  # nosec B602 - Test script with controlled input
        capture_output=True,
        text=True,
        cwd=cwd,
        encoding="utf-8",
        errors="replace",
    )
    return process


def test_docker_build():
    print("🚀 Starting Docker Build Test (TDD)...")

    # 1. Build Image
    print("🔨 Building Docker image...")
    # Zorg dat we in de juiste directory zijn (project root)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dockerfile_path = os.path.join(
        project_root, "infrastructure", "docker", "Dockerfile"
    )

    # Check if Dockerfile exists
    if not os.path.exists(dockerfile_path):
        print(f"❌ Dockerfile not found at {dockerfile_path}")
        sys.exit(1)

    # Build command
    build_cmd = f"docker build -t agentic-trader:test -f {dockerfile_path} ."
    result = run_command(build_cmd, cwd=project_root)

    if result.returncode != 0:
        print("❌ Docker build failed!")
        print(result.stderr)
        sys.exit(1)

    print("✅ Docker build successful.")

    # 2. Check Image Size
    print("📏 Checking image size...")
    client = docker.from_env()
    try:
        image = client.images.get("agentic-trader:test")
        size_mb = image.attrs["Size"] / (1024 * 1024)
        print(f"ℹ️  Image Size: {size_mb:.2f} MB")

        if size_mb > 250:
            print(f"❌ Image size too large ({size_mb:.2f} MB > 250 MB).")
            # We failen hier niet hard in de Red Phase, maar wel in Green
            # Voor nu, laten we het script falen om 'Red' te simuleren als doel
            sys.exit(1)
        else:
            print("✅ Image size checks passed (< 250 MB).")

    except Exception as e:
        print(f"❌ Failed to inspect image: {e}")
        sys.exit(1)

    print("🎉 Test passed!")


if __name__ == "__main__":
    test_docker_build()
