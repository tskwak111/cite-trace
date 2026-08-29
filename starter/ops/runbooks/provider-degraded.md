# Provider Degraded Runbook

This runbook covers incidents where an external provider is
degraded: high latency, elevated error rate, partial outage, or a
content-policy change that causes rejections. The current set of
external providers in scope is:

- LLM providers (OpenAI, Anthropic, Google, etc.) configured in
  `config/model-routing.yaml`.
- Reference resolution providers (Crossref, OpenAlex, Semantic
  Scholar, Unpaywall).
- GROBID (covered by the GROBID capacity runbook; do not use this
  runbook for parser issues).
- Source acquisition providers (publisher APIs, arXiv, PMC).

## Symptoms

- Per-provider latency p95 is more than 3x the 7-day baseline.
- The provider's status page reports an incident (open it; do not
  rely on a third-party status aggregator).
- The model gateway emits `model_call_timeout` or
  `model_rejected_for_policy` at more than 1% of calls.
- Crossref/OpenAlex/Semantic Scholar/Unpaywall response rate is
  below 80% over a 5-minute window.

## Pre-conditions

- PagerDuty acknowledgement by the on-call SRE.
- Read access to the per-provider dashboard and the model gateway
  metrics.

## Procedure

1. **Confirm the symptom with the provider's own status page.**
   If the provider reports a known incident, switch the routing
   configuration to the fallback provider and inform the
   status page.

2. **If the provider is LLM-based and the failure is policy
   rejection rather than network, do not blindly retry.** The
   rejection means the prompt triggered the provider's policy
   filter; a retry will fail the same way. Inspect the offending
   prompt (it may include user-supplied paper text that looks
   like a prompt injection) and, if the rejection is correct,
   route to a different model or return `insufficient_evidence`.

3. **If the provider is resolution-based, switch the resolution
   priority** via the reference resolution service. The service
   already has a fallback order; the runbook step is to set the
   degraded provider's priority to `disabled` in
   `config/feature-flags.yaml` and reload.

4. **Verify the fallback is healthy** by sending a single
   low-priority probe analysis through the routing configuration
   and confirming the analysis completes within the SLO. The
   probe must use a synthetic paper, not a real user analysis,
   so the fallback is exercised without affecting user data.

5. **If all fallback providers are also degraded,** mark the
   reference resolution stage as `degraded` in the analysis
   pipeline and emit `insufficient_evidence` for new analyses
   rather than waiting for the providers to recover. This is
   the AGENTS.md "abstention is success" rule applied at the
   pipeline level.

6. **Communicate the degradation** on the status page within
   15 minutes of detection. The status page entry must include
   the affected stage, the fallback in use, and the expected
   recovery window.

## Recovery

When the provider's status page reports resolution, restore the
routing configuration. The recovery is staged:

- 15-minute soak with the probe analyses to confirm stability.
- Restore the routing order in `config/model-routing.yaml`.
- Re-enable the previously-degraded provider at the bottom of
  the priority list.
- Remove the status page entry.

## Postmortem

A provider-degradation incident must be postmortemed within
72 hours. The postmortem must include the upstream incident
ID, the time-to-detection, the time-to-fallback, the number
of analyses affected, and any follow-up actions to improve
detection or fallback latency.
