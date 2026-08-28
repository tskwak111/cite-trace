# ADR-0004: Durable Asynchronous Stage Pipeline

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

PDF parsing, provider lookup, source acquisition and model verification exceed interactive request budgets and may partially fail.

## Decision

HTTP commands create durable analysis resources. Stage-specific workers consume idempotent commands, write checkpoints and publish immutable events. The API exposes state and SSE progress. PostgreSQL is authoritative; queue delivery is treated as at-least-once.

## Consequences

- every handler needs an input fingerprint and idempotency behavior,
- partial valid results survive later failures,
- users can cancel and prioritize citations,
- retries cannot duplicate semantic records,
- operational dashboards must expose queue age and stage attempts.
