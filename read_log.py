try:
    with open("rls_debug.log", "r", encoding="utf-8", errors="replace") as f:
        print(f.read())
except Exception as e:
    try:
        with open("rls_debug.log", "r", encoding="cp1252", errors="replace") as f:
            print(f.read())
    except Exception as e:
        print(f"Error reading log: {e}")
