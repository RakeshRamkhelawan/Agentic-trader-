#!/usr/bin/env python3
"""Inject config.js content inline into index.html"""

import os

html_path = "/usr/share/nginx/html/index.html"
config_path = "/usr/share/nginx/html/config.js"

# Read config.js
with open(config_path, "r") as f:
    config_content = f.read()

# Read index.html
with open(html_path, "r") as f:
    html_content = f.read()

# Replace external script with inline script
old_script = '<script src="./config.js"></script>'
new_script = f'<script>{config_content}</script>'

if old_script in html_content:
    html_content = html_content.replace(old_script, new_script)
    with open(html_path, "w") as f:
        f.write(html_content)
    print("Config geïnjecteerd als inline script!")
else:
    # Try with cache buster
    import re
    pattern = r'<script src="\./config\.js\?v=\d+"></script>'
    if re.search(pattern, html_content):
        html_content = re.sub(pattern, new_script, html_content)
        with open(html_path, "w") as f:
            f.write(html_content)
        print("Config geïnjecteerd als inline script (met cache-buster)!")
    else:
        print("Config script niet gevonden")
        print(f"HTML content: {html_content[:800]}")
