# Analysis Stalled Runbook

Use this runbook when user-visible analyses are taking longer than the
SLO target (5 minutes for the alpha contract) without producing a
result. The pipeline is broken into independent stages; the goal of
this runbook is to identify which stage is stalled and unstick it.

## Symptoms

- The `analysis_pipeline_age_seconds` P95 metric is above 600.
- Analyses are in `parse_requested` or `retrieve_in_progress` for more
  than 15 minutes.
- The status page has not been updated; the user impact is the only
  signal.

## Pre-conditions

- PagerDuty acknowledgement by the on-call SRE.
- Access to the evidence-quality Grafana dashboard.

## Procedure

1. **Identify the stalled stage.** Open the analysis detail view for
   the most recent affected tenant and read the `current_stage` and
   `stage_entered_at` fields. If `stage_entered_at` is more than
   30 minutes in the past, this stage is the suspect.

2. **Parse stall.** If the current stage is `parse_requested`, jump
   to the GROBID capacity runbook. The parse stage is the most
   common failure point.

3. **Resolution stall.** If the current stage is `resolve_requested`
   or `resolve_in_progress`, check the per-provider latency:
   `SELECT provider, AVG(latency_ms) FROM resolution_metrics
   WHERE created_at > now() - interval '1 hour' GROUP BY provider`.
   A single provider above 30 seconds p95 explains most stalls. If
   the offending provider is a third-party (Crossref, OpenAlex,
   Semantic Scholar, Unpaywall), consult the provider-degraded
   runbook.

4. **Acquisition stall.** If the current stage is `acquire_requested`,
   check whether the access policy has changed. A new paywall or a
   recent takedown can leave workers retrying indefinitely. Inspect
   the `acquisition.outcome` distribution; a spike in
   `inaccessible_source` suggests the takedown-source runbook is
   the right next step.

5. **Retrieval stall.** If the current stage is `retrieve_in_progress`,
   check the vector index health. `SELECT COUNT(*) FROM chunks WHERE
   index_status != 'ready';` should be `0`; a non-zero number means
   an index rebuild is in progress and the stall is expected.

6. **Verification / explanation stall.** These stages are
   LLM-driven. A stall here usually means the model provider is
   timing out. Check the model gateway logs for `model_call_timeout`
   and switch the routing configuration to the fallback provider via
   `config/model-routing.yaml`. The change is hot-reloaded by the
   gateway; the verification stage resumes within 60 seconds.

7. **Calibration / audit stall.** These are CPU-bound and should
   not stall beyond a few minutes. A stall here is a code bug;
   collect the worker logs and escalate to the evidence-quality
   working group.

## Recovery

Once the offending stage is identified and the underlying cause is
addressed, the stalled analyses are re-queued by the worker restart
script. Do not manually re-queue analyses from the database; the
outbox pattern is the only safe way to resume a pipeline run, and
the worker manages it.

## Postmortem

Within 48 hours, write a postmortem that includes the stalled stage,
the underlying cause, the time-to-detection, the time-to-recovery,
and the tenants affected. The postmortem must include at least one
follow-up action that prevents the same stall class in the future.
