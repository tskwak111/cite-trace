#!/usr/bin/env python3
"""Check that every declared secret is within its rotation
window (ADR-0015).

Reads the secret_manager_boundary.yaml contract and asserts,
for each declared secret, that the synthetic
CITETRACE_SECRET_AGE_<NAME> environment variable reports
an age below the declared `rotation_days`.

Exit codes:
  0 — every secret is within its window
  1 — at least one secret is overdue
  2 — the script is run without the CITETRACE_SECRET_AGE_*
      environment variables (treated as a hard configuration
      error so the gate is never silently bypassed)

The script is **synthetic** in CI: the production deployment
populates the CITETRACE_SECRET_AGE_* variables from the real
secret manager. The contract test in
`starter/ops/tests/test_secret_rotation.py` exercises the
script with a temporary boundary file and synthetic ages.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml is required; install with: uv pip install pyyaml", file=sys.stderr)
    raise

ENV_PREFIX = "CITETRACE_SECRET_AGE_"


def _read_boundary(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _check(boundary: dict, env: dict) -> tuple[int, list[str]]:
    failures: list[str] = []
    seen_any = False
    for name, spec in boundary.get("secrets", {}).items():
        rotation = spec.get("rotation_days")
        if not isinstance(rotation, int) or rotation <= 0:
            failures.append(f"{name}: rotation_days must be a positive integer")
            continue
        env_key = f"{ENV_PREFIX}{name.upper()}"
        age_raw = env.get(env_key)
        if age_raw is None or age_raw == "":
            continue
        try:
            age = int(age_raw)
        except ValueError:
            failures.append(f"{name}: {env_key}={age_raw!r} is not an integer")
            continue
        seen_any = True
        if age < 0:
            failures.append(f"{name}: age={age} is negative")
            continue
        if age >= rotation:
            failures.append(
                f"{name}: age={age}d >= rotation_days={rotation}d (overdue)"
            )
    if not seen_any:
        return 2, [
            f"no {ENV_PREFIX}<NAME> environment variables were set; "
            f"the gate is refused rather than silently passing"
        ]
    return (1 if failures else 0), failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--boundary",
        type=Path,
        default=Path("starter/ops/policies/secret_manager_boundary.yaml"),
    )
    args = parser.parse_args()
    if not args.boundary.exists():
        print(f"boundary file not found: {args.boundary}", file=sys.stderr)
        return 2
    boundary = _read_boundary(args.boundary)
    code, failures = _check(boundary, os.environ)
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
    if code == 0:
        print("all secrets within their rotation window")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
