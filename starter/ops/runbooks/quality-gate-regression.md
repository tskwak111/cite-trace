# Quality Gate Regression Runbook

This runbook covers a regression in the evidence quality gates:
quote validation, span containment, scope comparison, or the
calibration confidence. The gates are the AGENTS.md invariant
"never weaken evidence or security gates"; a regression here
must be investigated with the same urgency as a security incident.

## Symptoms

- The `quote_validator` failure rate increases by more than 2x
  over the 7-day baseline.
- The `relation_verifier` macro-F1 on the synthetic contract
  drops below 0.75.
- The `confidence_calibration.expected_calibration_error` rises
  above the configured threshold.
- The release-time `run_release_evaluation.py` script exits
  non-zero on a release candidate that previously passed.

## Pre-conditions

- PagerDuty acknowledgement by the on-call SRE.
- Access to the quality-gate dashboard and the synthetic contract
  results.

## Procedure

1. **Identify the gate that regressed.** Open the quality-gate
   dashboard and compare the last 24 hours to the previous
   7 days. The dashboard shows per-gate regression alerts; do
   not infer from a single metric.

2. **Freeze new releases** by setting
   `release.registry.freeze = true` so that no new release is
   promoted to default while the regression is being
   investigated. This is a no-cost precaution; the freeze is
   reverted in step 8.

3. **Determine the cause.** In order:
   - A prompt version change in `prompts/` since the last
     passing release. Diff the prompt against the previous
     version and confirm whether the change is the regression
     or whether the prompt was supposed to address a different
     issue.
   - A model provider change in `config/model-routing.yaml`
     since the last passing release. A new model version
     frequently shifts calibration; confirm via the per-model
     dashboard.
   - A change in the verifier or the calibrator code. Pull
     the diff and confirm whether the change is the regression.

4. **If a prompt change is the cause,** revert the prompt and
   re-run the synthetic contract. The synthetic contract must
   reach the previous macro-F1 within one hour; if not, the
   revert is not the right action and the next suspect is the
   model provider.

5. **If a model provider change is the cause,** route the
   affected gate to the previous model version via
   `config/model-routing.yaml` and re-run the synthetic
   contract. If the previous model is not available, the
   gate is held and the regression is escalated.

6. **If a code change is the cause,** revert the change and
   re-run the synthetic contract. The revert must be reviewed
   by a second engineer before it is merged; a quality-gate
   regression reverted without review is grounds for the
   on-call to be paged again.

7. **Run the release-time script** in dry-run mode against
   the staging environment and confirm that the regression
   no longer reproduces. The script must pass before the
   release freeze is lifted.

8. **Lift the release freeze** by setting
   `release.registry.freeze = false` and re-enable promotion
   through the normal release pipeline.

9. **Write the postmortem** within 48 hours. The postmortem
   must include the regressed gate, the cause, the
   time-to-detection, the time-to-mitigation, the affected
   analyses (if any), and the follow-up action that prevents
   the same regression class in the future.

## What this runbook does not cover

- Permanent changes to a gate's threshold. Threshold changes
  require an ADR and the evidence-quality working group's
  approval; they cannot be made through this runbook.
- New gates. New gates are introduced through the eval
  pipeline and require their own contract tests; this
  runbook is for existing gates.
