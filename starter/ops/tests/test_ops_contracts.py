"""Ops contract tests.

These tests assert that the operational artifacts under `starter/ops/`
are real, runnable procedures — not placeholders kept only to satisfy
a "file exists" check. AGENTS.md forbids weakening evidence or
security gates merely to make a demo pass, and a runbook that does
not say what to do in a real incident is the operational equivalent
of a gate that does not check.
"""

from __future__ import annotations

from pathlib import Path

import pytest

OPS_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = OPS_ROOT.parent.parent

MIN_RUNBOOK_BYTES = 400
MIN_CHECKLIST_BYTES = 200
MIN_K8S_MANIFEST_BYTES = 200


def _all_files(directory: Path) -> list[Path]:
    return sorted(p for p in directory.rglob("*") if p.is_file())


@pytest.mark.parametrize(
    "path",
    [p for p in _all_files(OPS_ROOT / "runbooks") if p.suffix == ".md"],
    ids=lambda p: str(p.relative_to(REPO_ROOT)),
)
def test_runbook_is_not_a_placeholder(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) >= MIN_RUNBOOK_BYTES, (
        f"{path.relative_to(REPO_ROOT)} is a {len(text)}-byte placeholder; "
        f"runbooks must describe real recovery steps."
    )
    assert text.count("\n") >= 5, (
        f"{path.relative_to(REPO_ROOT)} has too few lines; "
        f"a runbook must list symptoms, checks, and actions."
    )
    forbidden_placeholders = [
        "# DB Restore\n",
        "# Grobid Capacity\n",
        "# Rollback\n",
    ]
    for placeholder in forbidden_placeholders:
        assert text != placeholder, (
            f"{path.relative_to(REPO_ROOT)} is still a placeholder; "
            f"found forbidden body {placeholder!r}."
        )


def test_release_checklist_is_substantive() -> None:
    path = OPS_ROOT / "release" / "release-checklist.md"
    text = path.read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) >= MIN_CHECKLIST_BYTES, (
        f"release checklist is only {len(text)} bytes; must contain the "
        f"real gates: evidence quality, security, infra, and rollback."
    )


@pytest.mark.parametrize(
    "path",
    [p for p in _all_files(OPS_ROOT / "deploy" / "base") if p.suffix in {".yaml", ".yml"}],
    ids=lambda p: str(p.relative_to(REPO_ROOT)),
)
def test_k8s_manifest_has_real_spec(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) >= MIN_K8S_MANIFEST_BYTES, (
        f"{path.relative_to(REPO_ROOT)} is a {len(text)}-byte stub; "
        f"Kubernetes manifests must define the spec, and where applicable "
        f"the replicas, image, and resources of each workload."
    )
    assert "spec:" in text, f"{path.relative_to(REPO_ROOT)} missing 'spec:'"
    if "kind: Deployment" in text:
        for field in ("replicas:", "image:", "resources:"):
            assert field in text, (
                f"{path.relative_to(REPO_ROOT)} is a Deployment without {field}"
            )
    if "kind: NetworkPolicy" in text:
        assert "policyTypes:" in text, (
            f"{path.relative_to(REPO_ROOT)} is a NetworkPolicy without policyTypes"
        )
        assert "ingress" in text or "egress" in text, (
            f"{path.relative_to(REPO_ROOT)} is a NetworkPolicy without rules"
        )
    if "kind: PodDisruptionBudget" in text:
        assert "selector:" in text, (
            f"{path.relative_to(REPO_ROOT)} is a PodDisruptionBudget without selector"
        )
        assert "minAvailable:" in text or "maxUnavailable:" in text, (
            f"{path.relative_to(REPO_ROOT)} is a PodDisruptionBudget without a budget threshold"
        )


def test_load_test_is_more_than_a_print() -> None:
    path = OPS_ROOT / "load" / "analysis_load.py"
    text = path.read_text(encoding="utf-8")
    assert 'print("Running load test")' not in text, (
        "analysis_load.py is a placeholder; it must run real requests "
        "and record latency/throughput metrics."
    )
    assert "import httpx" in text or "import aiohttp" in text, (
        "analysis_load.py must use a real HTTP client."
    )
