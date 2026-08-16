import base64
import hashlib
import hmac
import os
import secrets
import time

from fastapi import HTTPException, Request, Response


COOKIE_NAME = os.getenv("ADMIN_COOKIE_NAME", "jain_ai_admin_session")
SESSION_SECONDS = int(os.getenv("ADMIN_SESSION_SECONDS", "28800"))


def _session_secret() -> str:
    value = os.getenv("ADMIN_SESSION_SECRET", "").strip()
    if not value:
        raise RuntimeError("ADMIN_SESSION_SECRET is not configured")
    return value


def _sign(payload: str) -> str:
    return hmac.new(
        _session_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_session_token() -> str:
    issued_at = str(int(time.time()))
    nonce = secrets.token_urlsafe(16)
    payload = f"{issued_at}.{nonce}"
    signed = f"{payload}.{_sign(payload)}"
    return base64.urlsafe_b64encode(signed.encode("utf-8")).decode("ascii")


def verify_session_token(token: str | None) -> bool:
    if not token:
        return False

    try:
        decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        issued_at, nonce, signature = decoded.split(".", 2)
        payload = f"{issued_at}.{nonce}"

        if not hmac.compare_digest(signature, _sign(payload)):
            return False

        if int(time.time()) - int(issued_at) > SESSION_SECONDS:
            return False

        return True
    except Exception:
        return False


def verify_password(password: str) -> bool:
    expected = os.getenv("ADMIN_PASSWORD", "")
    if not expected:
        raise RuntimeError("ADMIN_PASSWORD is not configured")
    return hmac.compare_digest(password, expected)


def set_admin_cookie(response: Response, token: str) -> None:
    secure = os.getenv("ADMIN_COOKIE_SECURE", "false").lower() == "true"
    same_site = os.getenv("ADMIN_COOKIE_SAMESITE", "lax").lower()

    if same_site not in {"lax", "strict", "none"}:
        same_site = "lax"

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=secure,
        samesite=same_site,
        path="/",
    )


def clear_admin_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
    )


def require_admin(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not verify_session_token(token):
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required",
        )
    return True
