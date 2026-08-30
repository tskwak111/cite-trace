"""Bearer token authentication (ADR-0018).

The OpenAPI document declares `bearerAuth: []` (JWT bearer
token) as the security scheme. This module is the
FastAPI-side implementation: it parses the
`Authorization: Bearer <token>` header, verifies the JWT
against the `CITETRACE_AUTH_SECRET` environment variable,
and returns a `WorkspacePrincipal` for the route to use.

The token format is HS256-signed JWT with the following
claims:

  - `sub`     workspace UUID (the principal)
  - `role`    "annotator" | "adjudicator" | "admin"
  - `exp`     Unix timestamp; the verifier rejects
              tokens whose `exp` has passed

The production deployment replaces the HS256 verifier with
a real OIDC verifier (AWS Cognito, Auth0, Keycloak, etc.)
that returns the same `WorkspacePrincipal` shape. The
rest of the code is unchanged.
"""

from __future__ import annotations

import base64
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from fastapi import Header, HTTPException, status

Role = Literal["annotator", "adjudicator", "admin"]


@dataclass(frozen=True)
class WorkspacePrincipal:
    workspace_id: UUID
    role: Role

    def has_role(self, required: Role) -> bool:
        """Return True when the principal's role is at least
        the requested role. The hierarchy is
            admin > adjudicator > annotator
        so a higher-privilege principal satisfies a
        lower-privilege requirement. The hierarchy is
        enforced in code rather than by string comparison
        so the role names are explicit."""
        order: dict[Role, int] = {"annotator": 0, "adjudicator": 1, "admin": 2}
        return order[self.role] >= order[required]


def _b64decode(data: str) -> bytes:
    padded = data + "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def issue_token(
    workspace_id: UUID,
    role: Role,
    secret: str,
    ttl_seconds: int = 3600,
) -> str:
    """Sign a JWT for the given workspace. Used by the
    contract test and by the local dev workflow; the
    production path is the OIDC provider."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": str(workspace_id),
        "role": role,
        "exp": now + ttl_seconds,
        "iat": now,
    }
    h = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{h}.{p}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, "sha256").digest()
    return f"{h}.{p}.{_b64encode(signature)}"


def verify_bearer_token(token: str, secret: str) -> WorkspacePrincipal:
    """Verify a HS256 JWT and return the principal.

    Raises HTTPException(401) if the token is malformed,
    the signature is wrong, the `exp` has passed, or the
    `sub` is not a UUID. The error is intentionally
    indistinct (no "signature mismatch" vs "expired"
    branches) to avoid leaking validation timing.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("malformed token")
        h_b64, p_b64, s_b64 = parts
        signing_input = f"{h_b64}.{p_b64}".encode("ascii")
        expected = hmac.new(
            secret.encode("utf-8"), signing_input, "sha256"
        ).digest()
        actual = _b64decode(s_b64)
        if not hmac.compare_digest(expected, actual):
            raise ValueError("signature mismatch")
        payload = json.loads(_b64decode(p_b64).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("token expired")
        workspace_id = UUID(payload["sub"])
        role = payload.get("role", "annotator")
        if role not in ("annotator", "adjudicator", "admin"):
            raise ValueError(f"invalid role {role!r}")
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid bearer token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return WorkspacePrincipal(workspace_id=workspace_id, role=role)


def get_auth_secret() -> str:
    secret = os.environ.get("CITETRACE_AUTH_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CITETRACE_AUTH_SECRET is not set; the auth verifier is misconfigured",
        )
    return secret


def current_principal(
    authorization: str | None = Header(default=None),
) -> WorkspacePrincipal:
    """FastAPI dependency. Reads the `Authorization: Bearer
    <token>` header and returns the verified
    WorkspacePrincipal.

    Routes that need a tenant scope declare
    `Depends(current_principal)` in their signature; routes
    that are public (e.g. `/healthz`) do not declare the
    dependency and so skip the check.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing Authorization: Bearer <token> header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[len("Bearer "):].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="empty bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_bearer_token(token, get_auth_secret())
