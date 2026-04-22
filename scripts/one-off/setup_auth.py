#!/usr/bin/env python3
"""Setup proper authentication for local development."""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, '/app')

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Create password hash for admin user
admin_password = "admin123"
admin_hash = get_password_hash(admin_password)

print(f"Admin password hash: {admin_hash}")
print(f"\nUse these credentials:")
print(f"  Email: admin@agentic-trader.local")
print(f"  Password: {admin_password}")

# SQL to create/update user
sql = f"""
-- Create admin user with proper credentials
INSERT INTO users (id, email, tenant_id, password_hash, role, is_active, is_verified, created_at)
VALUES (
    gen_random_uuid(),
    'admin@agentic-trader.local',
    'tenant-local',
    '{admin_hash}',
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

print(f"\nSQL to execute:\n{sql}")

# Write SQL to file
with open('/tmp/setup_auth.sql', 'w') as f:
    f.write(sql)

print("\nSQL written to /tmp/setup_auth.sql")
