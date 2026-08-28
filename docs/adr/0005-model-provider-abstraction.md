# ADR-0005: Route Models Through a Typed Model Gateway

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Model capability, pricing, privacy options and availability change. Domain semantics must not depend on one provider's SDK or self-reported confidence.

## Decision

All embedding and generation calls pass through typed gateway interfaces. Routes are configured by purpose, privacy profile and quality tier. Outputs are JSON-Schema validated; stage confidence derives from calibrated system features.

## Consequences

- providers can be changed without public API changes,
- prompts/models are versioned with every result,
- private/self-hosted routes can be added,
- model failure becomes typed and bounded,
- raw provider objects and invalid output never reach domain/UI layers.
