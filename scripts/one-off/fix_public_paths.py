#!/usr/bin/env python3
"""Patch AuthMiddleware.PUBLIC_PATHS to add bitvavo-status"""

import os

file_path = "/app/backend/core/auth/middleware.py"

with open(file_path, "r") as f:
    content = f.read()

# Check if bitvavo-status is already in public paths
if "/api/v1/paper-trading/bitvavo-status" in content:
    print("bitvavo-status al publiek!")
    exit(0)

# Add bitvavo-status to PUBLIC_PATHS
old_text = '''PUBLIC_PATHS = {
        "/",
        "/health",
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/metrics",
        "/api/v1/auth/token",
    }'''

new_text = '''PUBLIC_PATHS = {
        "/",
        "/health",
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/metrics",
        "/api/v1/auth/token",
        "/api/v1/paper-trading/bitvavo-status",
    }'''

if old_text in content:
    content = content.replace(old_text, new_text)
    with open(file_path, "w") as f:
        f.write(content)
    print("PUBLIC_PATHS bijgewerkt!")
else:
    print("Kon pattern niet vinden")
    print("Zoeking...")
    if "PUBLIC_PATHS" in content:
        print("PUBLIC_PATHS gevonden, maar andere format")
        # Try to insert after the existing PUBLIC_PATHS set
        import re
        pattern = r'(PUBLIC_PATHS\s*=\s*\{[^}]+\})'
        match = re.search(pattern, content)
        if match:
            old_set = match.group(1)
            if "/api/v1/paper-trading/bitvavo-status" not in old_set:
                # Add the new path before the closing brace
                new_set = old_set.rstrip()[:-1].rstrip() + '\n        "/api/v1/paper-trading/bitvavo-status",\n    }'
                content = content.replace(old_set, new_set)
                with open(file_path, "w") as f:
                    f.write(content)
                print("PUBLIC_PATHS bijgewerkt via regex!")
