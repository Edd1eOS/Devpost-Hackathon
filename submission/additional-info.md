# Additional Info — Next Audit

## Current MVP Limitations
This hackathon submission is a demo/MVP and does not represent the full intended production system.

Current limitations include:
- Static predefined audit rules
- No user-created rule configuration UI
- Limited OCR/anomaly detection implementation
- No database persistence
- No accounting software integrations

---

## Planned Future Enhancements
### AI-Assisted Anomaly Detection
Future versions will include AI models that analyze receipt/expense patterns to detect anomalies and suspicious behaviours beyond rule-based checks.

---

### Advanced OCR Pipeline
OCR will be upgraded to production-grade AI receipt understanding to improve extraction reliability across varying receipt formats and quality levels.

---

### Dynamic Rule Configuration
Companies will be able to define and manage their own expense policies and audit rules directly through the platform.

---

## Design Philosophy
We intentionally chose a hybrid architecture:
- AI handles flexible/unstructured tasks (OCR, anomaly assistance)
- Deterministic local logic handles final audit decisions

This improves reliability and reduces hallucination risk in audit-critical workflows.

---
