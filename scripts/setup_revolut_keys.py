import base64
import sys
import os

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("De library 'cryptography' is niet gevonden.")
    print("Installeer deze eerst met het commando:")
    print("pip install cryptography")
    sys.exit(1)

def generate_keys():
    print("--- Revolut X API Key Generator ---\n")

    # 1. Genereer de Private Key
    private_key = ed25519.Ed25519PrivateKey.generate()

    # 2. Zet om naar bytes voor opslag (Private Key)
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # 3. Genereer de Public Key (Deze moet naar Revolut)
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Decodeer naar string voor weergave
    public_key_str = public_bytes.decode('utf-8')
    
    # Sla de private key op
    filename = "revolut_private.pem"
    file_path = os.path.join(os.getcwd(), filename) # Absoluut pad
    
    try:
        with open(file_path, "wb") as f:
            f.write(private_bytes)
        print(f"SUCCES! Je private key is veilig opgeslagen in: {file_path}")
        print("WAARSCHUWING: Deel dit bestand met niemand en commit het NIET naar Git.\n")
    except IOError as e:
        print(f"FOUT: Kon de private key niet opslaan in {file_path}. Controleer schrijfrechten. Details: {e}")
        sys.exit(1)

    print("--- KOPIEER ONDERSTAANDE REGELS NAAR REVOLUT ---")
    print("(Kopieer alles, inclusief -----BEGIN... en ...END-----")
    print("")
    print(public_key_str)
    print("--------------------------------------------------")

if __name__ == "__main__":
    generate_keys()
