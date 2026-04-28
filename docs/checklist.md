# Checklist.md — AI Auditor Assistant Build Plan

## Planning / Documentation
- Finalize project idea
- Define scope
- Create PRD
- Create technical specification
- Break project into build tasks

---

## Demo Data Preparation
- Collect / create sample receipts
- Create sample expense CSV
- Add intentional edge cases:
  - Duplicate expense
  - Amount mismatch
  - Missing receipt
  - Invalid expense category

---

## Core Development
### Upload System
- Implement CSV upload
- Implement receipt upload

### OCR Module
- Integrate OCR extraction
- Parse OCR output into structured fields

### Matching Logic
- Match receipts to spreadsheet entries

### Rule Engine
- Implement JSON rule parser
- Implement amount mismatch rule
- Implement duplicate detection rule
- Implement missing receipt rule
- Implement invalid expense rule

### Output
- Build structured audit report formatter
- Add reasoning to flagged/uncertain items

---

## Testing
- Test OCR extraction on sample receipts
- Test each audit rule independently
- Test end-to-end audit workflow

---

## Polish / Submission
- Improve UI/UX of demo
- Create README run instructions
- Prepare Devpost submission materials

---

## Team Responsibilities
### Muhammad
- Product ideation
- Documentation / planning
- Architecture / scope definition

### Eddie
- Core implementation / development
- Technical integration
- Deployment / demo preparation
