
import os
import re
import sys

# Define sensitive patterns (Strict boundaries)
SENSITIVE_PATTERNS = [
    r"\bsk-[a-zA-Z0-9]{32,}\b",     # OpenAI/DeepSeek keys (Word boundary)
    r"\bAIza[0-9A-Za-z-_]{35}\b",   # Google API keys (Word boundary)
    r"\beyJ[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]*", # JWT (Must start with eyJ)
]

# Define safe patterns (exceptions)
SAFE_PATTERNS = [
    r"sk-proj-[a-zA-Z0-9]+", 
    r"sk-ant-api03-[a-zA-Z0-9]+",
]

# Define ignored directories (recursively skipped)
IGNORE_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", "mypy_cache", 
    "venv", ".venv", "node_modules", ".idea", ".vscode", ".ruff_cache",
    "htmlcov", "dist", "build", "site-packages",
    ".next", ".turbo", ".vercel", "out", "coverage" # Frontend/Next.js artifacts
}

# Define ignored filenames (exact match)
IGNORE_FILES = {
    ".env", ".env.local", ".env.test", ".env.example", 
    "security_scan.py", "poetry.lock", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", "Pipfile.lock", "requirements.txt", "uv.lock",
    "tsconfig.tsbuildinfo",
    "test_output.log", "test_output.txt", "debug_test_output.txt" # Log files
}

# Define allowed extensions (white-list)
SCAN_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", 
    ".json", ".md", ".yml", ".yaml", ".ini", ".conf", 
    ".sh", ".bat", ".ps1", ".txt", ".env"
}

def is_safe(match_text):
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, match_text):
            return True
    return False

def scan_file(filepath):
    """Scans a single file for sensitive patterns."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for pattern in SENSITIVE_PATTERNS:
                matches = re.finditer(pattern, content)
                for match in matches:
                    match_text = match.group(0)
                    if not is_safe(match_text):
                        # Context (cleanup newlines)
                        start = max(0, match.start() - 30)
                        end = min(len(content), match.end() + 30)
                        context = content[start:end].replace("\n", " ")
                        print(f"❌ [ALERT] Potential secret found in {filepath}: ...{context}...")
                        return True
    except Exception:
        pass
    return False

def main():
    print("🛡️  Starting Security Scan (Strict Mode + Ignored Dirs)...")
    found_secrets = False
    root_dir = os.getcwd()
    
    scanned_count = 0
    skipped_count = 0
    
    for root, dirs, files in os.walk(root_dir):
        # 1. Modify dirs in-place to prevent descent
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        # 2. Extra safety: Check if current root path contains any ignored dir
        # (Handles cases where os.walk might have descended before filter or race conditions)
        path_parts = root.split(os.sep)
        if any(part in IGNORE_DIRS for part in path_parts):
            continue

        for file in files:
            if file in IGNORE_FILES:
                continue
            
            _, ext = os.path.splitext(file)
            if ext not in SCAN_EXTENSIONS and ext != "": 
                if file not in ["Dockerfile", "Makefile", "Jenkinsfile"]:
                    continue

            filepath = os.path.join(root, file)
            if scan_file(filepath):
                found_secrets = True
            scanned_count += 1

    print(f"✅ Scanned {scanned_count} files.")
    
    if found_secrets:
        print("❌ SECURITY SCAN FAILED: Secrets detected!")
        sys.exit(1)
    else:
        print("✅ Security Scan Passed. No secrets found.")
        sys.exit(0)

if __name__ == "__main__":
    main()
