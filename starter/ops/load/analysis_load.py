"""Analysis pipeline load test.

Runs a configurable number of paper analyses against a target base
URL and reports latency, throughput, and a per-stage timing
breakdown. Used by the capacity runbook and the SLO dashboard.

Usage:
    uv run --with httpx python -m ops.load.analysis_load \\
        --base-url https://staging.citetrace.example \\
        --concurrency 16 --duration 300 --api-key "$LOAD_KEY"

The load test is intentionally conservative on assertion: it always
exits with the metrics it observed, and a separate SLO check script
(not this one) decides whether the SLO is violated.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class Sample:
    started: float
    duration: float
    status: int
    stage_latencies: dict[str, float]


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    return statistics.quantiles(values, n=100, method="inclusive")[int(p) - 1]


async def _run_one(
    client: httpx.AsyncClient,
    base_url: str,
    payload: dict[str, object],
    api_key: str,
) -> Sample:
    headers = {"Authorization": f"Bearer {api_key}"}
    started = time.monotonic()
    try:
        response = await client.post(
            f"{base_url}/analyses",
            json=payload,
            headers=headers,
            timeout=httpx.Timeout(120.0, connect=10.0),
        )
        elapsed = time.monotonic() - started
        return Sample(
            started=started,
            duration=elapsed,
            status=response.status_code,
            stage_latencies=response.json().get("stage_durations_ms", {}),
        )
    except httpx.HTTPError:
        return Sample(
            started=started,
            duration=time.monotonic() - started,
            status=0,
            stage_latencies={},
        )


async def _load(
    base_url: str,
    concurrency: int,
    duration: int,
    api_key: str,
    payload: dict[str, object],
) -> list[Sample]:
    semaphore = asyncio.Semaphore(concurrency)
    samples: list[Sample] = []
    stop = time.monotonic() + duration

    async with httpx.AsyncClient() as client:
        async def worker() -> None:
            async with semaphore:
                while time.monotonic() < stop:
                    samples.append(await _run_one(client, base_url, payload, api_key))

        await asyncio.gather(*(worker() for _ in range(concurrency)))
    return samples


def _summarise(samples: list[Sample]) -> dict[str, object]:
    durations = sorted(s.duration for s in samples)
    statuses: dict[str, int] = {}
    for sample in samples:
        bucket = str(sample.status) if sample.status else "error"
        statuses[bucket] = statuses.get(bucket, 0) + 1
    stage_totals: dict[str, list[float]] = {}
    for sample in samples:
        for stage, value in sample.stage_latencies.items():
            stage_totals.setdefault(stage, []).append(float(value))
    stage_summary = {
        stage: {
            "p50_ms": _percentile(values, 50),
            "p95_ms": _percentile(values, 95),
            "p99_ms": _percentile(values, 99),
        }
        for stage, values in stage_totals.items()
    }
    return {
        "sample_count": len(samples),
        "throughput_rps": len(samples) / (sum(durations) / max(len(samples), 1) or 1),
        "latency_seconds": {
            "p50": _percentile(durations, 50),
            "p95": _percentile(durations, 95),
            "p99": _percentile(durations, 99),
        },
        "status_counts": statuses,
        "stage_p95_ms": stage_summary,
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--report", type=Path, default=Path("/tmp/analysis_load.json"))
    args = parser.parse_args()

    payload = {
        "paper_id": "load-test-fixture",
        "modes": ["understand"],
        "synthetic": True,
    }
    samples = await _load(
        args.base_url, args.concurrency, args.duration, args.api_key, payload
    )
    summary = _summarise(samples)
    args.report.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
