import pyseto
import os
# from paseto.protocol.version4 import Version4

# Generate a key for symmetric encryption
#key = Version4.generate_key()

# Generate a symmetric key manually
key_bytes = os.urandom(32)  # 32 bytes for a v4 local key
key = pyseto.Key.new(version=4, purpose="local", key=key_bytes)

# Create a Paseto instance
paseto_instance = pyseto.Paseto()

# Create a PASETO token
payload = {
    "user_id": 123,
    "role": "admin"
}
token = paseto_instance.encode(
    key=key,
    payload=payload)
print("Generated Token:", token)


key_bytes = os.urandom(32)  # 32 bytes for a v4 local key
key2 = pyseto.Key.new(version=4, purpose="local", key=key_bytes)

try:
    # Attempt to decode the token with a different key
    verified_payload = paseto_instance.decode(
        keys=[key, key2],
        token=token
    )
except Exception as e:
    print("Invalid signature error:", e)
    exit(1)

import json

# Decode the payload from bytes to a dictionary
decoded_payload = json.loads(verified_payload.payload.decode("utf-8"))

# Extract user_id from the decoded payload
user_id = decoded_payload.get("user_id")
print("User ID:", user_id)
