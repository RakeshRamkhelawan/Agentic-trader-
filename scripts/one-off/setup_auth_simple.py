#!/usr/bin/env python3
"""Setup proper authentication for local development."""

# Pre-generated bcrypt hash for 'admin123' (truncated to 72 bytes)
# Using a known working hash
admin_hash = "$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Placeholder

# Let's use Python's hashlib for a simple SHA256 hash instead for now
import hashlib

password = "admin123"
sha256_hash = hashlib.sha256(password.encode()).hexdigest()

print(f"SHA256 hash: {sha256_hash}")

# SQL to create/update user with SHA256 hash (not recommended for production, but works for local dev)
sql = f"""
-- Create admin user with proper credentials
INSERT INTO users (id, email, tenant_id, password_hash, role, is_active, is_verified, created_at)
VALUES (
    gen_random_uuid(),
    'admin@agentic-trader.local',
    'tenant-local',
    '{sha256_hash}',
    'admin',
    true,
    true,
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    role = 'admin',
    is_active = true,
    is_verified = true;
"""

print(f"\nSQL:\n{sql}")

# Write SQL to file
with open('/tmp/setup_auth.sql', 'w') as f:
    f.write(sql)

print("\nSQL written to /tmp/setup_auth.sql")
