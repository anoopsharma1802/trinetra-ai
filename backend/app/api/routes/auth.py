import base64
import hashlib
import hmac
import json
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    operator_id: str
    access_key: str


def _sign(payload: str) -> str:
    return hmac.new(
        settings.auth_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def create_access_token(operator_id: str) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": operator_id, "exp": int(time.time()) + 28800}).encode()
    ).decode()
    return f"{payload}.{_sign(payload)}"


def verify_access_token(token: str) -> bool:
    try:
        payload, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(payload)):
            return False
        data = json.loads(base64.urlsafe_b64decode(payload).decode())
        return int(data["exp"]) > int(time.time())
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False


@router.post("/login")
def login(payload: LoginRequest):
    if (
        not hmac.compare_digest(payload.operator_id.strip().lower(), settings.admin_operator_id)
        or not hmac.compare_digest(payload.access_key, settings.admin_access_key)
    ):
        raise HTTPException(status_code=401, detail="Invalid command center credentials")

    return {
        "access_token": create_access_token(payload.operator_id.strip().lower()),
        "token_type": "bearer",
        "expires_in": 28800,
    }