# push.py - CORRECTED VAPID Key Generator
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_vapid_keys():
    # Generate private key
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize private key (PEM format for server)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Serialize public key (uncompressed format for browser)
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # Base64 URL-safe encode public key (this is what browser needs)
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    return public_key_b64, private_key_pem

if __name__ == "__main__":
    print("=" * 60)
    print("Generating VAPID Keys for Myfi...")
    print("=" * 60)
    
    try:
        public_key, private_key = generate_vapid_keys()
        
        print("\n✅ Keys generated successfully!\n")
        print("PUBLIC KEY (for browser):")
        print(public_key)
        print(f"\nLength: {len(public_key)} characters")
        
        print("\n" + "=" * 60)
        print("Add these to your .env file:")
        print("=" * 60)
        print(f"\nVAPID_PUBLIC_KEY={public_key}")
        print(f"VAPID_PRIVATE_KEY='{private_key}'")
        print(f"VAPID_CLAIM_EMAIL=mailto:admin@myfi.co.ke")
        print("\n" + "=" * 60)
        print("\nIMPORTANT: The private key should be wrapped in quotes in .env")
        print("because it contains newlines.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure you have installed:")
        print("  pip install cryptography pywebpush")