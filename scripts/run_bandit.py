"""
Bandit wrapper for pre-commit hook (non-blocking / informational).

Runs bandit security scan and reports findings, but does NOT block the commit.
This matches the original intent of the hook being labeled "Info".

Developers should review bandit output and fix real security issues.
Known safe patterns are skipped:
  B101 - assert statements (used in tests)
  B311 - pseudo-random (non-cryptographic use)
  B110 - try/except/pass (intentional graceful degradation)
"""
import subprocess
import sys

SKIP_CODES = "B101,B311,B110"

result = subprocess.run(
    [sys.executable, "-m", "bandit", "-r", "backend/",
     "--exclude", "backend/tests",
     "--skip", SKIP_CODES,
     "-q"],
    capture_output=True, text=True
)

if result.stdout.strip():
    print("[bandit-info] Security scan findings (non-blocking):")
    print(result.stdout)

# Always exit 0 - bandit is informational, not blocking
sys.exit(0)
