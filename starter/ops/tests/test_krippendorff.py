"""Contract test: Krippendorff's alpha for nominal and
interval scales.

The IAA tool reports Cohen's kappa for the four nominal
dimensions and Jaccard for the multi-label dimensions.
For ordinal / interval dimensions (e.g. the 1-5
usefulness scale on the rubric) the more informative
metric is Krippendorff's alpha, computed with the
appropriate interval metric.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "compute_iaa.py"


def _load():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("compute_iaa", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_alpha_nominal_perfect_agreement() -> None:
    module = _load()
    alpha = module.krippendorff_alpha_nominal(
        ["a", "b", "c", "a", "b"], ["a", "b", "c", "a", "b"]
    )
    assert alpha == 1.0, f"perfect agreement must produce alpha=1.0; got {alpha}"


def test_alpha_nominal_full_disagreement() -> None:
    module = _load()
    alpha = module.krippendorff_alpha_nominal(
        ["a", "a", "a", "a", "a"], ["b", "b", "b", "b", "b"]
    )
    assert alpha is not None and alpha < -0.5, (
        f"complete disagreement should produce a strongly negative alpha; "
        f"got {alpha}"
    )


def test_alpha_nominal_returns_none_for_too_few_values() -> None:
    module = _load()
    assert module.krippendorff_alpha_nominal(["a"], ["b"]) is None
    assert module.krippendorff_alpha_nominal([], []) is None


def test_alpha_interval_perfect_agreement() -> None:
    module = _load()
    alpha = module.krippendorff_alpha_interval(
        [1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 2.0, 3.0, 4.0, 5.0]
    )
    assert alpha == 1.0, f"perfect interval agreement must be 1.0; got {alpha}"


def test_alpha_interval_zero_variance() -> None:
    module = _load()
    alpha = module.krippendorff_alpha_interval([3.0, 3.0], [3.0, 3.0])
    assert alpha is None, "zero variance must yield None"


def test_alpha_interval_partial_agreement() -> None:
    module = _load()
    alpha = module.krippendorff_alpha_interval(
        [1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 2.0, 3.0, 4.0, 5.0]
    )
    assert alpha == 1.0
    alpha_partial = module.krippendorff_alpha_interval(
        [1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 3.0, 3.0, 4.0, 5.0]
    )
    assert 0.0 < alpha_partial < 1.0, (
        f"partial agreement should be in (0, 1); got {alpha_partial}"
    )
