# Process Notes

## /scope

**How the idea evolved:** Xinxiang arrived with a well-formed product vision captured in a checklist file. The /scope conversation moved them from *what* (the checklist) to *why* and *how* — surfacing the competitive positioning (lightweight + explainable vs. AppZen's black-box and TaxHacker's extraction-only), the three-layer architecture (OCR → rule engine → controlled AI), and the full UI vision.

**Pushback received:** Challenged on whether export and the AI ambiguous-case layer were truly necessary for MVP. Xinxiang defended both: export makes the output usable beyond the demo; the AI layer is part of the core working logic. They deprioritized interactive dashboard filtering instead. Valid tradeoffs — accepted without significant revision.

**References that resonated:** The three-way competitive analysis (AppZen / Rydoo / TaxHacker) landed strongly. Xinxiang came back with a sharp positioning statement unprompted — "lightweight, explainable, fills the gap" — which became the core differentiator in the scope doc.

**Deepening rounds:** One round (UI design). Surfaced: light-mode financial aesthetic, semantic color system (green/red/orange, no yellow), and the full results page layout (summary bar → filter → table → detail panel → export). The UX logic they articulated — inform → narrow → investigate → act — materially sharpened the scope doc.

**Active shaping:** High. Xinxiang drove nearly every significant decision: the three-layer architecture, the color system rationale (avoiding yellow for contrast), the layout hierarchy, the competitive framing. They pushed back on suggested cuts (AI layer, export) with reasoned arguments. Very little passive acceptance — they contributed ideas the conversation hadn't surfaced.

## /onboard

**Technical experience:** CS Y1 student, 2 years self-study. Python-strong, knows HTML/CSS and C. Has built a chess engine and YouTube tune extraction tool — not trivial projects. Experienced with AI coding agents (Copilot, Claude, Cursor); uses them for plan iteration and execution. Reliably hits ~80% of planned scope and is explicitly motivated to close that gap.

**Learning goals:** Build production-quality, fully functional apps — not demos or toys. Wants systematic practices that lead to reliable, complete software.

**Creative sensibility:** No strong aesthetic signals. Defaulting to clean and functional (appropriate for a financial tool).

**Prior SDD experience:** Has clarified goals informally before projects but without constraints or full scope. Good planning instincts, no formal SDD experience. Will benefit from seeing how constraints sharpen outcomes.

**Energy and engagement:** Focused and driven. Knows exactly what they want to build and why. Came in with a fully-formed product idea — will need to be guided toward deeper exploration in /scope rather than just restating the spec. Teammate Muhammad Bin Mateen also involved; may want to check in on Muhammad's background during /scope.

## /prd

**What was added or changed vs. scope doc:**
- Upload screen was entirely undefined in the scope doc — this conversation specified: two upload zones, required `receipt_file` column, fail-fast CSV schema validation with specific error messages, downloadable template
- Processing screen: added step-by-step text-based progress (4 steps), completion markers, missing-file warning without blocking
- Rule engine: all five rules now have precise OK/UNCERTAIN/FLAGGED thresholds with specific numeric boundaries (10% amount mismatch threshold, exact vs. fuzzy duplicate criteria)
- AI layer: explicitly constrained to category validation only; structured output format defined (`category_consistent` / `category_unclear` / `category_mismatch`)
- Detail panel: defined as right-side master-detail (table stays visible); rule-specific data comparison specified per rule type; duplicate side-by-side view with highlighted matching fields defined
- CSV export: full column list defined (7 original + 12 audit fields); three export filter options specified
- Session management: "New Audit" button added — explicitly required, not just a page refresh
- All-clear state: defined as a prominent outcome display when 0 flagged + 0 uncertain
- OCR recovery: three-tiered inline recovery (accept / edit inline / replace image)

**"What if" questions that surprised the learner:**
- Receipt-to-CSV matching was not thought through — the learner initially said "just upload folders" without considering how the system links a receipt image to a specific expense row. This triggered a full discussion of matching strategy.
- First-run / empty state: the all-clear case had not been considered. Learner responded quickly and cleanly once surfaced.
- What happens when a receipt file is missing during processing: learner hadn't considered whether this should block or continue — arrived at the right answer (audit finding, not system failure) quickly.

**Pushback and strong positions:**
- Visual mapping interface: learner got excited and proposed a full drag-and-drop matching UI (auto-match → visual confirm → manual fix). Flagged as scope risk; learner correctly identified it as a future enhancement after considering build time vs. demo value.
- Rule configuration UI: attempted again during edge cases ("user can configure new rules using graphical UI"). Held the scope boundary; learner confirmed it was still out of scope.
- AI layer, export, and the five-rule engine: all defended as essential from the start. No pushback on these.

**Scope guard conversations:**
- Visual mapping interface deferred — learner made the call after the scope concern was named directly. Recognized it wasn't part of the core demo story (audit logic, explainability, controlled AI).
- Rule configuration UI: second attempt to add it; confirmed deferred again.
- What was kept: all five rules, OCR recovery, detail panel, CSV export, AI layer, processing screen.

**Deepening rounds:** One round. Surfaced: all-clear state, "New Audit" button, fail-fast CSV validation, OCR inline recovery flow. All four gaps would have been surprise blockers during build.

**Active shaping:** High. Learner drove almost every significant decision: the `receipt_file` column approach (and its rationale — "more reliable, avoids ambiguity, supports multiple receipts per expense"), the three-tier OCR recovery, the all-clear state design, the full CSV export column list, the step-by-step processing screen as part of the explainability story. The duplicate side-by-side comparison view was entirely learner-originated. Passive acceptance was rare — most answers came with principled reasoning ("auditors need a complete audit trail," "data issues are audit findings, not system failures," "a good product should not make users think about what to do next").

## /spec

**Technical decisions made:**
- **Pure Streamlit over FastAPI:** Deployment constraint drove this — Streamlit Community Cloud runs one process. FastAPI would require a second free host (Render) with 10–30s cold starts. Learner chose working deployed demo over FastAPI learning goal. Clean module separation (`engine/`, `models/`, `ui/`) delivers equivalent structure without HTTP.
- **Groq (Llama 3.3 70B) over OpenAI:** OpenAI has no free tier. Groq is free (~14,400 req/day), OpenAI-compatible, and sufficient for 3-way classification. Restricted items fast-path (JSON list check before API call) reduces Groq calls further.
- **Severity grounded in AppZen's model:** Learner was unfamiliar with auditing — researched industry standard (AppZen, PCAOB, ACCA). Settled on rule-type-based severity (HIGH = fraud signals, MEDIUM = policy ambiguity, LOW = data quality). Learner confirmed this made sense after seeing the research.
- **Pytesseract on Streamlit Community Cloud:** Confirmed viable via `packages.txt` (installs `tesseract-ocr` via apt). Version 4.1.1 available — sufficient for demo.
- **Single-page Streamlit with session state step control:** Linear flow (upload → processing → results) doesn't benefit from Streamlit multi-page routing. Step controller in `app.py` keeps navigation app-controlled.

**Three PRD open questions resolved:**
1. Severity: rule-type-based HIGH/MEDIUM/LOW matrix (not dollar-amount-based)
2. AI fallback: approved-list-only check, UNCERTAIN for ambiguous, `ai_assisted=false` in export
3. Approved category list: 12 standard business categories in `config/categories.json`; restricted items in `config/restricted_items.json`

**What learner was confident about vs uncertain:**
- Confident: overall three-layer architecture, modular Python structure, data model shape, rule engine design, the "AI as suggestion not decision" principle
- Uncertain/deferred to research: severity criteria (unfamiliar with auditing industry standards), OCR API options, AI provider selection

**Stack choices and rationale:**
- Streamlit: Python-first, zero frontend code, deploys free on Community Cloud
- pytesseract: free, local, PRD's OCR recovery flow already designed for its accuracy limitations
- Groq / Llama 3.3 70B: free tier, OpenAI-compatible, sufficient for constrained 3-way classification
- pandas: learner's Python strength; natural fit for CSV manipulation and rule engine data access

**Deepening rounds:** Zero rounds chosen. Learner reviewed the full architecture (file structure, data flow, session state, engine layer, UI layer) and confirmed no changes needed after each proposal. They explicitly declined additional deepening rounds and moved straight to spec generation. Architecture was detailed enough that all PRD epics had a clear home before generation began.

**Active shaping:** Moderate. Learner specified the initial stack (FastAPI + Streamlit + pytesseract) and drove the deployment priority decision (live URL > FastAPI learning). Deferred to research for OCR accuracy context, AI provider selection, and severity criteria. Accepted the pure-Streamlit architectural pivot quickly with clear reasoning ("working deployed demo, not production backend"). No pushback on engine module design or session state model — accepted proposals without revision except two minor improvements to RuleResult (added confidence field, requested row-level error handling in orchestrator). Both were additive, not corrective.

## /checklist

**Sequencing decisions:**
- Learner initially proposed rules-first, then backend. Correct instinct (rules are the core) but reordered: OCR before rules so rule engine has real OCRResult data to run against, not mocked values.
- Learner then independently reordered to data → core logic → orchestration → UI. Clean engineering principle. Accepted entirely — engine modules (items 1–7) are all built and testable in Python before any Streamlit UI work begins.
- Two gaps filled: `matcher.py` added to item 4 (prerequisite for OCR); `upload_view.py` added as item 8 (needed to feed data into pipeline from browser).
- Devpost submission is item 13.

**Methodology preferences:**
- Build mode: Step-by-step
- Comprehension checks: Yes (one question per item to confirm understanding)
- Verification: Yes (per item — run app or module and confirm expected output)
- Git cadence: Commit after each item, message format "Complete step N: [title]"
- Check-in cadence: Learning-driven — post-item debrief (files changed, what it does, how to test) + comprehension check question

**Items and estimated build time:**
- 13 items total: 1 scaffolding + 1 models + 5 engine modules + 2 UI entry/processing + 3 results UI + 1 export/reset + 1 Devpost
- Estimated: 15–30 min per item → 4–6 hours total build time (step-by-step with verification)

**Learner confidence vs guidance needed:**
- Confident: reordering rationale (drove the data→logic→UI principle independently), step-by-step preference, verification need
- Deferred to agent: "wow moment" screenshot (hadn't seen the app yet — noted as TBD once results view is built)
- No hesitation on any sequencing decision once the OCR-before-rules logic was explained

**Submission planning notes:**
- Core story is strong and learner-authored: "auditors don't just see flags, they see exactly why something was flagged"
- GitHub repo already exists: https://github.com/Edd1eOS/Devpost-Hackathon
- Deployment already planned: Streamlit Community Cloud (in spec)
- Wow moment screenshot: TBD — flagged as "identify when results_view.py is complete"; likely the detail panel with rule-specific comparison

**Deepening rounds:** Zero rounds chosen. Learner reviewed the proposed checklist and confirmed it felt right for the time available. No items were split, consolidated, or reordered after the initial proposal.

**Active shaping:** High on sequencing. Learner did not passively accept the proposed order — they independently proposed a different sequencing principle (data → logic → orchestration → UI) and it was adopted. Minor gaps (matcher, upload_view) filled by agent. Methodology preferences were stated clearly and specifically ("briefly explain what files changed, what the module does, how I can test it") rather than just agreeing to defaults.
