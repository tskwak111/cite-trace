# Privacy Delete Request Runbook

This runbook describes the procedure for processing user privacy
deletion requests under GDPR, CCPA, and equivalent regulations. The
goal is a verifiable, complete deletion that the user can audit
through the data-export endpoint before the deletion is performed.

## When to use this runbook

- A user submits a verified deletion request through the in-app
  privacy workflow.
- A regulator orders deletion of a workspace.
- A user has been inactive for longer than the configured retention
  window and the retention service has flagged the workspace for
  deletion.

## Pre-conditions

- Identity is verified. For end-user requests, the request must come
  through the privacy workflow, not email, so that the verification
  step is part of the audit trail. For regulator requests, the
  legal team confirms the request and attaches the order to the
  ticket.

- The user is informed of what will be deleted. The export endpoint
  is offered before the deletion is scheduled; if the user does not
  request an export, the deletion proceeds regardless because the
  user's right to deletion is not contingent on accepting an
  export.

## Procedure

1. **Mark the workspace as `deletion_pending`.** This is a soft
   lock that prevents new analyses from being queued and prevents
   shared links from resolving. Existing in-flight analyses are
   allowed to complete and are then purged.

2. **Export the data to a temporary signed URL** if the user
   requested an export. The URL is single-use, expires in 24
   hours, and is delivered to the verified contact channel only.
   The export contains the analysis history, the user-uploaded
   assets, the user-created notes, and the feedback history. It
   does **not** contain the per-tenant row-level-secure data
   belonging to other tenants.

3. **Purge the user-uploaded assets.** Use the retention service
   `purge_workspace` job, which deletes the assets, the parsed
   source versions, the chunks, and the embeddings. The job
   writes a deletion receipt to the audit log with the
   workspace ID, the request ticket ID, the legal basis, and
   the SHA-256 of the deletion manifest.

4. **Tombstone the analyses.** Analyses are not hard-deleted;
   they are tombstoned so that any shared link the user has
   already sent resolves to a `410 Gone` response with an
   explanation. Tombstoning preserves the audit chain without
   leaking the deleted content.

5. **Cancel active share links** issued by the user. The links
   are revoked and the share tokens are burned. The audit log
   records the revocation with the share token hash, never the
   token itself.

6. **Verify the deletion.** Run the verification query in the
   retention service and confirm that the audit report shows
   zero user-uploaded bytes remaining. The verification must
   include the object-store delete marker check, not just the
   database row count.

7. **Notify the user.** Send a deletion confirmation through the
   verified contact channel. The confirmation includes the
   deletion receipt ID, the deletion timestamp, and the
   verified-by name.

## What this runbook does not cover

- Bulk deletion of a tenant by a billing-related action. That
  flows through the tenant-offboarding runbook, which is a
  separate procedure because it has different audit and
  notification requirements.
- Legal hold. A workspace under legal hold cannot be deleted
  through this runbook; the legal hold must be lifted first
  and the deletion is then performed by the legal team.
