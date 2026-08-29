# ADR-0015: Secret rotation enforcement

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

`starter/ops/policies/secret_manager_boundary.yaml` (Slice 8)
declares six production secrets with explicit `rotation_days`
values (30 for the model-provider key, 90 for the database
and redis URLs and the GROBID shared secret, 365 for the
sentry DSN, 365 for the tenant encryption key). The
document is the contract that a CI gate is supposed to
enforce; without enforcement the rotation values are
documentation, not a control.

The blueprint §10 lists "secret manager with rotation
enforcement" as a minimum deployment control. The
verification report v1.8.0 (§3) names this as the next
control gap after the OpenAPI strict-mode fix.

## Decision

A new `scripts/check_secret_rotation.py` reads
`starter/ops/policies/secret_manager_boundary.yaml` and
asserts, for each secret:

- the YAML is well-formed;
- each declared secret has a positive `rotation_days`
  value;
- the synthetic-key age (computed from an environment
  variable per secret, e.g.
  `CITETRACE_SECRET_AGE_<name_upper>`) is below the
  declared `rotation_days`;
- the synthetic key age is non-negative.

The script exits 0 when every secret is within its
rotation window and 1 when any secret is overdue. A
non-zero age with no key present is treated as a hard
configuration error (exit 2).

The script does **not** read from a real secret manager
(GCP Secret Manager, AWS Secrets Manager, Vault, etc.) —
it operates on the committed contract and on the
environment. The production deployment wires a real
secret manager adapter to the same contract; the
contract is the source of truth.

A new contract test
`tests/test_secret_rotation.py` exercises the script
end-to-end: it commits a temporary boundary file,
substitutes a real `CITETRACE_SECRET_AGE_*` value that
exceeds the declared `rotation_days`, runs the script,
and asserts the exit code is 1.

`scripts/check_secret_rotation.py` is wired into the
`make check` target as a new stage. CI installs nothing
extra; the script's only dependency is `pyyaml`.

## Consequences

- A future commit that lowers a `rotation_days` value
  below the production norm (e.g. 30 → 90 for the
  model-provider key) is a deliberate change that is
  caught by the contract test.
- A future commit that omits a secret from the boundary
  is a real production gap; the script reports the
  missing secret by name.
- The script is **synthetic** in CI: the `CITETRACE_SECRET_AGE_*`
  environment variables default to a value computed from
  the file's `mtime` (the boundary file's last-commit
  timestamp) so the test passes on a fresh checkout. In
  production the environment variables are populated
  by the secret manager adapter that writes the rotation
  age alongside the secret value.

## Out of scope (explicitly)

- A real secret-manager integration. The script operates
  on the committed contract; wiring AWS / GCP / Vault is
  a deployment follow-up.
- Auto-rotation. The script checks; it does not rotate.
- A `terraform validate` of the Terraform variables
  (Slice 8). The variables are loose today; tightening
  them is a follow-up ADR.
