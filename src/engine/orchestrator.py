from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from engine import ai, ocr, rules
from engine.matcher import match_receipts
from models.schemas import AuditResult, AuditStatus, Severity

_SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2, Severity.NONE: 3}
_STATUS_ORDER   = {AuditStatus.FLAGGED: 0, AuditStatus.UNCERTAIN: 1, AuditStatus.OK: 2}


def _highest(rule_results: list):
    return min(rule_results, key=lambda r: (_STATUS_ORDER[r.status], _SEVERITY_ORDER[r.severity]))


def _assemble(row: pd.Series, rule_results: list, ocr_result, ai_result) -> AuditResult:
    triggered = [r for r in rule_results if r.status != AuditStatus.OK]
    if not triggered:
        triggered = rule_results[:1]  # at least one entry (the OK)

    best = _highest(triggered if any(r.status != AuditStatus.OK for r in rule_results) else rule_results)
    all_triggered_names = [r.rule_name for r in rule_results if r.status != AuditStatus.OK]
    combined_detail = "\n\n".join(
        f"[{r.rule_name}]\n{r.detailed_reason}"
        for r in rule_results if r.status != AuditStatus.OK
    ) or rule_results[0].detailed_reason

    dup_id = next((r.duplicate_match_id for r in rule_results if r.duplicate_match_id), None)

    return AuditResult(
        expense_id=str(row["expense_id"]),
        employee_id=str(row["employee_id"]),
        vendor=str(row["vendor"]),
        amount=float(row["amount"]),
        date=str(row["date"]),
        category=str(row["category"]),
        receipt_file=str(row["receipt_file"]),
        audit_status=best.status,
        severity=best.severity,
        confidence=best.confidence,
        triggered_rules=all_triggered_names,
        reason_summary=best.reason_summary,
        detailed_reason=combined_detail,
        suggested_action=best.suggested_action,
        matched_receipt_file=str(row["receipt_file"]),
        ocr_result=ocr_result,
        duplicate_match_id=dup_id,
        ai_assisted=ai_result is not None,
        ai_note=f"AI classification: {ai_result}" if ai_result else None,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _error_result(row: pd.Series, error_msg: str) -> AuditResult:
    return AuditResult(
        expense_id=str(row.get("expense_id", "UNKNOWN")),
        employee_id=str(row.get("employee_id", "")),
        vendor=str(row.get("vendor", "")),
        amount=float(row.get("amount", 0)),
        date=str(row.get("date", "")),
        category=str(row.get("category", "")),
        receipt_file=str(row.get("receipt_file", "")),
        audit_status=AuditStatus.FLAGGED,
        severity=Severity.HIGH,
        confidence=0.0,
        triggered_rules=[],
        reason_summary=f"processing error: {error_msg}",
        detailed_reason=f"processing error: {error_msg}",
        suggested_action="Review raw data; contact system administrator.",
        matched_receipt_file=str(row.get("receipt_file", "")),
        ocr_result=None,
        duplicate_match_id=None,
        ai_assisted=False,
        ai_note=None,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def run_audit(df: pd.DataFrame, receipt_map: dict, groq_client=None) -> list:
    results = []
    preliminary = []  # list of dicts for suspicious pattern second pass

    st.session_state["processing_step"] = 0

    # Pass 1: OCR, AI, and first four rules
    for _, row in df.iterrows():
        try:
            img_bytes = receipt_map.get(row["receipt_file"])
            ocr_result = ocr.extract(img_bytes) if img_bytes else None
            ai_result = ai.classify(row["category"], ocr_result.raw_text) if ocr_result else None

            rule_results = [
                rules.check_amount_mismatch(row, ocr_result),
                rules.check_duplicate(row, df),
                rules.check_missing_receipt(row, ocr_result),
                rules.check_category(row, ocr_result, ai_result),
            ]

            triggered_names = [r.rule_name for r in rule_results if r.status != AuditStatus.OK]
            best = _highest([r for r in rule_results if r.status != AuditStatus.OK] or rule_results)

            preliminary.append({
                "expense_id": str(row["expense_id"]),
                "audit_status": best.status,
                "triggered_rules": triggered_names,
                "_row": row,
                "_rule_results": rule_results,
                "_ocr_result": ocr_result,
                "_ai_result": ai_result,
            })

        except Exception as e:
            preliminary.append({
                "expense_id": str(row.get("expense_id", "UNKNOWN")),
                "audit_status": AuditStatus.FLAGGED,
                "triggered_rules": [],
                "_row": row,
                "_rule_results": None,
                "_ocr_result": None,
                "_ai_result": None,
                "_error": str(e),
            })

    st.session_state["processing_step"] = 2

    # Pass 2: suspicious pattern (needs preliminary results from all rows)
    for entry in preliminary:
        row = entry["_row"]
        if entry.get("_error"):
            results.append(_error_result(row, entry["_error"]))
            continue
        try:
            pattern_rule = rules.check_suspicious_pattern(row, df, preliminary)
            all_rules = entry["_rule_results"] + [pattern_rule]
            results.append(_assemble(row, all_rules, entry["_ocr_result"], entry["_ai_result"]))
        except Exception as e:
            results.append(_error_result(row, str(e)))

    st.session_state["processing_step"] = 3

    return results
