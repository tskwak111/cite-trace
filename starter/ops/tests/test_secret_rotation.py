"""Contract test: secret rotation enforcement (ADR-0015).

The committed secret_manager_boundary.yaml declares six
production secrets with explicit rotation_days values.
This test runs the checker with synthetic
CITETRACE_SECRET_AGE_<NAME> environment variables and
asserts the exit code matches the contract:

  - exit 0 when every secret is within its window;
  - exit 1 when at least one secret is overdue;
  - exit 2 when the script is run without the
    CITETRACE_SECRET_AGE_* environment (treated as a
    hard configuration error so the gate is never
    silently bypassed by an unset CI variable).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_secret_rotation.py"
BOUNDARY = REPO_ROOT / "starter" / "ops" / "policies" / "secret_manager_boundary.yaml"


def _run(ages: dict[str, str] | None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if ages is not None:
        for name, value in ages.items():
            env[f"CITETRACE_SECRET_AGE_{name.upper()}"] = value
    else:
        for key in list(env):
            if key.startswith("CITETRACE_SECRET_AGE_"):
                env.pop(key)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--boundary", str(BOUNDARY)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_every_secret_has_positive_rotation_days() -> None:
    import yaml

    boundary = yaml.safe_load(BOUNDARY.read_text(encoding="utf-8"))
    for name, spec in boundary["secrets"].items():
        assert "rotation_days" in spec, f"secret {name!r} has no rotation_days"
        assert spec["rotation_days"] > 0, (
            f"secret {name!r} has non-positive rotation_days "
            f"{spec['rotation_days']!r}"
        )


def test_passes_when_every_secret_is_within_window() -> None:
    import yaml

    boundary = yaml.safe_load(BOUNDARY.read_text(encoding="utf-8"))
    ages = {
        name: str(max(1, spec["rotation_days"] // 2))
        for name, spec in boundary["secrets"].items()
    }
    result = _run(ages)
    assert result.returncode == 0, (
        f"all secrets within window; expected exit 0; got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_fails_when_a_secret_is_overdue() -> None:
    import yaml

    boundary = yaml.safe_load(BOUNDARY.read_text(encoding="utf-8"))
    ages = {
        name: str(max(1, spec["rotation_days"] // 2))
        for name, spec in boundary["secrets"].items()
    }
    overdue_name = next(iter(boundary["secrets"]))
    ages[overdue_name] = str(boundary["secrets"][overdue_name]["rotation_days"] + 1)
    result = _run(ages)
    assert result.returncode == 1, (
        f"overdue secret must produce exit 1; got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert overdue_name in result.stdout or overdue_name in result.stderr


def test_fails_hard_when_environment_is_unset() -> None:
    result = _run(None)
    assert result.returncode == 2, (
        f"unset environment must produce exit 2 (hard configuration error); "
        f"got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
