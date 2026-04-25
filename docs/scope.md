# AI Audit Assistant

## Idea
A lightweight, explainable expense audit assistant that combines deterministic rule-based logic with controlled AI assistance — producing structured, decision-ready audit reports rather than opaque verdicts.

## Who It's For
**Primary:** Professional auditors who review large expense datasets and need comprehensive coverage without manual sampling. Their pain: traditional auditing only samples data, missing duplicates and patterns at scale. Their need: a scalable first-pass review system that flags and explains, not just decides.

**Secondary:** Small business owners and finance teams who can't afford enterprise audit tools but need reliable expense verification.

**Market signal:** PwC's $100M investment in generative AI for auditing confirms this is a real, large-scale problem — auditors are overwhelmed by unstructured data. This project targets the gap that enterprise tools leave: transparency and explainability at lightweight cost.

## Inspiration & References
- [AppZen](https://www.appzen.com/ai-for-expense-audit) — The enterprise benchmark. Does 100% expense audit, receipt verification, duplicate detection. Black-box, opaque. Validates the market; defines what we're NOT building.
- [Rydoo Smart Audit](https://www.rydoo.com/expense/smart-audit/) — Closest UI reference: filterable compliance dashboard by alert type, user, category. Good model for the filter/sort interaction layer.
- [TaxHacker](https://github.com/vas3k/TaxHacker) — Open-source receipt OCR + extraction. Proves a small team can build the extraction pipeline; doesn't do validation or auditing.

**Competitive positioning:** The gap between these three — lightweight + explainable + rule-driven + controlled AI — is exactly where this project lives.

**Design energy:** Light mode, financial-tool aesthetic (closer to spreadsheet/dashboard than developer console). Clean information hierarchy, dense data display, professional and trustworthy. Not decorative.

**Color system:**
- OK → green (success), dark text on light badge
- Flagged → red (high risk), dark text on light badge
- Uncertain → orange (warning), dark text on light badge
- Pure yellow avoided for contrast reasons in light mode

## Goals
- Prove that 100% expense coverage is achievable without a black-box system
- Demonstrate explainable auditing: every flag comes with structured reasoning, not just a verdict
- Show a complete end-to-end workflow: upload → extract → validate → report → export
- Build something that feels production-quality, not a demo toy — the output should be immediately usable by a real auditor

## What "Done" Looks Like
An auditor uploads a CSV of expense entries and a set of receipt images. The system:

1. Extracts structured data from receipts via OCR
2. Runs a deterministic rule engine (amount mismatch, duplicate detection, missing receipt, invalid category, suspicious patterns)
3. Routes ambiguous cases to a controlled AI layer that produces structured suggestions — not final decisions
4. Displays results in a dashboard with this layout:

   **Top:** Summary bar — total checked, OK / Flagged / Uncertain counts, total amount reviewed, high-risk amount total

   **Second:** Filter + sort controls — filter by status, sort by severity, search by vendor / employee / category

   **Main:** Results table — expense ID, vendor, amount, category, status badge, confidence score, severity, short reason. Flagged entries appear first by default.

   **Detail panel:** Click any row to expand full explanation — data comparison, triggered rule, AI-assisted note (if applicable), detected pattern, suggested next action

   **Bottom:** Export button + disclaimer ("first-pass assistant, not a replacement for human review")

5. Exports results as CSV (minimum) — PDF and other formats are stretch goals

**Example flagged output:**
```
Expense #4821 | Wine & Dine Co. | $150 reported / $120 receipt
Status: FLAGGED | Confidence: 91% | Severity: HIGH
Reason: +25% mismatch exceeds 10% threshold
Pattern: 2 similar mismatches from same user
Action: Request clarification; verify non-reimbursable items
```

The UX logic follows a deliberate flow: inform → narrow → investigate → act. Auditors see the risk picture first, filter to what matters, examine entries, then know what to do next.

## What's Explicitly Cut
- **UI-based rule creation** — Rules are JSON-configured and hardcoded for the demo. A rule-creation interface is out.
- **Enterprise infrastructure / scalability** — This is a demo-scale system, not production-grade.
- **Accounting software integration** — No QuickBooks, SAP, or similar integrations.
- **Persistent database** — Session-based only; no data stored between runs.
- **Multi-user authentication** — Single-session use only.
- **Complex ML anomaly detection** — AI is constrained to structured suggestions on ambiguous cases; no freeform ML models.
- **PDF export (for now)** — CSV download is the MVP export. PDF is a stretch goal; it adds significant build time for limited demo value.
- **Interactive dashboard filtering** — The filter/sort UI is B-priority; if time is tight, a static sorted table still demonstrates the concept.
- **Dark mode** — Light mode only for the demo. Dark mode optionally deferred.

## Loose Implementation Notes
**Architecture (three layers):**
1. **Data extraction** (AI optional) — OCR preprocesses receipt images into structured fields. No audit decisions happen here.
2. **Validation layer** (no AI) — Deterministic rule engine handles amount matching, duplicate detection, policy checks. Produces explainable, deterministic outputs.
3. **AI assistant layer** (controlled) — Claude or similar handles ambiguous cases only (e.g., interpreting item descriptions). AI output is treated as a suggestion; rules define final decision boundaries.

**OCR failure strategy (decided):**
- Default: OCR processes all receipt images (natural workflow, no upfront choice)
- Localized recovery: if OCR confidence is low on a specific receipt, offer inline options — replace the image or manually enter the missing fields
- System-level fallback: if OCR is consistently unreliable (e.g., demo environment), allow CSV upload of pre-extracted receipt data instead
- Flow: OCR by default → localized correction → optional CSV fallback
- Failure is treated as a handled state, not a crash — "unreadable receipt" is already an audit flag; low-confidence OCR becomes an Uncertain entry

**Priority stack:**
- S (critical): CSV parsing, OCR extraction
- A (core): file upload, rule engine, CSV export
- B (high value): interactive filtering/sorting, detail panel
- C (stretch): PDF export, dark mode, AI ambiguous-case layer

**Team:**
- **Muhammad Bin Mateen** — Idea origination, feasibility research, high-level structure and architecture decisions. Established the repo skeleton (top-level folders, submission docs).
- **Xinxiang Lei** — Refinement, engineering, detailed implementation, AI-assisted coding (owns Claude Pro). Responsible for all `src/` architecture — not yet defined.
- Structure is mostly final. All folders except `src/` need little to no change. Only `src/` architecture remains to be designed — that's the one open decision before the build starts.

**Repository:** https://github.com/Edd1eOS/Devpost-Hackathon
- `docs/` — all doc files exist but are empty; to be filled by this curriculum
- `src/` — completely empty; code architecture to be designed in /spec
- `submission/` — hackathon submission templates (additional-info.md, devpost-checklist.md, project-story.md) already in place
