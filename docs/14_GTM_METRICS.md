# CiteTrace Go-to-Market & Metrics

> **Version:** 1.0.0  
> **Status:** Hypothesis framework for validation, not a revenue forecast.

---

## 1. Launch wedge

### Primary wedge

Students, graduate researchers and small research labs reading method-heavy English scientific papers in AI/CS and selected life-science domains.

### Why this wedge

- frequent reference-following behavior,
- high pain from method/data/metric dependencies,
- strong digital PDF and arXiv/repository usage,
- outcomes are demonstrable in a single session,
- accessible communities for design partnerships,
- lower procurement friction than institutional launch.

### Excluded initial targets

- broad consumer “learn anything” market,
- legal/medical decision support,
- publisher-wide integrity scoring,
- automated peer-review verdict products,
- universal multilingual/scanned-document claims.

---

## 2. Message hierarchy

### Headline

> Click a citation. See the original evidence.

### Supporting message

> CiteTrace finds the cited work, opens the exact relevant passage, checks whether it supports the current claim, and explains what the new paper adopted or changed.

### Trust message

> Every conclusion shows the source version, exact evidence and uncertainty. When the source cannot be verified, CiteTrace says so.

### Korean working copy

> **논문 인용을 누르면, 원래 근거까지 바로 보여줍니다.**  
> 현재 논문의 주장과 레퍼런스 원문의 정확한 구간을 연결하고, 지지·범위 차이·변형 관계와 불확실성을 함께 설명합니다.

---

## 3. Demo-led acquisition

The strongest acquisition asset is a before/after workflow:

1. show a dense citing sentence with three references,
2. manually describe the old search/read burden,
3. click one citation,
4. show exact source span and version,
5. reveal that the source is narrower than the citing claim,
6. open the source page,
7. save the truly important reference.

The demo must use a licensed/public example with prevalidated assets and still show limitations honestly.

---

## 4. Distribution channels

### Individual

- university and research communities
- technical paper-reading content
- arXiv/research-tool communities
- student research courses and lab onboarding
- open-source starter or limited free tier

### Lab/team

- design-partner outreach to professors/lab managers
- implementation/reproducibility workflows
- shared reading queue and correction history
- private workshops using the lab's authorized documents

### Institutional later

- research libraries and R&D organizations
- SSO/retention/audit requirements
- private deployment and source-policy controls
- authorized link resolver/proxy integrations

---

## 5. Pricing hypotheses

### Free

- limited active papers per month
- a bounded number of priority citation analyses
- short retention
- public/OA and user-upload workflow

### Individual Pro

- higher analysis limits
- full-paper modes
- reading queues and exports
- longer retention and history

### Lab

- shared workspace and roles
- collaborative corrections/notes
- pooled usage and storage
- admin retention controls

### Enterprise/R&D

- SSO, audit, legal/source policy
- private model route/deployment
- regional and retention requirements
- support and capacity commitments

The product should meter user-meaningful units—papers, priority citations, storage and concurrent analyses—rather than exposing model tokens.

---

## 6. Funnel metrics

### Acquisition

- landing-to-signup
- demo completion
- referral/source mix
- qualified lab conversations

### Activation

A user is activated when, within an initial usage window, they:

1. import a supported paper,
2. open at least one evidence card,
3. open the exact source evidence,
4. inspect or save another citation/reference.

Track:

- import success
- time to first inspectable citation state
- evidence card open
- source span open
- reading queue save

### Retention

- weekly returning researchers
- papers analyzed per active week
- repeat source opens
- reading queue revisits
- exports/shares
- team correction activity

### Revenue

- free-to-paid conversion
- lab trial-to-paid
- expansion by seats/usage
- gross margin by verified evidence link
- support cost by plan

---

## 7. Trust and quality metrics alongside growth

No growth review is valid without:

- wrong-paper correction rate
- wrong-evidence correction rate
- relation disagreement rate
- abstention rate and recovery
- fabricated quote invariant
- source-open rate
- parse/access distribution
- cost per verified evidence link

A conversion increase caused by hiding uncertainty is considered a product-quality regression.

---

## 8. Validation experiments

### Experiment E1 — Evidence vs summary value

Compare user task correctness and preference between:

- generic cited-paper summary,
- relationship-centered card with exact evidence.

Primary metric: correct explanation of why the reference matters.

### Experiment E2 — Mode priority

Observe real tasks in Understand, Implement and Review. Determine which mode produces repeat usage and willingness to pay.

### Experiment E3 — Abstention copy

Test whether users understand `inaccessible_source`, `insufficient_evidence` and recovery actions without perceiving the system as broken.

### Experiment E4 — Team correction loop

Give labs a shared review queue and measure whether corrections are produced, reused and valued.

### Experiment E5 — Source availability

Sample representative launch-domain papers and measure:

- resolved references,
- OA full text,
- abstract only,
- user-source required,
- version ambiguity.

This determines honest product claims and cost.

---

## 9. Product-market evidence thresholds

Strong evidence includes:

- repeated voluntary weekly use,
- high source-open and reading-queue behavior,
- users bringing important/private papers under clear policy,
- correction activity that improves later results,
- labs paying for shared provenance/workflow,
- users describing trust and saved cognitive effort without prompting.

Vanity indicators such as one-time PDF uploads or generated word count are insufficient.
