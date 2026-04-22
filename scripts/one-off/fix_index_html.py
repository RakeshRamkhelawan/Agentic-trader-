#!/usr/bin/env python3
"""Fix index.html to add cache-buster to config.js"""

file_path = "/usr/share/nginx/html/index.html"

with open(file_path, "r") as f:
    content = f.read()

# Replace config.js with config.js?v=timestamp
import time
timestamp = int(time.time())

old_script = '<script src="./config.js"></script>'
new_script = f'<script src="./config.js?v={timestamp}"></script>'

if old_script in content:
    content = content.replace(old_script, new_script)
    with open(file_path, "w") as f:
        f.write(content)
    print(f"index.html bijgewerkt met cache-buster: {new_script}")
else:
    print("Config script niet gevonden in verwachte format")
    print(f"Content: {content[:500]}")
