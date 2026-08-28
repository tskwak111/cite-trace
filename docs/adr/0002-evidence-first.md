# ADR-0002: Evidence-First Generation and Exact Quote Validation

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

A language model can produce fluent explanations that cite the wrong source or invent a plausible quotation. The product's core promise requires inspectable source evidence.

## Decision

Retrieve candidate evidence, select exact source spans, validate those spans against one immutable source asset version, verify the relationship, and only then generate prose. Every displayed quote must be an exact validated substring with source coordinates/provenance. An explanation sentence must reference accepted spans or be marked as inference.

## Consequences

- free-form model quotes are never trusted,
- failures produce limited/abstained states,
- quote validation is a blocking release invariant,
- source asset/version storage is mandatory,
- the pipeline may be slower than generic summarization but is materially more auditable.
