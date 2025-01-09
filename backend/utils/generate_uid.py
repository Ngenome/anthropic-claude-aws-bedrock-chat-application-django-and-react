import hashlib
import base64
import uuid

def generate_uid():
    # Generate a UUID
    uid = str(uuid.uuid4())

    # Hash the UUID using SHA-256
    hashed_uid = hashlib.sha256(uid.encode()).digest()

    # Encode the hashed UUID in base64
    short_uid = base64.urlsafe_b64encode(hashed_uid)[:8].decode()

    return short_uid

