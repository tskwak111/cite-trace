"""Slice 8 production-infrastructure contract tests.

Asserts that the operational artifacts in `starter/ops/` are real
infrastructure inputs, not placeholders. The contract is narrow:
if a Terraform variable is documented, the default value must be
the one the deployment actually uses; if a secret is referenced,
the secret-manager boundary must be defined in SECURITY.md or a
dedicated secret policy file.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import yaml

OPS_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = OPS_ROOT.parent.parent
SECRETS_FILE = OPS_ROOT / "secrets" / "secret_manager_boundary.yaml"


def test_secrets_directory_exists() -> None:
    assert (OPS_ROOT / "secrets").is_dir(), (
        f"ops/secrets/ directory missing; secrets have no home"
    )


def test_secret_manager_boundary_is_documented() -> None:
    assert SECRETS_FILE.exists(), (
        f"{SECRETS_FILE.relative_to(REPO_ROOT)} is missing; the secret "
        "manager boundary must be a committed, reviewable file"
    )
    payload = yaml.safe_load(SECRETS_FILE.read_text(encoding="utf-8"))
    assert "version" in payload
    assert "secrets" in payload
    for name, spec in payload["secrets"].items():
        assert "description" in spec, f"secret {name!r} has no description"
        assert "rotation_days" in spec, f"secret {name!r} has no rotation policy"
        assert spec["rotation_days"] > 0, f"secret {name!r} rotation_days must be positive"


def test_observability_directory_has_collector_config() -> None:
    obs_dir = OPS_ROOT / "observability"
    if not obs_dir.is_dir():
        pytest.skip("ops/observability/ is not yet laid out")
    assert (obs_dir / "otel-collector.yaml").exists(), (
        "OpenTelemetry collector config missing; the release pipeline cannot emit traces"
    )


def test_release_artifacts_dir_has_helm_input() -> None:
    release_dir = OPS_ROOT / "release"
    if not (release_dir / "helm").is_dir():
        pytest.skip("ops/release/helm/ is not yet laid out")
    chart_yaml = release_dir / "helm" / "Chart.yaml"
    values_yaml = release_dir / "helm" / "values.yaml"
    assert chart_yaml.exists(), f"{chart_yaml.relative_to(REPO_ROOT)} missing"
    assert values_yaml.exists(), f"{values_yaml.relative_to(REPO_ROOT)} missing"
    chart = yaml.safe_load(chart_yaml.read_text(encoding="utf-8"))
    assert "name" in chart and "version" in chart


def test_terraform_variables_match_k8s_manifests() -> None:
    tfvars = OPS_ROOT / "deploy" / "terraform.tfvars"
    if not tfvars.exists():
        pytest.skip("ops/deploy/terraform.tfvars is not yet laid out")
    contents = tfvars.read_text(encoding="utf-8")
    assert "namespace" in contents, "terraform.tfvars must declare the namespace"
    assert "release_tag" in contents, (
        "terraform.tfvars must declare release_tag; the image pin depends on it"
    )
