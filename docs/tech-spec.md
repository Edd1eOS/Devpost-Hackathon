# Tech-Spec.md — Next Audit

## Architecture Overview
Next Audit uses a lightweight single-application architecture designed for rapid prototyping and demo deployment.

The application is built entirely in Python with a Streamlit frontend and no separate backend server.  
All business logic, OCR processing, matching, and auditing run within the same application runtime.

Pipeline:

Upload Inputs → OCR Extraction → Matching Engine → Rule Engine → Audit Report

---

## Technology Stack

### Frontend / UI
- **Streamlit**
- Handles file uploads, user interaction, and result display

### Backend
- **Python Only**
- No separate API/backend server

### OCR / AI
- **Groq LLM API**
- Used for OCR / structured receipt extraction from uploaded receipt images

### Configuration
- **JSON-based rule configuration**
- Rules stored statically in `rules.json`

---

## Environment Variables

Required:

```env
GROQ_API_KEY=your_api_key_here
