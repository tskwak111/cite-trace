"""Contract test: `helm lint` on the production chart exits 0.

This is the acceptance criterion for ADR-0014. The chart is
committed in `starter/ops/release/helm/` and the `make check`
target runs `helm lint` against it. The test re-runs the
same command and asserts the exit code is 0; if the chart
template or values drift into an invalid state, this test
fails first.

When `kubeconform` is also on PATH the test additionally
asserts that the rendered manifest is schema-valid
against the Kubernetes 1.30 JSON Schema. This catches
mistakes that `helm lint` accepts but the cluster
rejects (e.g. `envFrom.secretRef.key` is not a valid
field; the proper construct is `env.valueFrom.secretKeyRef`).

The test is skipped if `helm` is not on PATH so the test
suite still runs on machines without the Helm CLI.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CHART = REPO_ROOT / "starter" / "ops" / "release" / "helm"


def _helm_available() -> bool:
    return shutil.which("helm") is not None


def _kubeconform_available() -> bool:
    return shutil.which("kubeconform") is not None


@pytest.mark.skipif(not _helm_available(), reason="helm CLI is required")
def test_helm_lint_passes() -> None:
    result = subprocess.run(
        ["helm", "lint", str(CHART)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"helm lint must exit 0 per ADR-0014; got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.skipif(not _helm_available(), reason="helm CLI is required")
@pytest.mark.skipif(not _kubeconform_available(), reason="kubeconform is optional")
def test_rendered_manifest_passes_kubeconform_strict() -> None:
    """The rendered manifest must validate against the
    Kubernetes 1.30 JSON Schema in strict mode. This
    catches template errors that helm lint accepts but
    a real cluster would reject."""
    template = subprocess.run(
        ["helm", "template", "citetrace", str(CHART)],
        capture_output=True,
        text=True,
        check=True,
    )
    rendered = template.stdout
    check = subprocess.run(
        [
            "kubeconform",
            "-summary",
            "-strict",
            "-kubernetes-version",
            "1.30.0",
        ],
        input=rendered,
        capture_output=True,
        text=True,
        check=False,
    )
    assert check.returncode == 0, (
        f"kubeconform -strict must accept the rendered manifest; "
        f"got exit {check.returncode}\n"
        f"stdout: {check.stdout}\nstderr: {check.stderr}"
    )


@pytest.mark.skipif(not _helm_available(), reason="helm CLI is required")
def test_helm_chart_has_required_metadata() -> None:
    """The chart must declare name, version, appVersion, and
    type. A missing field would break `helm install` and
    `helm template`."""
    import yaml

    chart_yaml = CHART / "Chart.yaml"
    assert chart_yaml.exists(), f"{chart_yaml.relative_to(REPO_ROOT)} is missing"
    chart = yaml.safe_load(chart_yaml.read_text(encoding="utf-8"))
    for field in ("name", "version", "appVersion", "type"):
        assert field in chart, (
            f"Chart.yaml is missing the required field {field!r}; "
            f"got {sorted(chart.keys())}"
        )
    assert chart["type"] == "application", (
        f"chart type must be 'application'; got {chart['type']!r}"
    )


@pytest.mark.skipif(not _helm_available(), reason="helm CLI is required")
def test_helm_template_renders_expected_resources() -> None:
    """`helm template` with the default values must produce a
    non-empty manifest that includes the api, web, and
    worker Deployments. A template that silently renders an
    empty document is a real production failure mode.

    Per ADR-0014, this is the v1.9 chart: the Deployment
    templates pin the values contract. Service and
    ConfigMap templates are a v2 follow-up.
    """
    result = subprocess.run(
        ["helm", "template", "citetrace", str(CHART)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"helm template must succeed; got {result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    rendered = result.stdout
    assert "kind: Deployment" in rendered, (
        "rendered manifest is missing a Deployment; the chart "
        "template is incomplete"
    )
    deployment_count = rendered.count("kind: Deployment")
    assert deployment_count == 3, (
        f"rendered manifest has {deployment_count} Deployments; "
        f"the chart must produce exactly 3 (api, web, worker)"
    )
    for name in ("api", "web", "worker"):
        assert f"app: {name}\n" in rendered or f"app: {name}" in rendered, (
            f"rendered manifest is missing a workload with label app={name!r}"
        )
