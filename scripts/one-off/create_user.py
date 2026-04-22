import bcrypt
import sys

# Generate password hash for 'admin123'
password = 'admin123'.encode('utf-8')
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password, salt)

print(f"Password hash: {hashed.decode('utf-8')}")
print(f"SQL: UPDATE users SET password_hash = '{hashed.decode('utf-8')}' WHERE email = 'tenant-dev@example.com';")
