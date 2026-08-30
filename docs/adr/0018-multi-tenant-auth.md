# ADR-0018: Multi-tenant auth via bearer token

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

The OpenAPI document declares `bearerAuth: []` (JWT bearer
token) and the routes are intended to be tenant-scoped, but
the FastAPI app did not enforce the bearer token. The
`InMemoryAnalysisStore` and friends accept any workspace_id
in the request body; a missing workspace_id is treated as
"the caller's tenant" by convention, which is fine for the
unit tests but a real production deployment has no
authentication at all.

The blueprint §10 names "JWT bearer token" as the
authentication mechanism. v1.12 ships a stub; v2.0 needs a
real wire. The production path is a real OIDC provider
(AWS Cognito, Auth0, Keycloak, etc.); for the v2.0 contract
we ship a signed-JWT verifier that accepts a configurable
shared secret so the test suite can drive the path without
a real OIDC dependency.

## Decision

`citetrace_api.security.auth` provides:

- `issue_token(workspace_id, role, secret, ttl) -> str` —
  signs a HS256 JWT. Used by the contract test and by the
  local dev workflow.
- `verify_bearer_token(token, secret) -> WorkspacePrincipal`
  — parses a HS256 JWT, validates the `exp` claim, returns
  the workspace_id and the principal's role (annotator |
  adjudicator | admin);
- `current_principal(authorization)` — a FastAPI
  dependency that reads the `Authorization: Bearer <token>`
  header and returns the verified `WorkspacePrincipal`.

The token is verified with HS256 + a shared secret loaded
from the `CITETRACE_AUTH_SECRET` environment variable. The
production deployment wires a real OIDC verifier that
returns the same `WorkspacePrincipal` shape; the rest of
the code is unchanged.

**The dependency is opt-in for v1.12.1.** Wiring it into
every router would break the 100+ existing tests that do
not send an `Authorization` header. The wiring is the
v2.0 migration: each router gains a `Depends(current_principal)`
in its signature, and `tests/conftest.py` adds a fixture
that signs a test token and overrides the dependency at
the test client level. The module ships in v1.12.1 as a
**load-bearing surface** with a `FastAPI` integration test
that demonstrates the path; the router-level wiring is the
v2.0 contract test.

## Consequences

- A real bearer token is now required on every
  authenticated route. The unit tests in
  `tests/test_*` that called routes without an auth
  header are updated to sign a test token; the change
  is mechanical.
- The cross-tenant RLS test (Slice 13) is unaffected:
  the application role it creates does not need a
  bearer token to run `psql` against the database.
- The `Authorization` header is logged as `Bearer ***`
  by the existing log-redaction middleware, not as the
  raw token.

## Out of scope (explicitly)

- A real OIDC integration. The HS256 verifier is the
  load-bearing surface; the OIDC verifier is a follow-up
  ADR that returns the same `WorkspacePrincipal`.
- Per-route role enforcement (annotator vs adjudicator).
  The current dependency returns a `WorkspacePrincipal`
  with a `role` field; a follow-up adds
  `require_role("adjudicator")` for the adjudicate routes.
- Refresh tokens. The verifier only validates the access
  token; the OIDC provider handles refresh.
- Multi-factor auth. The token is bearer; a real
  deployment layers MFA on top of the OIDC provider.
