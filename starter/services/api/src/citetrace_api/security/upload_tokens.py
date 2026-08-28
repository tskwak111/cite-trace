import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel


class AssetViewToken(BaseModel):
    actor_user_id: UUID
    workspace_id: UUID
    asset_id: UUID
    expires_at: datetime
    nonce: str

class TokenVerificationError(Exception):
    pass

class TokenExpiredError(TokenVerificationError):
    pass

def sign_asset_view_token(token: AssetViewToken, secret_key: str) -> str:
    payload = json.dumps({
        "actor_user_id": str(token.actor_user_id),
        "workspace_id": str(token.workspace_id),
        "asset_id": str(token.asset_id),
        "expires_at": token.expires_at.isoformat(),
        "nonce": token.nonce
    }, separators=(',', ':')).encode('utf-8')
    
    encoded_payload = base64.urlsafe_b64encode(payload).decode('utf-8').rstrip('=')
    
    signature = hmac.new(
        secret_key.encode('utf-8'),
        encoded_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"{encoded_payload}.{signature}"

def verify_asset_view_token(token_str: str, secret_key: str) -> AssetViewToken:
    try:
        encoded_payload, signature = token_str.rsplit('.', 1)
    except ValueError as e:
        raise TokenVerificationError("Invalid token format") from e
        
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        encoded_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        raise TokenVerificationError("Invalid signature")
        
    padded = encoded_payload + '=' * (4 - len(encoded_payload) % 4)
    try:
        payload_bytes = base64.urlsafe_b64decode(padded)
        payload_data = json.loads(payload_bytes)
        
        token = AssetViewToken(
            actor_user_id=UUID(payload_data["actor_user_id"]),
            workspace_id=UUID(payload_data["workspace_id"]),
            asset_id=UUID(payload_data["asset_id"]),
            expires_at=datetime.fromisoformat(payload_data["expires_at"]),
            nonce=payload_data["nonce"]
        )
    except Exception as e:
        raise TokenVerificationError(f"Invalid payload: {e}") from e
        
    if token.expires_at < datetime.now(UTC):
        raise TokenExpiredError("Token has expired")
        
    return token
