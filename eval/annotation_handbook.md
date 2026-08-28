# Annotation handbook

## 1. Unit of annotation

One case is one atomic citing claim associated with one target reference entry. A citation cluster containing three references may produce three cases, and one sentence containing two independently testable propositions may produce two claims.

## 2. Required evidence order

Annotators follow this order:

1. Verify the citing claim boundary and qualifiers.
2. Verify the bibliography entry and exact cited work/version.
3. Record source access level before reading any generated output.
4. Locate the best source evidence independently.
5. Compare claim and source scope dimension by dimension.
6. Assign one primary relation.
7. Assign citation intents from the citing context.
8. Assign transformation labels only when paired citing/source evidence exists.
9. Review the system explanation last.

This order reduces anchoring on model prose.

## 3. Claim boundary

Include every word that changes truth conditions:

- negation,
- hedging,
- population or dataset,
- task and modality,
- metric and baseline,
- temporal condition,
- numerical range,
- causal or comparative language.

Exclude adjacent commentary that can be judged independently.

## 4. Source identity

Record both intellectual work and manifestation. When a citation is clearly to the conference paper but only the later journal expansion is available, label the work match but version uncertainty. Do not silently treat all versions as interchangeable.

## 5. Relation decision tree

1. No inspectable source? `inaccessible_source`.
2. Source accessible, but no relevant passage after documented search? `no_relevant_evidence`.
3. Relevant passage exists but lacks enough information? `insufficient_evidence`.
4. Proposition incompatible under comparable conditions? `contradicts`.
5. Citing claim expands beyond source scope? `overgeneralized`.
6. Scope differs enough that support cannot be inferred, while neither proposition refutes the other? `scope_mismatch`.
7. Entire proposition and material qualifiers align? `direct_support`.
8. Only a material subset aligns? `partial_support`.
9. Source provides premises, mechanism or secondary support rather than direct evidence? `indirect_support`.

## 6. Multi-reference clusters

Do not copy the same relation to every target. Judge each reference independently. Use the citing syntax and the source evidence to determine whether the cluster shares one claim, separates targets or remains ambiguous.

## 7. Transformation labels

A transformation needs paired evidence:

- one or more spans showing the cited method or concept,
- one or more spans showing the citing paper's use or change,
- an explicit changed dimension when claiming parameter, domain or structural change.

Topical similarity is not conceptual inspiration.

## 8. Inaccessible material

Annotators must not obtain papers through unauthorized access. Use supplied lawful assets, open versions or user-provided copies. Abstract-only cases are labeled as such; the gold relation may be limited to what the abstract establishes.

## 9. Explanation audit

Split generated prose into material statements. For each statement, determine whether:

- exact supporting artifacts are listed,
- those artifacts actually support it,
- an inference is labeled,
- uncertainty and access limits are preserved.

A polished sentence with no artifact support is a failure.

## 10. Disagreement resolution

Annotators submit labels and rationales independently. The adjudicator reads both rationales, source spans and citing context, then records the final decision and a stable reason code. The original annotations remain immutable.
