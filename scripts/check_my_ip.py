#!/usr/bin/env python3
"""
Script to check your current public IP address
Useful for whitelisting in exchange API settings
"""

import requests

def get_public_ip():
    """Get public IP address using multiple sources for reliability"""
    sources = [
        "https://api.ipify.org",
        "https://api.myip.com",
        "https://ifconfig.me/ip",
    ]
    
    for source in sources:
        try:
            response = requests.get(source, timeout=5)
            if response.status_code == 200:
                ip = response.text.strip()
                print(f"✅ Je huidige publieke IP adres is: {ip}")
                print(f"\nℹ️  Gebruik dit IP adres bij het aanmaken van je Bybit API key")
                print(f"   (als je specifieke IP restricties wilt instellen)")
                return ip
        except Exception as e:
            print(f"❌ Fout met {source}: {e}")
            continue
    
    print("❌ Kon publiek IP adres niet ophalen")
    return None

if __name__ == "__main__":
    print("🌐 Publiek IP adres opzoeken...\n")
    get_public_ip()
