from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from typing import Any

from fastapi import HTTPException, status


def _secret_key() -> bytes:
    """
    Return secret key bytes for token signing.

    NOTE: For production you MUST set BACKEND_SECRET_KEY. If not set, we fall back to a process-local
    random key which invalidates tokens on restart (acceptable for demo/dev).
    """
    key = os.getenv("BACKEND_SECRET_KEY")
    if key:
        return key.encode("utf-8")
    return os.urandom(32)


_SECRET = _secret_key()


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 (no external deps)."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return base64.urlsafe_b64encode(salt + dk).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against stored hash."""
    try:
        raw = base64.urlsafe_b64decode(password_hash.encode("utf-8"))
        salt, dk = raw[:16], raw[16:]
        test = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(test, dk)
    except Exception:
        return False


def create_access_token(payload: dict[str, Any], expires_in_seconds: int = 60 * 60 * 24 * 7) -> str:
    """
    Create a compact signed token (not JWT) to avoid extra dependencies.

    Token format: base64url(payload_json).base64url(signature)
    Where signature = HMAC-SHA256(secret, payload_bytes).
    """
    # very small custom encoding to keep deps minimal
    import json

    data = payload.copy()
    data["exp"] = int(time.time()) + int(expires_in_seconds)
    payload_bytes = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    sig = hmac.new(_SECRET, payload_bytes, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    return f"{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a token.

    Raises HTTPException(401) if invalid/expired.
    """
    import json

    try:
        payload_b64, sig_b64 = token.split(".", 1)
        # restore padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + "==")
        sig = base64.urlsafe_b64decode(sig_b64 + "==")
        expected = hmac.new(_SECRET, payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        payload = json.loads(payload_bytes.decode("utf-8"))
        exp = int(payload.get("exp", 0))
        if exp <= int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
