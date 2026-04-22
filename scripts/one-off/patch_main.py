# Lees het bestand
with open('/app/backend/api/main.py', 'r') as f:
    content = f.read()

# Voeg de bitvavo-status toe aan de public paths
old_text = '"/api/v1/paper-trading/ws-url",'
new_text = '''"/api/v1/paper-trading/ws-url",
    "/api/v1/paper-trading/bitvavo-status",'''

if new_text not in content:
    content = content.replace(old_text, new_text)
    with open('/app/backend/api/main.py', 'w') as f:
        f.write(content)
    print("Toegevoegd!")
else:
    print("Bestaat al!")
