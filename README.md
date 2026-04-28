# Next Audit

**Live Demo:** https://nexaudit.streamlit.app/

Next Audit is an AI-assisted expense auditing demo that helps auditors and business owners review complete expense datasets instead of relying solely on manual sampling. Users upload expense spreadsheets and receipt images, and the system performs OCR extraction, applies audit rules, and flags suspicious or inconsistent entries for review.

---

## Overview

Traditional expense auditing is time-consuming and often limited to checking only a sample of records. Next Audit demonstrates how AI-assisted tooling can automate first-pass auditing by validating all submitted expense data against receipts and predefined business rules.

The application is designed as an **auditor assistant**, not a replacement for human auditors. It helps reduce manual effort while keeping final judgement in human hands.

---

## Features

- Upload expense spreadsheets (CSV)
- Upload receipt images/invoices
- OCR extraction of receipt information
- Receipt-to-expense matching
- Rule-based auditing engine
- Duplicate expense detection
- Amount mismatch detection
- Missing receipt detection
- Structured audit report with:
  - **OK**
  - **Flagged**
  - **Uncertain**

---

## How It Works

1. Upload a CSV containing expense records  
2. Upload corresponding receipt images  
3. OCR extracts receipt data  
4. Matching engine aligns receipts with expense entries  
5. Rule engine validates entries using predefined audit rules  
6. Results are displayed in a structured audit report  

---

## Tech Stack

- **Frontend/UI:** Streamlit
- **Backend:** Python
- **OCR:** AI/OCR-based receipt extraction
- **Validation Engine:** Deterministic JSON-configured rule engine

---

## Project Structure

```text
docs/            # Hackathon planning documents
src/             # Application source code
data/            # Sample CSVs and receipt images
submission/      # Devpost submission materials
