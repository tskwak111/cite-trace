# GROBID Capacity

GROBID is the third-party PDF parser that produces the TEI-XML
the rest of the pipeline depends on. It is deployed as a separate
service because it processes untrusted PDFs (per ADR-0001) and
because its runtime is JVM-based and not container-native.

This runbook is for incidents where GROBID is degraded, slow, or
fully unavailable. Because the rest of the pipeline cannot proceed
without a parse, this runbook is the highest-priority infrastructure
runbook in the on-call rotation.

## Symptoms

- The `parse_pipeline_age_seconds` P99 metric exceeds 600 seconds.
- The `grobid_5xx_rate` metric is above 0.5% over a 5-minute window.
- Workers in the parsing queue are stuck in `parse_requested` for
  more than 15 minutes.
- `grobid_oom_kills_total` is increasing.

## Pre-conditions

- PagerDuty acknowledgement by the on-call SRE.
- Read access to the GROBID Grafana dashboard
  (`https://grafana.internal/d/grobid`).

## Procedure

1. **Confirm the symptom.** Hit the GROBID health endpoint:
   `curl -fsS http://grobid:8070/api/isalive`
   If the response is 200, the issue is upstream (queue, network).
   If the response is 5xx, jump to step 3.

2. **Check queue depth.** `redis-cli LLEN citetrace:parse:queue`.
   If depth is below 50, the issue is not GROBID itself; treat as
   network or worker-pool exhaustion instead.

3. **Scale GROBID horizontally.** GROBID is stateful per request
   only; horizontal scaling is safe.
   `kubectl scale deploy/grobid --replicas=<current * 2> -n citetrace`
   then wait one minute and re-check the health endpoint.

4. **If scaling does not help, restart the GROBID JVM.** This is
   the equivalent of clearing the JVM heap; it loses in-flight parses.
   `kubectl rollout restart deploy/grobid -n citetrace` and confirm
   the new pods reach `Ready` state within two minutes.

5. **If restart does not help, fall back to the cached TEI store.**
   Set `GROBID_DEGRADED=true` on the worker environment. The worker
   will serve the most recent cached TEI for documents that have
   been parsed before, and will route new documents to the
   `parse:queue:degraded` queue which uses the lightweight
   `pypdf` fallback. **This degrades evidence quality; the change
   must be reverted within 24 hours** and a postmortem opened.

6. **If GROBID is fully down for more than 30 minutes,** pause
   new document ingest via
   `kubectl scale deploy/api --replicas=0 -n citetrace` and
   communicate the pause on the status page. The reader-side
   features keep working for previously parsed documents.

## Capacity planning

GROBID is sized for the contract in
`docs/00_MASTER_BLUEPRINT.md §12` (1–60 page documents, English,
born-digital). The current production baseline is
`2 replicas, 4 CPU, 8 GiB each`, sized for a 95th-percentile
parse time of 9 seconds. When the 95th-percentile exceeds 15
seconds, scale horizontally; when it exceeds 30 seconds, file a
capacity ticket for the next sprint planning.

## What this runbook does not cover

- Bypassing GROBID on accessibility grounds. The fallback chain
  is allowed only as a temporary degradation, never as a permanent
  shortcut. Any change that bypasses GROBID for a class of
  documents must be approved by the evidence-quality working
  group and recorded in an ADR.
- Paywall-bypass style fast paths. ADR-0006 forbids them and the
  pipeline does not expose a hook for them.
