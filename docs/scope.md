# Scope.md — AI Auditor Assistant

## Project Overview
We are building an **AI Auditor Assistant**, a web-based demo application that automates the first-pass review of business expenses by auditing complete expense datasets rather than relying on manual sampling.

The system compares uploaded expense spreadsheets and receipt images, applies OCR to extract receipt data, and validates entries using deterministic audit rules. It flags suspicious, invalid, or uncertain expenses for human review.

The product is positioned as an **AI-assisted auditing tool**, not a replacement for auditors, with human reviewers retaining final decision authority.

---

## Problem Statement
Traditional auditing often relies on sampling subsets of expense data due to time and resource constraints, which can miss duplicate claims, suspicious patterns, and policy violations across the broader dataset.

Manual verification of receipts is also slow and prone to human error.

---

## Target Users
- Professional auditors
- Small business owners
- Finance / administration teams

---

## In Scope (MVP Features)
### Input & Upload
- Upload business expense spreadsheet (CSV)
- Upload receipt images

### OCR & Extraction
- Extract structured receipt data using OCR/AI:
  - Merchant name
  - Date
  - Total amount
  - Item descriptions (where available)

### Validation & Audit Engine
- Compare receipt data against spreadsheet entries
- Apply predefined JSON-configured audit rules
- Detect duplicate or suspicious expense entries
- Mark uncertain cases when OCR confidence/recognition is low

### Output
- Generate structured audit report with:
  - **OK**
  - **Flagged**
  - **Uncertain**
- Include reason/explanation for each flagged or uncertain item

---

## Audit Rules Included in MVP
- Amount mismatch detection
- Duplicate receipt / duplicate expense detection
- Missing receipt detection
- Invalid / inappropriate expense category detection
- Optional stretch: basic suspicious pattern checks against prior/sample data

---

## Out of Scope
- User-defined rule creation / editing UI
- Production-scale infrastructure
- Database persistence
- Real accounting software integrations
- Authentication / multi-user system
- Advanced ML anomaly/fraud detection models
- Enterprise compliance / tax reporting

---

## Technical Constraints / Design Decisions
- AI/OCR used only for receipt extraction
- Deterministic local logic used for final audit decisions
- Human remains in the loop for uncertain cases
- Rules stored in static JSON configuration for MVP
- No dynamic rule authoring in MVP

---

## Success Criteria
The MVP is considered successful if:

1. Given a sample expense CSV and receipt set, the system outputs a complete audit report.
2. At least **3 audit rule types** function correctly:
   - Amount mismatch
   - Duplicate detection
   - Missing receipt detection
3. Each flagged/uncertain result includes a clear explanation.
4. The demo workflow runs end-to-end without manual intervention:
   - Upload → OCR → Audit → Report
5. The app demonstrates the feasibility of full-dataset AI-assisted auditing.

---
