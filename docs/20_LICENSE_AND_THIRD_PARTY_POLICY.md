# CiteTrace License & Third-Party Policy

> This is an engineering decision guide, not legal advice. The repository owner must select and approve the final license before public distribution or commercial deployment.

## 1. Recommended decision path

### Private commercial development

Keep application code and product documents proprietary while preserving all third-party notices and license obligations. Contractually define ownership of prompts, annotations, feedback, derived evaluation data, and customer-uploaded papers.

### Open-source foundation with commercial service

A permissive license such as Apache-2.0 is a practical default for the foundation code because it includes an express patent grant. Keep provider credentials, private datasets, customer assets, production deployment configuration, and proprietary model/evaluation assets outside the public repository.

### Research-only release

Do not use an ambiguous “research only” sentence as a substitute for a reviewed license. Define permitted use, redistribution, trained artifacts, data rights, and publication obligations explicitly.

## 2. Decisions required before distribution

- repository code and documentation license,
- contributor license agreement or developer certificate of origin,
- ownership and permitted reuse of human annotations,
- whether private feedback may ever enter shared training or evaluation,
- export formats and quotation limits,
- user warranties for uploaded-paper access rights,
- data-processing terms and subprocessors,
- policy for provider metadata and cached full text,
- trademark/name policy for “CiteTrace.”

## 3. Third-party inventory requirements

Generate an SBOM for every release and record, per dependency or container:

- exact name, version and source,
- package/container checksum,
- declared license and notice text,
- transitive dependencies,
- known vulnerabilities and exception owner,
- distribution or network-service obligations,
- upgrade and end-of-support date.

At minimum, review the selected releases of the web framework, UI runtime, API framework, database, vector extension, queue/cache, PDF parser, object store, model SDKs and every scholarly metadata/full-text provider. Do not infer redistributability from a public URL.

## 4. Scientific content policy

- bibliographic facts and provider records retain provider provenance,
- full text is acquired only through user-authorized upload or a lawful configured source,
- access level and license decision are stored per source asset,
- quotations are limited to what is necessary for inspection and comply with source policy,
- exports do not silently bundle full paper text,
- deletion and access revocation propagate to derived chunks, embeddings and exports according to policy,
- a source becoming unavailable does not erase the historical judgment, but the UI must mark the access/provenance change and prevent unauthorized redisplay.

## 5. Release gate

No public or commercial release is permitted until an accountable owner has recorded the selected repository license, completed the dependency/SBOM review, approved user upload terms, and validated quotation/export behavior for the launch jurisdictions and providers.
