import sys

# Lees het huidige bestand
with open('/app/backend/api/paper_trading_api.py', 'r') as f:
    content = f.read()

# Nieuwe endpoint code
new_code = '''

# --- NEW: Bitvavo Status Endpoint ---
@router.get("/bitvavo-status")
async def get_bitvavo_status():
    """Get Bitvavo connection status and account balance."""
    try:
        import os
        has_credentials = bool(
            os.environ.get("BITVAVO_API_KEY") and os.environ.get("BITVAVO_API_SECRET")
        )

        if not has_credentials:
            return {
                "connected": False,
                "message": "Bitvavo API credentials not configured",
                "has_api_key": bool(os.environ.get("BITVAVO_API_KEY")),
                "has_api_secret": bool(os.environ.get("BITVAVO_API_SECRET")),
                "balance_eur": 0.0,
                "available_eur": 0.0,
            }

        from backend.execution.bitvavo_adapter import BitvavoAdapter
        adapter = BitvavoAdapter()
        if not await adapter.initialize():
            return {"connected": False, "error": "Failed to connect to Bitvavo"}

        balance = await adapter.fetch_balance()
        await adapter.close()

        eur_balance = balance.get("EUR", {}).get("free", 0)
        return {
            "connected": True,
            "balance_eur": float(eur_balance),
            "total_balance_eur": float(balance.get("EUR", {}).get("total", 0)),
            "can_trade_live": float(eur_balance) >= 5.0,
            "message": "Connected" if float(eur_balance) >= 5.0 else "Insufficient balance (need €5+)"
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}
'''

# Voeg toe aan het einde
content = content.rstrip() + new_code

# Schrijf terug
with open('/app/backend/api/paper_trading_api.py', 'w') as f:
    f.write(content)

print("Patch toegepast!")
