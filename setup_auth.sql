
-- Delete existing dev user and create proper admin
DELETE FROM users WHERE email = 'tenant-dev@example.com';

-- Create admin user with proper credentials
INSERT INTO users (id, email, tenant_id, password_hash, role, is_active, is_verified, created_at)
VALUES (
    gen_random_uuid(),
    'admin@agentic-trader.local',
    'tenant-local',
    '$2b$12$4tD4n9f1Jy7zvUnX3QzQMeJR9qC3Wx7JqC2fZVzhQFjtC7tJpFJFq',
    'admin',
    true,
    true,
    NOW()
);
