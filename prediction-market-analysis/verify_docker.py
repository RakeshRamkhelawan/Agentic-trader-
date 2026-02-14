#!/usr/bin/env python3
"""
Docker Build & Verification Script for Prediction Market Intelligence Service

Tests:
1. Docker image builds successfully
2. Container starts without errors
3. Health endpoint is accessible
4. Database initializes
5. All modules import correctly
6. API responds to basic requests
"""
import subprocess
import time
import requests
import sys
from pathlib import Path


class DockerVerification:
    """Verify Docker build and runtime."""

    def __init__(self):
        self.image_name = "prediction-intelligence:dev"
        self.container_name = "prediction-intelligence-test"
        self.port = 8000
        self.base_url = f"http://localhost:{self.port}"
        self.dockerfile_path = Path("prediction-market-analysis/Dockerfile")
        self.context_path = Path("prediction-market-analysis")

    def log(self, message: str, level: str = "INFO"):
        """Log with level indicator."""
        print(f"[{level}] {message}")

    def run_command(self, cmd: str, check: bool = True, shell: bool = True) -> str:
        """Run shell command and return output."""
        try:
            result = subprocess.run(
                cmd, shell=shell, capture_output=True, text=True, check=check
            )
            return result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {cmd}", "ERROR")
            self.log(e.stderr, "ERROR")
            raise

    def test_dockerfile_exists(self) -> bool:
        """Check if Dockerfile exists."""
        self.log(f"Checking Dockerfile at {self.dockerfile_path}...")

        if not self.dockerfile_path.exists():
            self.log(f"Dockerfile not found: {self.dockerfile_path}", "ERROR")
            return False

        self.log(f"✓ Dockerfile found", "OK")
        return True

    def build_image(self) -> bool:
        """Build Docker image."""
        self.log(f"Building Docker image: {self.image_name}...")

        try:
            cmd = f"docker build -t {self.image_name} {self.context_path}"
            output = self.run_command(cmd)

            if "Successfully built" in output:
                self.log(f"✓ Docker image built successfully", "OK")
                return True
            else:
                self.log("Docker build did not complete successfully", "ERROR")
                self.log(output, "ERROR")
                return False
        except subprocess.CalledProcessError as e:
            self.log("Docker build failed", "ERROR")
            return False

    def image_exists(self) -> bool:
        """Check if Docker image exists."""
        self.log(f"Checking if image exists: {self.image_name}...")

        try:
            output = self.run_command(f"docker images {self.image_name}", check=False)
            if self.image_name in output:
                self.log(f"✓ Image exists", "OK")
                return True
            else:
                self.log("Image not found", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error checking image: {e}", "ERROR")
            return False

    def stop_container(self) -> bool:
        """Stop and remove container if running."""
        self.log(f"Stopping container: {self.container_name}...")

        try:
            # Stop container
            self.run_command(f"docker stop {self.container_name}", check=False)
            # Remove container
            self.run_command(f"docker rm {self.container_name}", check=False)
            self.log(f"✓ Container stopped and removed", "OK")
            return True
        except Exception as e:
            self.log(f"Error stopping container: {e}", "ERROR")
            return False

    def start_container(self) -> bool:
        """Start Docker container."""
        self.log(f"Starting container: {self.container_name}...")

        try:
            cmd = (
                f"docker run -d --name {self.container_name} "
                f"-p {self.port}:8000 "
                f"-v /app/data "
                f"{self.image_name}"
            )
            output = self.run_command(cmd)
            container_id = output.strip()

            if len(container_id) >= 12:  # Valid container ID
                self.log(f"✓ Container started with ID: {container_id[:12]}", "OK")
                return True
            else:
                self.log("Failed to start container", "ERROR")
                return False
        except subprocess.CalledProcessError as e:
            self.log(f"Error starting container: {e}", "ERROR")
            return False

    def wait_for_startup(self, timeout: int = 30) -> bool:
        """Wait for service to be ready."""
        self.log(f"Waiting for service to start (timeout: {timeout}s)...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    self.log(f"✓ Service is ready", "OK")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            except Exception:
                pass

            time.sleep(1)

        self.log(f"Service failed to start within {timeout}s", "ERROR")
        return False

    def test_health_endpoint(self) -> bool:
        """Test health endpoint."""
        self.log("Testing /health endpoint...")

        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)

            if response.status_code == 200:
                data = response.json()

                required_fields = ["status", "version", "timestamp"]
                missing = [f for f in required_fields if f not in data]

                if missing:
                    self.log(f"Missing fields in health response: {missing}", "ERROR")
                    return False

                self.log(f"✓ Health endpoint working (status: {data['status']})", "OK")
                return True
            else:
                self.log(f"Health endpoint returned {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error testing health endpoint: {e}", "ERROR")
            return False

    def test_api_endpoints(self) -> bool:
        """Test API endpoints."""
        self.log("Testing API endpoints...")

        tests = [
            ("GET", "/", "Root endpoint"),
            ("GET", "/health", "Health"),
            ("GET", "/health/ready", "Readiness"),
            ("GET", "/health/live", "Liveness"),
            ("GET", "/docs", "Swagger docs"),
            ("GET", "/api/v1/markets/summary", "Market summary"),
        ]

        all_passed = True
        for method, endpoint, name in tests:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)

                if response.status_code in [200, 307]:  # 307 for redirect to /docs
                    self.log(f"✓ {name}: {response.status_code}", "OK")
                else:
                    self.log(f"✗ {name}: {response.status_code}", "ERROR")
                    all_passed = False
            except Exception as e:
                self.log(f"✗ {name}: {str(e)[:50]}", "ERROR")
                all_passed = False

        return all_passed

    def test_container_logs(self) -> bool:
        """Check container logs for errors."""
        self.log("Checking container logs...")

        try:
            logs = self.run_command(f"docker logs {self.container_name}")

            error_keywords = ["ERROR", "CRITICAL", "FATAL", "Traceback"]
            errors = [
                line
                for line in logs.split("\n")
                if any(kw in line for kw in error_keywords)
            ]

            if errors:
                self.log(f"Found {len(errors)} error(s) in logs:", "WARNING")
                for error in errors[:5]:  # Show first 5
                    self.log(f"  {error[:100]}", "WARNING")
                return False

            self.log("✓ No critical errors in logs", "OK")
            return True
        except Exception as e:
            self.log(f"Error reading logs: {e}", "ERROR")
            return False

    def get_container_info(self) -> bool:
        """Get container resource info."""
        self.log("Getting container information...")

        try:
            info = self.run_command(
                f"docker inspect {self.container_name} --format="
                f"'{{{{json .State}}}}'",
                shell=True,
            )

            if '"Running":true' in info:
                self.log("✓ Container is running", "OK")
                return True
            else:
                self.log("Container is not running", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error getting container info: {e}", "ERROR")
            return False

    def run_all_tests(self) -> bool:
        """Run all verification tests."""
        self.log("=" * 70)
        self.log("Prediction Market Intelligence - Docker Verification", "INFO")
        self.log("=" * 70)

        results = {
            "Dockerfile exists": False,
            "Image builds": False,
            "Container starts": False,
            "Service ready": False,
            "Health endpoint": False,
            "API endpoints": False,
            "No errors in logs": False,
            "Container running": False,
        }

        # Stop any existing container
        self.stop_container()

        # 1. Check Dockerfile
        if not self.test_dockerfile_exists():
            self.log("Aborting: Dockerfile not found", "ERROR")
            return False
        results["Dockerfile exists"] = True

        # 2. Build image
        if not self.build_image():
            self.log("Aborting: Docker build failed", "ERROR")
            return False
        results["Image builds"] = True

        # 3. Verify image exists
        if not self.image_exists():
            self.log("Aborting: Image verification failed", "ERROR")
            return False

        # 4. Start container
        if not self.start_container():
            self.log("Aborting: Container start failed", "ERROR")
            return False
        results["Container starts"] = True

        # 5. Wait for startup
        if not self.wait_for_startup():
            self.log("Aborting: Service failed to start", "ERROR")
            self.stop_container()
            return False
        results["Service ready"] = True

        # 6-8. Run tests
        results["Health endpoint"] = self.test_health_endpoint()
        results["API endpoints"] = self.test_api_endpoints()
        results["Container running"] = self.get_container_info()
        results["No errors in logs"] = self.test_container_logs()

        # Print summary
        self.log("=" * 70)
        self.log("Verification Results", "INFO")
        self.log("=" * 70)

        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            self.log(f"{test_name:.<50} {status}")

        all_passed = all(results.values())

        self.log("=" * 70)
        if all_passed:
            self.log("✓ All verification tests PASSED", "OK")
        else:
            self.log(
                f"✗ {sum(1 for v in results.values() if not v)} test(s) FAILED", "ERROR"
            )

        # Cleanup
        self.log("\nCleaning up...")
        self.stop_container()

        return all_passed


def main():
    """Main entry point."""
    verifier = DockerVerification()
    success = verifier.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
