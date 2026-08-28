# Runbook: Source Takedown

## Overview
This runbook covers the procedure for taking down an external source (e.g. paper, article) when a valid DMCA or other takedown request is received.

## Procedure
1. Identify the source asset IDs related to the request.
2. Mark the source asset as a tombstone using the retention service.
3. Validate that the source is no longer accessible through the API.
4. The background retention worker will handle physical deletion.
