"""Script to fix security_middleware.py."""
import re

src = open('backend/api/security_middleware.py', encoding='utf-8').read()

# Add import os if not present
if 'import os' not in src:
    src = 'import os\n\n' + src

# Remove unsafe-inline and unsafe-eval from CSP
src = src.replace("\"script-src 'self' 'unsafe-inline' 'unsafe-eval'; \"", "\"script-src 'self'; \"")
src = src.replace("\"style-src 'self' 'unsafe-inline'; \"", "\"style-src 'self'; \"")

# Make HSTS conditional
old_hsts = """        # HSTS (only in production)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )"""
new_hsts = """        # HSTS - only when SSL is explicitly enabled or ENVIRONMENT=production
        if (
            os.getenv("SSL_ENABLED", "false").lower() == "true"
            or os.getenv("ENVIRONMENT", "development") == "production"
        ):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )"""

src = src.replace(old_hsts, new_hsts)

with open('backend/api/security_middleware.py', 'w', encoding='utf-8') as f:
    f.write(src)

print('unsafe-inline removed:', 'unsafe-inline' not in src)
print('unsafe-eval removed:', 'unsafe-eval' not in src)
print('HSTS conditional:', 'SSL_ENABLED' in src)
print('import os present:', 'import os' in src)
