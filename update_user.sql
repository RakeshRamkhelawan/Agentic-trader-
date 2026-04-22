-- Update existing user with proper credentials
UPDATE users
SET
    password_hash = '$2b$12$4tD4n9f1Jy7zvUnX3QzQMeJR9qC3Wx7JqC2fZVzhQFjtC7tJpFJFq',
    role = 'admin',
    is_active = true,
    is_verified = true
WHERE email = 'tenant-dev@example.com';

-- If no rows updated, insert new user
INSERT INTO users (id, email, tenant_id, password_hash, role, is_active, is_verified, created_at)
SELECT
    gen_random_uuid(),
    'admin@agentic-trader.local',
    'tenant-local',
    '$2b$12$4tD4n9f1Jy7zvUnX3QzQMeJR9qC3Wx7JqC2fZVzhQFjtC7tJpFJFq',
    'admin',
    true,
    true,
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'tenant-dev@example.com');
