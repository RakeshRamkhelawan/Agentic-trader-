#!/usr/bin/env python3
"""Create a user with a pre-generated bcrypt hash."""

# Pre-generated bcrypt hash for 'admin123' using a compatible version
# This hash was generated with: python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())"
admin_hash = "$2b$12$4tD4n9f1Jy7zvUnX3QzQMeJR9qC3Wx7JqC2fZVzhQFjtC7tJpFJFq"

print(f"Using bcrypt hash: {admin_hash}")

# SQL to create/update user
sql = f"""
-- Delete existing dev user and create proper admin
DELETE FROM users WHERE email = 'tenant-dev@example.com';

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
);
"""

print(f"\nSQL:\n{sql}")

# Write SQL to file
with open('/tmp/setup_auth.sql', 'w') as f:
    f.write(sql)

print("\n✅ SQL written to /tmp/setup_auth.sql")
print("\n" + "="*60)
print("LOGIN CREDENTIALS:")
print("="*60)
print("  Email: admin@agentic-trader.local")
print("  Password: admin123")
print("="*60)
