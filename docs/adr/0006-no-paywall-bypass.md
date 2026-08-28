# ADR-0006: Lawful Source Acquisition Only

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Reliable verification benefits from full text, but bypassing publisher access controls creates legal, contractual and trust risk.

## Decision

Analyze full text only from user-authorized assets or lawful open-access/provider paths. Never forward user sessions, bypass paywalls/CAPTCHAs, or redistribute private/licensed PDFs. Record access level, license/source, timestamp and checksum. Use abstract/metadata limited states when full text is unavailable.

## Consequences

- source availability limits some analyses,
- user upload is a first-class recovery flow,
- provider/source policies are operational configuration,
- excerpts remain minimal and attributed,
- commercial launch requires legal review of target integrations.
