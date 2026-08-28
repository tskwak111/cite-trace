# CiteTrace Demo & Pitch Package

> **Version:** 1.0.0  
> **Purpose:** Present the product without overstating scientific certainty or access.

---

## 1. Thirty-second pitch

논문을 읽다가 인용 하나를 확인하려면 References를 찾고, 논문을 검색하고, 원문을 구하고, 관련 구간을 읽고, 지금 주장과 맞는지 직접 비교해야 합니다. CiteTrace는 그 과정을 하나의 증거 화면으로 바꿉니다. 인용을 누르면 왜 인용했는지, 원 논문의 정확한 근거가 어디인지, 실제로 주장을 지지하는지, 무엇을 그대로 쓰고 무엇을 바꿨는지 보여줍니다. 그리고 원문을 확인하지 못한 경우에는 답을 꾸미지 않고 그 한계를 명확히 표시합니다.

---

## 2. Three-minute demo script

### Scene 1 — The pain

Open a paper at a sentence containing three references.

Narration:

> 이 한 문장을 제대로 이해하려면 세 논문을 각각 찾고, 현재 주장과 연결되는 구간을 찾아야 합니다. 일반 요약은 각 논문이 무엇인지 알려줄 수 있지만, 왜 이 자리에서 인용됐는지까지는 직접 다시 확인해야 합니다.

### Scene 2 — Click citation

Click the first citation. Show source identity immediately while evidence analysis completes.

> CiteTrace는 먼저 레퍼런스의 정확한 논문과 버전을 확인합니다. 비슷한 후보가 있으면 임의로 선택하지 않고 후보를 보여줍니다.

### Scene 3 — Exact evidence

Show the exact source passage and open it in the source PDF.

> 이 문장이 현재 주장과 가장 직접적으로 연결되는 원문입니다. 표시된 문장은 AI가 다시 쓴 문장이 아니라 분석한 source asset에 실제로 존재하는 구간입니다.

### Scene 4 — Scope difference

Show `scope_mismatch`.

> 그런데 현재 논문은 ‘적은 라벨 환경 전반’으로 표현했지만, 원 논문의 실험은 두 개의 이미지 데이터셋과 10% 라벨 조건에 한정되어 있습니다. CiteTrace는 관련성은 인정하면서도 범위 차이를 따로 표시합니다.

### Scene 5 — Transformation

Open a method citation with paired spans.

> 두 번째 인용에서는 원 논문의 목적함수는 유지했지만 이미지 인코더를 시계열 인코더로 바꾸고 정규화 항을 추가했습니다. 단순한 citation edge가 아니라 어떤 부분이 이어지고 바뀌었는지를 보여줍니다.

### Scene 6 — Honest limitation

Open an inaccessible source.

> 이 자료는 논문 정체만 확인됐고 합법적으로 분석 가능한 전문이 없습니다. 그래서 CiteTrace는 초록 수준의 정보만 표시하고, 확정적인 근거 판정은 보류합니다.

### Scene 7 — Value

Show prioritized reference map.

> 사용자는 60개의 레퍼런스를 전부 읽는 대신, 현재 논문을 이해하는 데 핵심인 7개와 왜 읽어야 하는지부터 확인할 수 있습니다.

---

## 3. Five-slide pitch outline

### Slide 1 — Problem

“한 편의 논문을 이해하려면 뒤에 연결된 수십 편을 다시 읽어야 한다.”

- reference search and version confusion
- exact evidence discovery
- claim/source comparison
- novice comprehension bottleneck

### Slide 2 — Product

“Every citation becomes an inspectable evidence trail.”

- click citation
- exact source span
- relation and scope
- adoption/change
- confidence and limitation

### Slide 3 — Why now / why different

- paper search, PDF chat and graphs are established categories
- cross-paper claim-to-evidence verification remains fragmented
- structured parsers, scholarly graphs, retrieval and models now make a focused workflow feasible
- moat is the corrected citation-evidence and transformation graph, not merely API access

### Slide 4 — Beachhead and model

- students/researchers/labs
- free → individual → lab → enterprise
- paper/citation-based meaningful usage units
- private and institution-ready path

### Slide 5 — Roadmap and proof

- one citation evidence invariant
- automated lawful acquisition
- relation/transformation intelligence
- whole-paper lineage
- gold-set and trust gates

---

## 4. Demo asset requirements

Use a prevalidated public/OA paper pair with:

- clear citation anchor
- stable source versions
- exact evidence passage
- one meaningful scope nuance
- one clear method change
- permission to display excerpts

Maintain a backup offline dataset and recorded analysis so provider outages do not force false live claims. Label recorded results if used.

---

## 5. Questions and answers

### “Is this just another PDF chatbot?”

No. The core object is a structured evidence link between a citing claim and exact source span, with work/version resolution, relation, transformation, confidence and provenance. Chat can be an interface later, not the product's trust boundary.

### “Can it access every paid paper?”

No. It uses user-authorized uploads and lawful open-access or provider content. When full text is unavailable, it exposes the limitation or asks for an authorized source.

### “Does it prove a citation is wrong?”

It identifies evidence relationships and scope differences for human inspection. A mismatch can arise from version, context or interpretation and is not automatically misconduct.

### “Why is this defensible?”

The long-term asset is an adjudicated citation-to-evidence and transformation dataset, user correction loop, provenance infrastructure and workflow integration—not the commodity ability to call a language model.

### “What is the hardest technical part?”

Reliable reference/version resolution, exact evidence retrieval, scope-aware relation judgment and calibrated abstention across fields and document formats.

---

## 6. Claims to avoid in pitch

- “100% accurate”
- “understands every paper”
- “proves truth or fraud”
- “unlimited access to all research”
- “replaces peer review”
- “eliminates the need to read sources”

Use measured target and evaluation language instead.
