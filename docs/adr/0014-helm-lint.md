# ADR-0014: Helm chart lint in `make check`

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

The Helm chart in `starter/ops/release/helm/` was added in
Slice 8 (production infrastructure). The chart is committed
but has no automated validation: a syntactically invalid
template would only surface at the next `helm install` on a
real cluster, and the release pipeline has no way to catch
typos in `values.yaml` field names, missing selectors, or
broken indentation before they hit production.

The blueprint §11 and the master plan list "deployable
Helm chart" as an exit gate for the v1.x release. The chart
is the artefact a future v2.0+ release will install; it
should lint cleanly today.

## Decision

`make check` gains a `helm lint` stage that runs
`helm lint <chart>` against the chart with the committed
default `values.yaml`. The lint catches:

- template parse errors (indentation, missing closing tags);
- missing required values referenced from templates;
- bad `apiVersion` / `kind` combinations;
- duplicate resource names within a release;
- whitespace and naming-convention issues that the
  `helm lint` plugin set considers warnings.

The stage does **not** invoke `helm template` and render
the chart to YAML; `helm lint` already parses the templates
and produces a rendered manifest internally. Rendering to
disk is left to the release pipeline.

The chart is committed without a `ci/` directory because
the chart's value-overrides are deployment-specific and
the lint target validates the **default** path only. A
future slice can add `helm template` + `kubeconform`
validation against the rendered manifest for a stricter
gate; that is an ADR-sized change of its own.

## Consequences

- A typo in any template or in `values.yaml` is caught by
  `make check` before a release is tagged.
- The `helm` binary becomes a build-time dependency. The
  CI workflow installs it via the same `azure/setup-helm`
  action (or `brew install helm` on macOS) so the lint
  stage runs in CI.
- The lint stage is optional in environments without
  `helm`; the `make check` target skips it with a clear
  message rather than failing the build.

## Out of scope (explicitly)

- `helm template` + `kubeconform` schema validation. That is
  a stricter gate and is a follow-up ADR.
- A chart-releaser workflow. The chart is internal to the
  repository for now; publishing it to a Helm repository
  is a deployment decision.
- Renovate or Dependabot integration for the chart's
  `appVersion` bumps. The chart is versioned by the
  package version, not by a separate chart bump.
