# AI Audit Assistant — Product Requirements

## Problem Statement

Professional auditors reviewing large expense datasets are forced to rely on manual sampling, which means duplicates, mismatches, and policy violations routinely slip through. Existing tools like AppZen provide 100% coverage but produce opaque verdicts with no explanation — auditors can't see why something was flagged or trust the output enough to act on it. This project targets that gap: a lightweight, explainable first-pass audit system that flags every expense with structured reasoning, so auditors can investigate efficiently rather than guess.

---

## User Stories

### Epic: Upload & Validation

- As a professional auditor, I want to upload a CSV of expense entries and a folder of receipt images so that the system has everything it needs to run a complete audit.
  - [ ] Upload screen shows two clearly labeled upload zones: one for the CSV file, one for the receipt image folder
  - [ ] Upload screen displays instructions explaining that the CSV must include a `receipt_file` column mapping each row to its corresponding image filename
  - [ ] A "Run Audit" button is visible but disabled until both files are provided
  - [ ] Optionally, a downloadable sample CSV template is available on the upload screen

- As a professional auditor, I want the system to validate my CSV immediately on upload so that I know right away if my file is missing required columns.
  - [ ] On CSV upload, the system immediately checks for required columns: `expense_id`, `vendor`, `amount`, `date`, `category`, `receipt_file`
  - [ ] If required columns are missing, the system blocks further action and shows a specific error listing the missing column names
  - [ ] The error message displays the expected schema so the auditor knows exactly what to fix
  - [ ] Processing does not begin until the CSV passes validation

### Epic: Processing & OCR Extraction

- As a professional auditor, I want to see step-by-step progress during processing so that I understand what the system is doing and trust that it is working.
  - [ ] Processing screen shows four labeled steps in sequence: "Loading expense data", "Matching receipts", "Running validation rules", "AI-assisted checks (if needed)"
  - [ ] Each step shows an in-progress indicator while active and a completion marker when done
  - [ ] The screen is text-based with no complex animations
  - [ ] If a receipt file listed in the CSV is not found in the uploaded folder, processing continues — the missing file is treated as an audit finding, not a system error
  - [ ] A warning is surfaced during processing for each missing receipt file, identifying the filename, without blocking the audit

- As a professional auditor, I want the system to recover gracefully when OCR reads a receipt with low confidence so that I can decide whether to fix it or accept the uncertainty.
  - [ ] When OCR confidence is low on a specific receipt, the system displays a low-confidence warning inline for that entry
  - [ ] The warning identifies which fields are uncertain or missing
  - [ ] The auditor is offered three recovery options: (1) Accept as UNCERTAIN and continue, (2) Edit the extracted fields inline, (3) Replace the receipt image
  - [ ] If the auditor takes no action, the entry is treated as UNCERTAIN and processing continues
  - [ ] OCR failures are treated as audit findings, not system failures

### Epic: Audit Rule Engine

- As a professional auditor, I want the system to automatically detect amount mismatches between reported expenses and receipt amounts so that I don't have to compare figures manually.
  - [ ] If reported amount matches receipt amount exactly (or within a trivial rounding tolerance), status is OK
  - [ ] If the difference is between 0% and 10%, status is UNCERTAIN (possible tax, tip, or rounding)
  - [ ] If the difference exceeds 10%, status is FLAGGED
  - [ ] The reason displayed includes the reported amount, receipt amount, calculated difference, and the 10% threshold

- As a professional auditor, I want the system to detect duplicate expense submissions so that I can identify potential double-billing.
  - [ ] If no matching duplicate is found, status is OK
  - [ ] If a row shares the same vendor and a similar amount/date with another row (but is not identical), status is UNCERTAIN
  - [ ] If a row shares an identical `receipt_file`, the same receipt ID, or an exact match on vendor + amount + date with another row, status is FLAGGED
  - [ ] Detail panel for a FLAGGED duplicate shows both matching entries side by side, with matching fields (vendor, amount, date, receipt_file) highlighted
  - [ ] Duplicate confidence score is shown
  - [ ] If multiple possible duplicates exist, the strongest match is shown first; additional matches are collapsed under "other possible matches"

- As a professional auditor, I want the system to flag expenses with missing or unreadable receipts so that I can follow up on unsupported claims.
  - [ ] If a receipt file exists and all required fields are readable, status is OK
  - [ ] If a receipt file exists but OCR/extraction is incomplete or low-confidence, status is UNCERTAIN
  - [ ] If a receipt file is missing (filename in CSV but not uploaded) or cannot be opened, status is FLAGGED
  - [ ] Reason displayed: "receipt file not found: [filename]" or "receipt unreadable: [filename]"

- As a professional auditor, I want the system to flag expenses with invalid or mismatched categories so that I can catch policy violations.
  - [ ] The system maintains a default approved category list (standard business expense categories, e.g. Meals, Travel, Office Supplies, Accommodation, Transportation, Software, Training)
  - [ ] An optional configuration file can override the default approved category list to match company policy
  - [ ] If the category is in the approved list AND AI confirms the receipt content is semantically consistent, status is OK
  - [ ] If the category is in the approved list BUT AI returns `category_unclear`, status is UNCERTAIN
  - [ ] If the category is not in the approved list OR AI returns `category_mismatch`, status is FLAGGED
  - [ ] Restricted item detection: if receipt content contains items explicitly incompatible with the claimed category (e.g. alcohol under "Office Supplies"), AI returns `category_mismatch`

- As a professional auditor, I want the system to detect suspicious behavior patterns across multiple entries so that I can identify systematic misuse, not just isolated errors.
  - [ ] If no repeated issues are found for the same user or vendor, status is OK
  - [ ] If one weak signal is present — such as repeated similar amounts or frequent small claims from the same user — status is UNCERTAIN
  - [ ] If multiple issues are found from the same user (repeated duplicates, repeated missing receipts, or an unusually high number of FLAGGED entries), status is FLAGGED
  - [ ] The pattern detected is described in the detail panel: e.g. "3 amount mismatches from the same employee in the past 30 days"

### Epic: AI-Assisted Classification

- As a professional auditor, I want AI to help evaluate ambiguous category cases so that the system can catch semantic mismatches a rule alone cannot detect.
  - [ ] AI is only invoked for category validation — not for other rules
  - [ ] AI receives the declared category and available receipt content (vendor name, item descriptions) and returns exactly one of three structured values: `category_consistent`, `category_unclear`, or `category_mismatch`
  - [ ] The rule engine maps the AI response to a final status — AI does not determine the final status directly
  - [ ] If AI assistance was used, the detail panel shows an "AI-assisted note" with the AI's reasoning
  - [ ] Each exported row includes an `ai_assisted` field (true/false) so the audit trail is transparent

### Epic: Results Dashboard

- As a professional auditor, I want to see a summary of the full audit at a glance so that I immediately understand the risk picture before diving into individual entries.
  - [ ] Summary bar at the top of the results screen shows: total expenses checked, OK count, FLAGGED count, UNCERTAIN count, total amount reviewed, and total high-risk amount (sum of FLAGGED entries)
  - [ ] If zero expenses are FLAGGED and zero are UNCERTAIN, the summary bar is replaced with a prominent all-clear state: "✔ All expenses passed audit" with the line "0 flagged · 0 uncertain · 100% compliant"
  - [ ] In the all-clear state, the full results table is still accessible below the summary for reference

- As a professional auditor, I want to filter and sort expenses by status and risk so that I can focus on what matters most.
  - [ ] Filter controls allow filtering by status: All / FLAGGED / UNCERTAIN / OK
  - [ ] Sort controls allow sorting by severity (high → low by default)
  - [ ] Search field allows filtering by vendor, employee, or category
  - [ ] FLAGGED entries appear first by default before any user filtering

- As a professional auditor, I want to see all expense results in a clear table so that I can scan the full dataset efficiently.
  - [ ] Results table columns: expense_id, vendor, amount, category, status badge (color-coded), confidence score, severity, short reason
  - [ ] Status badges: OK (green), FLAGGED (red), UNCERTAIN (orange)
  - [ ] The currently selected row is visually highlighted
  - [ ] Table remains visible when the detail panel is open

### Epic: Detail Panel

- As a professional auditor, I want to click any row and see the full explanation in a side panel so that I can investigate flagged entries without losing my place in the table.
  - [ ] Clicking any row opens a right-side detail panel; the results table remains fully visible
  - [ ] Detail panel shows: status badge, confidence score, severity, triggered rule name, data comparison section, AI-assisted note (if applicable), detected pattern description, and suggested next action
  - [ ] Data comparison section adapts to the triggered rule:
    - Amount mismatch: CSV reported amount vs receipt amount, calculated difference, 10% threshold reference
    - Duplicate: side-by-side entry comparison with matching fields highlighted, duplicate confidence, strongest match first, other possible matches collapsed
    - Missing receipt: filename that was expected but not found
    - Invalid category: declared category, AI-returned classification, reason
    - Suspicious pattern: list of related entries that contributed to the flag, with counts
  - [ ] Clicking a different row updates the detail panel without closing it

### Epic: Export

- As a professional auditor, I want to export the full audit results as a CSV so that I can include the report in my documentation and share findings with the team.
  - [ ] Export button is visible at the bottom of the results screen
  - [ ] By default, the export includes all expense rows (not only flagged)
  - [ ] Before exporting, the auditor can choose: export all results / export flagged only / export uncertain only
  - [ ] Exported CSV includes all original fields: `expense_id`, `employee_id`, `vendor`, `amount`, `date`, `category`, `receipt_file`
  - [ ] Exported CSV includes all audit fields: `audit_status`, `severity`, `confidence`, `triggered_rules`, `reason_summary`, `detailed_reason`, `suggested_action`, `matched_receipt_file`, `duplicate_match_id` (if applicable), `ai_assisted`, `generated_at`
  - [ ] A disclaimer is visible near the export button: "This report is a first-pass audit assistant and is not a replacement for human review."

### Epic: Session Management

- As a professional auditor, I want to start a new audit after reviewing results so that I can audit a different dataset without refreshing or navigating manually.
  - [ ] A "New Audit" button is visible on the results screen
  - [ ] Clicking "New Audit" returns the app to the upload screen in a clean state
  - [ ] No data from the previous session is carried over

---

## What We're Building

Everything below is required for a complete, demonstrable audit assistant within 3–4 hours:

1. **Upload screen** — CSV upload zone, receipt folder upload zone, required column instructions, fail-fast CSV schema validation with specific error messages, optional downloadable sample template, "Run Audit" button
2. **Processing screen** — four-step sequential progress display (loading data → matching receipts → running rules → AI checks), completion markers per step, missing receipt warning without blocking
3. **OCR extraction** — receipt images processed to extract vendor, amount, date, item descriptions; low-confidence recovery flow (accept / edit inline / replace image)
4. **Five-rule validation engine** — amount mismatch (10% threshold), duplicate detection (exact + fuzzy), missing receipt, invalid category (approved list + AI semantic check), suspicious patterns (per-user aggregation)
5. **Controlled AI layer** — category validation only; returns `category_consistent` / `category_unclear` / `category_mismatch`; maps to status via rule engine; AI note displayed in detail panel
6. **Results dashboard** — summary bar with counts and amounts, all-clear state for zero-flag results, filter by status, sort by severity, search by vendor/employee/category, color-coded status badges, FLAGGED-first default sort
7. **Detail panel** — right-side panel, table stays visible, rule-specific data comparison, duplicate side-by-side view, suggested action, AI note when applicable
8. **CSV export** — all rows by default, optional filter (all / flagged / uncertain), full original + audit column set, disclaimer text
9. **New Audit flow** — button on results screen, returns to clean upload state

---

## What We'd Add With More Time

- **Visual receipt-mapping interface** — auto-match receipts to CSV rows with color-coded confidence, drag-and-drop correction, confirmation step. Reduces friction for users who haven't pre-organized their data.
- **Graphical rule configuration UI** — lets auditors define or modify rules without editing JSON. High value for non-technical users.
- **PDF export** — formatted audit report. Higher polish for formal reporting contexts.
- **AI fallback behavior** — graceful degradation when the AI layer is unavailable (e.g., API timeout). Currently undefined; category validation would fall back to rule-only status.
- **Auditor notes** — ability to annotate individual flagged entries with comments before exporting.
- **Severity tuning** — configurable thresholds for severity levels (LOW / MEDIUM / HIGH) per rule type.
- **Dark mode** — light mode only for this build.
- **Accounting software integrations** — QuickBooks, SAP, etc. Out of scope for demo scale.

---

## Non-Goals

- **UI-based rule creation** — Rules are hardcoded in the system with JSON configuration for overrides. No graphical interface for defining new rules. Reason: builds on audit logic complexity without contributing to the core demo story.
- **Persistent database** — Session-based only. No data is stored between runs. Reason: adds infrastructure complexity with no demo value.
- **Multi-user authentication** — Single session, no login system. Reason: not relevant to the audit workflow being demonstrated.
- **Enterprise-scale infrastructure** — This is a demo-scale system. No concurrency handling, queue management, or horizontal scaling.
- **Complex ML anomaly detection** — AI is constrained to structured category classification. No freeform models or unsupervised anomaly detection.

---

## Open Questions

- **How is severity (LOW / MEDIUM / HIGH) determined?** Is it based on the rule type, the amount involved, or both? This needs an answer before `/spec` because severity is displayed in the table and exported in the CSV.
- **What happens when the AI layer is unavailable?** If the API is down or times out, should category validation fall back to rule-only (OK/UNCERTAIN/FLAGGED based on approved list alone), or should affected entries be marked UNCERTAIN by default? Needs an answer before `/spec`.
- **What is the exact default approved category list?** The specific category names need to be decided so the rule engine can be implemented precisely. Can be decided at `/spec` time.
