# AI Audit Assistant — Technical Spec

## Stack

| Layer | Tool | Version | Docs |
|---|---|---|---|
| UI & app entry | [Streamlit](https://docs.streamlit.io) | ≥ 1.35 | https://docs.streamlit.io |
| Data processing | [pandas](https://pandas.pydata.org/docs/) | ≥ 2.2 | https://pandas.pydata.org/docs/ |
| OCR | [pytesseract](https://github.com/madmaze/pytesseract) + [Pillow](https://pillow.readthedocs.io) | pytesseract ≥ 0.3.10 | https://github.com/madmaze/pytesseract |
| System OCR engine | [Tesseract 4.1.1](https://tesseract-ocr.github.io) | 4.1.1 (Community Cloud) | https://tesseract-ocr.github.io/tessdoc/ |
| AI classification | [Groq Python SDK](https://console.groq.com/docs/openai) | ≥ 0.9 | https://console.groq.com/docs/quickstart |
| AI model | Llama 3.3 70B (via Groq) | — | https://console.groq.com/docs/models |
| Language | Python | ≥ 3.11 | — |

**Rationale:** Pure Python stack — no separate backend server, no HTTP overhead, deploys as a single Streamlit app. Engine logic lives in importable modules; Streamlit handles all UI. Groq's Llama 3.3 70B is free-tier, OpenAI-compatible, and sufficient for a 3-way classification task.

---

## Runtime & Deployment

- **Runtime:** Web app (browser), single-process Streamlit server
- **Local:** `streamlit run src/app.py` — requires Tesseract installed locally
- **Deployed:** [Streamlit Community Cloud](https://streamlit.io/cloud) — free tier, public URL, no credit card
  - Entry point: `src/app.py`
  - System packages: `packages.txt` installs `tesseract-ocr` via apt on deploy
  - API key: `GROQ_API_KEY` stored in Streamlit Community Cloud secrets (Settings → Secrets), accessed via `st.secrets["GROQ_API_KEY"]`
  - Local: key stored in `.streamlit/secrets.toml` (gitignored)

**Environment requirements:**
- Python 3.11+
- `GROQ_API_KEY` secret (free at https://console.groq.com)
- Tesseract binary (local: install via OS package manager; deployed: via `packages.txt`)

---

## Architecture Overview

### Component Map

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit App                     │
│                    (app.py)                         │
│         step: "upload" | "processing" | "results"  │
└────────┬────────────────┬──────────────────────────┘
         │                │
         ▼                ▼
┌─────────────┐   ┌───────────────┐   ┌──────────────┐
│ upload_view │   │processing_view│   │results_view  │
│   .py       │   │    .py        │   │    .py       │
└─────┬───────┘   └───────┬───────┘   └──────┬───────┘
      │                   │                  │
      │         ┌─────────▼──────────┐       │
      │         │   orchestrator.py  │       │
      │         │   (pipeline runner)│       │
      │         └──┬──┬──┬──┬──┬────┘       │
      │            │  │  │  │  │            │
      │      ┌─────┘  │  │  │  └───┐        │
      │      ▼        ▼  ▼  ▼      ▼        │
      │  parser  matcher ocr rules  ai       │
      │   .py    .py   .py  .py   .py       │
      │                               │      │
      └──────────── st.session_state ─┴──────┘
```

### Data Flow — Full Pipeline

```
1. User uploads CSV + receipt images
        │
        ▼
2. parser.py
   - validates required columns
   - returns pd.DataFrame or raises ValidationError
        │
        ▼
3. matcher.py
   - maps receipt_file values → uploaded image bytes
   - returns dict[str, bytes | None]
   - missing files → None (not a crash; becomes FLAGGED later)
        │
        ▼
4. ocr.py  (per receipt, called by orchestrator)
   - pytesseract --psm 6 on image bytes
   - extracts vendor / amount / date via regex
   - computes mean confidence from per-word scores
   - returns OCRResult(vendor, amount, date, raw_text, confidence)
   - confidence < 0.6 → low-confidence warning + inline recovery UI
        │
        ▼
5. rules.py  (per row)
   - check_amount_mismatch()   → RuleResult
   - check_duplicate()         → RuleResult
   - check_missing_receipt()   → RuleResult
   - check_category()          → calls ai.py if needed → RuleResult
   - check_suspicious_pattern()→ RuleResult
   - highest severity wins; all triggered rule names recorded
        │
        ▼
6. ai.py  (called from check_category() only)
   - checks raw_text against restricted_items.json first
     → if hit: returns "category_mismatch" immediately (no API call)
   - otherwise: Groq API call with declared category + OCR text
   - returns exactly one of:
       "category_consistent" | "category_unclear" | "category_mismatch"
   - on timeout/exception: returns None → fallback applied
        │
        ▼
7. orchestrator.py assembles AuditResult per row
   - wraps each row in try/except
   - on unexpected error: AuditResult with status=FLAGGED, severity=HIGH,
     reason="processing error: [exception message]"
   - yields progress events for the processing screen (steps 1–4)
        │
        ▼
8. st.session_state["results"] = list[AuditResult]
        │
        ▼
9. results_view.py renders dashboard, detail panel, export
```

---

## Data Model

### `models/schemas.py`

```python
from dataclasses import dataclass
from enum import Enum

class AuditStatus(Enum):
    OK        = "OK"
    UNCERTAIN = "UNCERTAIN"
    FLAGGED   = "FLAGGED"

class Severity(Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"
    NONE   = "NONE"

@dataclass
class OCRResult:
    vendor:     str | None
    amount:     float | None
    date:       str | None
    raw_text:   str
    confidence: float          # 0.0–1.0; < 0.6 triggers inline recovery

@dataclass
class RuleResult:
    status:           AuditStatus
    severity:         Severity
    confidence:       float        # rule-level confidence in the finding
    rule_name:        str
    reason_summary:   str          # one-line, shown in table
    detailed_reason:  str          # full explanation, shown in detail panel
    suggested_action: str
    duplicate_match_id: str | None = None

@dataclass
class AuditResult:
    # Original CSV fields
    expense_id:    str
    employee_id:   str
    vendor:        str
    amount:        float
    date:          str
    category:      str
    receipt_file:  str

    # Audit output
    audit_status:     AuditStatus
    severity:         Severity
    confidence:       float
    triggered_rules:  list[str]
    reason_summary:   str
    detailed_reason:  str
    suggested_action: str

    # Receipt & OCR
    matched_receipt_file: str
    ocr_result:           OCRResult | None   # None if receipt missing

    # Duplicate detection
    duplicate_match_id: str | None

    # AI layer
    ai_assisted: bool
    ai_note:     str | None

    # Metadata
    generated_at: str    # ISO 8601 timestamp, e.g. "2026-04-26T14:32:00Z"
```

---

## Engine Layer

### `engine/parser.py`

Implements `prd.md > Upload & Validation`

**Input:** raw CSV file bytes (from `st.file_uploader`)
**Output:** `pd.DataFrame` on success; raises `ValidationError` with field-level message on failure

**Required columns:** `expense_id`, `employee_id`, `vendor`, `amount`, `date`, `category`, `receipt_file`

**Behavior:**
- On upload, immediately checks for all required columns
- If any are missing: raises `ValidationError("Missing columns: [x, y, z]. Expected schema: expense_id, employee_id, vendor, amount, date, category, receipt_file")`
- Processing does not begin until validation passes
- Also exposes `generate_sample_csv() -> bytes` used to create `assets/sample_expenses.csv`

### `engine/matcher.py`

Implements `prd.md > Processing & OCR Extraction` (receipt matching step)

**Input:** validated `pd.DataFrame`, `dict[str, bytes]` (filename → file bytes from uploader)
**Output:**
```python
(
  matched: dict[str, bytes | None],   # receipt_file value → bytes or None
  missing: list[str]                  # filenames referenced in CSV but not uploaded
)
```

Missing files produce `None` in `matched` — not an error. The missing list is surfaced as inline warnings on the processing screen. Each missing file becomes a FLAGGED / HIGH `AuditResult` via `check_missing_receipt()`.

### `engine/ocr.py`

Implements `prd.md > Processing & OCR Extraction` (OCR extraction step)

**Input:** image bytes (one receipt)
**Output:** `OCRResult`

**Implementation:**
```python
import pytesseract
from PIL import Image

# pytesseract config
TESSERACT_CONFIG = "--psm 6"   # assume uniform block of text
CONFIDENCE_THRESHOLD = 0.6
```

**Extraction logic:**
- Open image bytes via `PIL.Image.open(BytesIO(bytes))`
- Run `pytesseract.image_to_data()` to get per-word confidence scores
- Compute `confidence = mean(word_confidences) / 100`
- Run `pytesseract.image_to_string()` for raw text
- Apply regex patterns to extract:
  - `amount`: `r'\$?\d{1,6}[\.,]\d{2}'`
  - `date`: `r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}'`
  - `vendor`: first non-numeric line of raw text (heuristic)
- Returns `OCRResult` with extracted fields (or `None` per field if not found)

**Low-confidence flow:** `confidence < CONFIDENCE_THRESHOLD` → orchestrator surfaces inline recovery UI before continuing that row (see `processing_view.py > OCR Recovery`)

### `engine/rules.py`

Implements `prd.md > Audit Rule Engine`

**Input per function:** one expense row (pd.Series), full pd.DataFrame, OCRResult | None
**Output per function:** `RuleResult`

#### `check_amount_mismatch(row, ocr) -> RuleResult`
- If `ocr` is None or `ocr.amount` is None: skip (handled by missing receipt rule)
- Difference = `abs(row.amount - ocr.amount) / row.amount`
- If difference == 0: OK / NONE
- If 0 < difference ≤ 0.10: UNCERTAIN / LOW — "possible tax, tip, or rounding"
- If difference > 0.10: FLAGGED / HIGH — "+{pct}% mismatch exceeds 10% threshold"
- `detailed_reason`: includes reported amount, OCR amount, calculated difference, threshold reference
- `suggested_action`: "Request clarification; verify non-reimbursable items"

#### `check_duplicate(row, df) -> RuleResult`
- Exact match: same `receipt_file` OR (same `vendor` + `amount` + `date`) with another row → FLAGGED / HIGH
- Fuzzy match: same `vendor` + amount within 5% + date within 3 days → UNCERTAIN / MEDIUM
- No match: OK / NONE
- `duplicate_match_id`: the `expense_id` of the matching row
- `detailed_reason`: side-by-side field comparison for detail panel (all matching fields listed)
- Duplicate confidence score: 1.0 for exact, 0.6–0.9 for fuzzy (based on how many fields match)
- If multiple possible duplicates: strongest match reported, others listed in `detailed_reason`

#### `check_missing_receipt(row, ocr) -> RuleResult`
- If receipt file found and OCR ran: OK / NONE
- If receipt file found but OCR incomplete/low-confidence: UNCERTAIN / LOW
- If receipt file missing (bytes was None from matcher): FLAGGED / HIGH
  - `reason_summary`: `"receipt file not found: {filename}"`

#### `check_category(row, ocr, ai_result) -> RuleResult`
- `ai_result`: output of `ai.py` — `"category_consistent"` | `"category_unclear"` | `"category_mismatch"` | `None`
- Loads `config/categories.json` (approved list)
- If category not in approved list: FLAGGED / MEDIUM (AI not invoked)
- If category in approved list:
  - `ai_result == "category_consistent"`: OK / NONE
  - `ai_result == "category_unclear"`: UNCERTAIN / LOW
  - `ai_result == "category_mismatch"`: FLAGGED / MEDIUM
  - `ai_result == None` (AI unavailable):
    - If category in approved list: UNCERTAIN / LOW — detail panel note: "AI-assisted check unavailable — rule-only result"
    - If category not in approved list: FLAGGED / MEDIUM (rule-only)

#### `check_suspicious_pattern(row, df) -> RuleResult`
- Aggregates all rows with the same `employee_id` across the full DataFrame
- Counts: number of FLAGGED results, repeated duplicate pairs, repeated missing receipts
- One weak signal (repeated similar amounts, frequent small claims): UNCERTAIN / LOW
- Multiple issues (≥ 2 of: repeated duplicates, repeated missing receipts, high FLAGGED count): FLAGGED / MEDIUM
- No issues: OK / NONE
- `detailed_reason`: "N amount mismatches from same employee in past 30 days" (pattern description)

**Multi-rule resolution (in orchestrator):**
- All five rules run per row
- If multiple fire: highest severity wins
- All triggered rule names collected into `AuditResult.triggered_rules`
- `reason_summary`: reason from the highest-severity rule
- `detailed_reason`: concatenated from all triggered rules

### `engine/ai.py`

Implements `prd.md > AI-Assisted Classification`

**Input:** `category: str`, `ocr_raw_text: str`
**Output:** `"category_consistent"` | `"category_unclear"` | `"category_mismatch"` | `None`

**Restricted item fast-path:**
- Load `config/restricted_items.json` (e.g. `["alcohol", "wine", "spirits", "personal care", "gift card"]`)
- If any item in list appears in `ocr_raw_text.lower()`: return `"category_mismatch"` immediately (no API call)

**Groq API call:**
```python
from groq import Groq

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are an expense audit assistant.
Given a declared expense category and the text extracted from a receipt,
determine whether the receipt content is consistent with the category.
Respond with exactly one word: category_consistent, category_unclear, or category_mismatch.
No explanation. No punctuation. One word only."""

USER_PROMPT = f"Category: {category}\nReceipt text: {ocr_raw_text}"

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": USER_PROMPT},
    ],
    max_tokens=10,
    temperature=0,
)
```

**Response validation:** strip and lowercase the response; if not one of the three valid values, treat as `"category_unclear"`.

**Error handling:** wrap entire call in `try/except`; on any exception (timeout, API error, rate limit) return `None` → fallback in `check_category()`.

**Groq docs:** https://console.groq.com/docs/quickstart | https://console.groq.com/docs/models

### `engine/orchestrator.py`

**Input:** `df: pd.DataFrame`, `receipt_map: dict[str, bytes | None]`, `groq_client`
**Output:** `list[AuditResult]`, yields progress events

**Pipeline per row:**
```python
for _, row in df.iterrows():
    try:
        ocr_result  = ocr.extract(receipt_map[row.receipt_file])
        ai_result   = ai.classify(row.category, ocr_result.raw_text) if ocr_result else None
        rule_results = [
            rules.check_amount_mismatch(row, ocr_result),
            rules.check_duplicate(row, df),
            rules.check_missing_receipt(row, ocr_result),
            rules.check_category(row, ocr_result, ai_result),
            rules.check_suspicious_pattern(row, df),
        ]
        audit_result = assemble(row, rule_results, ocr_result, ai_result)
    except Exception as e:
        audit_result = error_result(row, str(e))   # FLAGGED / HIGH / "processing error"
    results.append(audit_result)
```

**Progress events (for processing screen):**
- Step 1 complete: CSV loaded and validated
- Step 2 complete: receipts matched (missing files listed)
- Step 3 complete: all rules run
- Step 4 complete: AI checks done (or skipped/unavailable)

Progress tracked via `st.session_state["processing_step"] = 0..3`

---

## UI Layer

### `app.py`

Single entry point. Reads `st.session_state["step"]` and renders the correct view. ~30 lines.

```python
import streamlit as st
from ui.upload_view import render_upload
from ui.processing_view import render_processing
from ui.results_view import render_results

st.set_page_config(page_title="AI Audit Assistant", layout="wide")

if "step" not in st.session_state:
    st.session_state["step"] = "upload"

step = st.session_state["step"]
if step == "upload":
    render_upload()
elif step == "processing":
    render_processing()
elif step == "results":
    render_results()
```

### Session State Schema

```python
st.session_state = {
    "step":           str,                  # "upload" | "processing" | "results"
    "csv_df":         pd.DataFrame,         # validated expense data
    "receipt_files":  dict[str, bytes],     # filename → image bytes
    "results":        list[AuditResult],    # final audit output
    "selected_row":   str | None,           # expense_id for detail panel
    "filter_status":  str,                  # "All" | "FLAGGED" | "UNCERTAIN" | "OK"
    "search_query":   str,                  # vendor / employee / category search
    "processing_step": int,                 # 0–3 for progress display
}
```

### `ui/upload_view.py`

Implements `prd.md > Upload & Validation`

**Components:**
- `st.file_uploader("Upload expense CSV", type=["csv"])` → triggers immediate schema validation on change
- `st.file_uploader("Upload receipt images", type=["jpg","jpeg","png"], accept_multiple_files=True)`
- Validation error display: `st.error(f"Missing columns: {missing}. Expected: expense_id, employee_id, vendor, amount, date, category, receipt_file")`
- `st.download_button("Download sample CSV template", data=sample_csv_bytes, file_name="sample_expenses.csv")`
- `st.button("Run Audit", disabled=not (csv_valid and receipts_uploaded))` → on click: write to session state, set step = "processing"

### `ui/processing_view.py`

Implements `prd.md > Processing & OCR Extraction`

**Step display:** four labeled rows with icons:
```
✓  Loading expense data
✓  Matching receipts
⟳  Running validation rules   (active step)
   AI-assisted checks
```

Driven by `st.session_state["processing_step"]`. Each step renders a completion marker (✓) or in-progress spinner (⟳) or pending (grey dot).

**Missing receipt warnings:** rendered inline after step 2 completes:
```
⚠ receipt_missing: invoice_4821.jpg — not found in uploaded folder
```
Does not block processing.

**OCR low-confidence recovery:** when `OCRResult.confidence < 0.6` for a row, processing pauses and shows an expander for that entry:
- Option 1: "Accept as UNCERTAIN and continue"
- Option 2: "Edit extracted fields" → inline text inputs for vendor, amount, date
- Option 3: "Replace receipt image" → new `st.file_uploader` for that row
- If no action taken within rerun: auto-accept as UNCERTAIN

**On completion:** set `st.session_state["step"] = "results"`, trigger rerun.

### `ui/results_view.py`

Implements `prd.md > Results Dashboard`, `Detail Panel`, `Export`, `Session Management`

#### Summary Bar

Top of screen. Computed from `st.session_state["results"]`:

```
Total checked: 47  |  ✓ OK: 31  |  ⚑ Flagged: 12  |  △ Uncertain: 4
Total reviewed: $18,432  |  High-risk amount: $4,211
```

All-clear state (zero FLAGGED, zero UNCERTAIN):
```
✔ All expenses passed audit
0 flagged · 0 uncertain · 100% compliant
```
Full table still shown below.

#### Filter & Search Row

```python
col1, col2, col3 = st.columns([1, 1, 2])
filter_status = col1.selectbox("Status", ["All", "FLAGGED", "UNCERTAIN", "OK"])
search_query  = col3.text_input("Search vendor / employee / category")
```

Applied before rendering the table: filter `results` list by `audit_status` and search string match on `vendor`, `employee_id`, `category`.

#### Results Table

Rendered with `st.dataframe`. Columns (in order):
`expense_id` | `vendor` | `amount` | `category` | `status` (badge) | `confidence` | `severity` | `reason_summary`

Default sort: FLAGGED first, then severity HIGH → MEDIUM → LOW within each status group.

Status badges: color-coded via pandas Styler or custom HTML:
- FLAGGED → red background, dark text
- UNCERTAIN → orange background, dark text
- OK → green background, dark text

Selected row: tracked via `st.session_state["selected_row"]`. Clicking a row updates the detail panel without closing it.

#### Detail Panel

Rendered in right column (`st.columns([2, 1])`). Always visible when a row is selected.

**Header:** status badge, confidence score, severity badge, triggered rule name(s)

**Data comparison section** — adapts to triggered rule:

- **Amount mismatch:**
  ```
  Reported:  $150.00
  Receipt:   $120.00
  Difference: $30.00 (+25%)
  Threshold: 10%
  ```

- **Duplicate:** side-by-side table of the two matching rows; matching fields highlighted; duplicate confidence score; strongest match first; "other possible matches" collapsed in expander

- **Missing receipt:**
  ```
  Expected file: invoice_4821.jpg
  Status: not found in uploaded folder
  ```

- **Invalid category:**
  ```
  Declared: Office Supplies
  AI classification: category_mismatch
  Reason: receipt contains alcohol-related items
  ```

- **Suspicious pattern:**
  ```
  3 amount mismatches from same employee in this dataset
  Related entries: #4801, #4812, #4821
  ```

**AI-assisted note:** shown only if `ai_assisted = True`:
```
AI note: Receipt content is inconsistent with declared category "Office Supplies"
```

**Suggested action:** always shown at bottom of panel.

#### Export

```python
st.radio("Export:", ["All results", "Flagged only", "Uncertain only"])
st.download_button("Export CSV", data=csv_bytes, file_name="audit_report.csv")
st.caption("This report is a first-pass audit assistant and is not a replacement for human review.")
```

Exported CSV columns (all 19 fields):
- **Original:** `expense_id`, `employee_id`, `vendor`, `amount`, `date`, `category`, `receipt_file`
- **Audit:** `audit_status`, `severity`, `confidence`, `triggered_rules`, `reason_summary`, `detailed_reason`, `suggested_action`, `matched_receipt_file`, `duplicate_match_id`, `ai_assisted`, `generated_at`

#### New Audit Button

```python
if st.button("New Audit"):
    for key in ["csv_df", "receipt_files", "results", "selected_row",
                "filter_status", "search_query", "processing_step"]:
        st.session_state.pop(key, None)
    st.session_state["step"] = "upload"
    st.rerun()
```

---

## Config & Assets

### `config/categories.json`

Default approved expense categories. Loaded by `check_category()` in `rules.py`. Overridable by replacing this file.

```json
[
  "Meals",
  "Travel",
  "Accommodation",
  "Transportation",
  "Office Supplies",
  "Software",
  "Training",
  "Marketing",
  "Client Entertainment",
  "Utilities",
  "Equipment",
  "Professional Services"
]
```

### `config/restricted_items.json`

Items whose presence in OCR text triggers an immediate `category_mismatch` without an API call. Checked case-insensitively against `ocr_result.raw_text`.

```json
[
  "alcohol",
  "wine",
  "beer",
  "spirits",
  "liquor",
  "personal care",
  "gift card",
  "tobacco",
  "gambling"
]
```

### `assets/sample_expenses.csv`

Pre-built CSV template with correct headers and 3–5 example rows. Generated once by `parser.generate_sample_csv()` and committed to the repo. Available as a download on the upload screen.

---

## File Structure

```
Devpost-Hackathon/
├── src/
│   ├── app.py                        # Streamlit entry point; step controller
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── parser.py                 # CSV parsing + schema validation
│   │   ├── matcher.py                # receipt filename → image bytes mapping
│   │   ├── ocr.py                    # pytesseract extraction + confidence
│   │   ├── rules.py                  # 5 deterministic audit rules
│   │   ├── ai.py                     # Groq category classification
│   │   └── orchestrator.py           # pipeline runner → list[AuditResult]
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                # AuditResult, OCRResult, RuleResult, enums
│   └── ui/
│       ├── __init__.py
│       ├── upload_view.py            # upload screen
│       ├── processing_view.py        # processing progress + OCR recovery
│       └── results_view.py           # dashboard, detail panel, export
├── config/
│   ├── categories.json               # default approved category list
│   └── restricted_items.json         # restricted items for fast-path mismatch
├── assets/
│   └── sample_expenses.csv           # downloadable template
├── docs/
│   ├── learner-profile.md
│   ├── scope.md
│   ├── prd.md
│   └── spec.md                       # this file
├── submission/
│   ├── additional-info.md
│   ├── devpost-checklist.md
│   └── project-story.md
├── process-notes.md
├── requirements.txt
├── packages.txt                      # tesseract-ocr (for Streamlit Community Cloud)
├── .gitignore                        # must include .streamlit/secrets.toml
└── .streamlit/
    ├── config.toml                   # page title, layout="wide", light theme
    └── secrets.toml                  # GROQ_API_KEY — local only, never committed
```

---

## Key Technical Decisions

### 1. Pure Streamlit over FastAPI + Streamlit

**Decision:** Drop FastAPI; run all processing logic as imported Python modules within the Streamlit process.

**Why:** Streamlit Community Cloud runs exactly one process. FastAPI would require a separate server — either a second free-tier host (Render) with 10–30s cold starts, or experimental ASGI mounting. For a demo where judges click a live URL, cold starts are a real risk. Clean module separation (`engine/`, `models/`, `ui/`) delivers the same structural clarity without HTTP overhead.

**Tradeoff accepted:** No REST API layer. Logic is not independently callable via HTTP. Acceptable for demo scope.

### 2. Groq (Llama 3.3 70B) over OpenAI

**Decision:** Use Groq's free tier with Llama 3.3 70B for category classification.

**Why:** OpenAI has no meaningful free tier. Groq provides ~14,400 requests/day free, is OpenAI API-compatible, and Llama 3.3 70B is more than capable of a 3-way classification task returning one word. The system prompt constrains output to `category_consistent | category_unclear | category_mismatch` — no frontier model needed.

**Tradeoff accepted:** Groq is a third-party inference provider. If unavailable, the AI fallback activates. Provider can be swapped by changing one env var and one model string.

### 3. Severity grounded in AppZen's LOW/MEDIUM/HIGH model

**Decision:** Severity determined by rule type, not dollar amount. HIGH = clear fraud signals (exact duplicate, mismatch >10%, missing receipt). MEDIUM = policy ambiguity (invalid category, suspicious pattern, fuzzy duplicate). LOW = data quality / uncertain cases.

**Why:** AppZen (the enterprise benchmark cited in scope.md) uses this exact three-tier model grounded in impact × likelihood. Defensible to judges with knowledge of the industry. Dollar-amount-based severity was rejected because a $10 exact duplicate is more suspicious than a $200 tip discrepancy.

**Tradeoff accepted:** Severity is not configurable in the UI (out of scope). Thresholds are hardcoded; the JSON configs cover category and restricted item customization only.

---

## Dependencies & External Services

| Service / Library | Purpose | Free tier | Docs |
|---|---|---|---|
| Streamlit Community Cloud | Hosting + deployment | Unlimited public apps | https://docs.streamlit.io/deploy/streamlit-community-cloud |
| Groq API | LLM inference (Llama 3.3 70B) | ~14,400 req/day | https://console.groq.com/docs/quickstart |
| pytesseract | Python wrapper for Tesseract | Free / open source | https://github.com/madmaze/pytesseract |
| Tesseract OCR | System OCR binary | Free / open source | https://tesseract-ocr.github.io/tessdoc/ |
| pandas | CSV parsing, data manipulation | Free / open source | https://pandas.pydata.org/docs/ |
| Pillow | Image loading for OCR | Free / open source | https://pillow.readthedocs.io |
| GitHub | Source code + Streamlit Cloud integration | Free | https://github.com |

**API key setup:**
1. Create a free Groq account at https://console.groq.com
2. Generate an API key (Dashboard → API Keys)
3. Local: add to `.streamlit/secrets.toml` as `GROQ_API_KEY = "gsk_..."`
4. Deployed: add via Streamlit Community Cloud app settings → Secrets

**`requirements.txt` (minimum):**
```
streamlit>=1.35
pandas>=2.2
pytesseract>=0.3.10
Pillow>=10.0
groq>=0.9
```

**`packages.txt` (Streamlit Community Cloud system packages):**
```
tesseract-ocr
```

---

## Open Issues

All three open questions from `prd.md > Open Questions` are now resolved:

| Question | Resolution |
|---|---|
| How is severity determined? | Rule-type-based: HIGH (exact dup, mismatch >10%, missing receipt), MEDIUM (invalid category, suspicious pattern, fuzzy dup), LOW (mismatch 1–10%, low OCR confidence, category unclear) |
| What happens when AI is unavailable? | Category check falls back to approved-list-only: in-list → UNCERTAIN/LOW with "AI unavailable" note; not-in-list → FLAGGED/MEDIUM. `ai_assisted = false` in export. |
| What is the default approved category list? | 12 categories in `config/categories.json`: Meals, Travel, Accommodation, Transportation, Office Supplies, Software, Training, Marketing, Client Entertainment, Utilities, Equipment, Professional Services |

**Architecture risks to watch during build:**

1. **OCR low-confidence recovery UX in Streamlit** — the inline pause-and-edit flow during processing is the most complex UI interaction in the app. Streamlit's rerun model makes mid-pipeline pausing tricky. If it proves too complex, simplify: run OCR over all receipts first, surface all low-confidence cases at once before proceeding to rules.

2. **Suspicious pattern rule requires full DataFrame context** — `check_suspicious_pattern()` aggregates across all rows, meaning it can only run after OCR and the first four rules complete for all rows. Orchestrator must run it in a second pass or accumulate intermediate results before calling it.

3. **Streamlit `st.dataframe` row selection** — native row click selection in `st.dataframe` is limited. Use `st.data_editor` with `on_change` or a radio-button column to track `selected_row` in session state. Test this early in the build.
