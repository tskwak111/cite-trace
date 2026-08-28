import uuid
from datetime import UTC, datetime, timedelta

import pytest

from citetrace_api.security.upload_tokens import (
    AssetViewToken,
    TokenExpiredError,
    TokenVerificationError,
    sign_asset_view_token,
    verify_asset_view_token,
)


def test_sign_and_verify_token() -> None:
    secret = "supersecretkey"
    token = AssetViewToken(
        actor_user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        nonce="randomnonce"
    )
    
    token_str = sign_asset_view_token(token, secret)
    verified_token = verify_asset_view_token(token_str, secret)
    
    assert verified_token.asset_id == token.asset_id
    assert verified_token.actor_user_id == token.actor_user_id
    assert verified_token.workspace_id == token.workspace_id
    assert verified_token.nonce == token.nonce

def test_expired_token() -> None:
    secret = "supersecretkey"
    token = AssetViewToken(
        actor_user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        expires_at=datetime.now(UTC) - timedelta(minutes=10),
        nonce="randomnonce"
    )
    
    token_str = sign_asset_view_token(token, secret)
    
    with pytest.raises(TokenExpiredError):
        verify_asset_view_token(token_str, secret)

def test_invalid_signature() -> None:
    secret = "supersecretkey"
    token = AssetViewToken(
        actor_user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        nonce="randomnonce"
    )
    
    token_str = sign_asset_view_token(token, secret)
    
    with pytest.raises(TokenVerificationError, match="Invalid signature"):
        verify_asset_view_token(token_str, "wrongsecret")
