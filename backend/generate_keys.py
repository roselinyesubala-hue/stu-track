
import base64
import os
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_vapid_keys():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    private_bytes = private_key.private_numbers().private_value.to_bytes(32, byteorder='big')
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    private_key_base64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
    public_key_base64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')

    return private_key_base64, public_key_base64

if __name__ == "__main__":
    priv, pub = generate_vapid_keys()
    with open("vapid_keys.txt", "w") as f:
        f.write(f"PRIVATE_KEY: {priv}\n")
        f.write(f"PUBLIC_KEY: {pub}\n")
    print(f"PRIVATE_KEY: {priv}")
    print(f"PUBLIC_KEY: {pub}")
