import json
import os
from datetime import datetime, timedelta

import pandas as pd

from models.schemas import AuditStatus, RuleResult, Severity

_CATEGORIES_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "config", "categories.json")
)


def _load_categories() -> list:
    with open(_CATEGORIES_PATH) as f:
        return json.load(f)


def _ok(rule_name: str) -> RuleResult:
    return RuleResult(
        status=AuditStatus.OK,
        severity=Severity.NONE,
        confidence=1.0,
        rule_name=rule_name,
        reason_summary="",
        detailed_reason="",
        suggested_action="",
    )


# ---------------------------------------------------------------------------
# 1. Amount mismatch
# ---------------------------------------------------------------------------

def check_amount_mismatch(row: pd.Series, ocr) -> RuleResult:
    rule = "check_amount_mismatch"
    if ocr is None or ocr.amount is None:
        return _ok(rule)

    reported = float(row["amount"])
    receipt = float(ocr.amount)
    if reported == 0:
        return _ok(rule)

    diff = abs(reported - receipt) / reported
    pct = round(diff * 100, 1)

    if diff == 0:
        return _ok(rule)

    if diff <= 0.10:
        return RuleResult(
            status=AuditStatus.UNCERTAIN,
            severity=Severity.LOW,
            confidence=0.7,
            rule_name=rule,
            reason_summary=f"possible rounding/tip: {pct}% difference",
            detailed_reason=(
                f"Reported amount: ${reported:.2f}\n"
                f"Receipt amount:  ${receipt:.2f}\n"
                f"Difference:      ${abs(reported - receipt):.2f} ({pct}%)\n"
                f"Threshold:       10% — below threshold; could be tax, tip, or rounding."
            ),
            suggested_action="Verify non-reimbursable items (tax, tip, service charge).",
        )

    return RuleResult(
        status=AuditStatus.FLAGGED,
        severity=Severity.HIGH,
        confidence=0.95,
        rule_name=rule,
        reason_summary=f"+{pct}% mismatch exceeds 10% threshold",
        detailed_reason=(
            f"Reported amount: ${reported:.2f}\n"
            f"Receipt amount:  ${receipt:.2f}\n"
            f"Difference:      ${abs(reported - receipt):.2f} ({pct}%)\n"
            f"Threshold:       10% — exceeds threshold; significant discrepancy detected."
        ),
        suggested_action="Request clarification; verify non-reimbursable items.",
    )


# ---------------------------------------------------------------------------
# 2. Duplicate detection
# ---------------------------------------------------------------------------

def _parse_date(date_str: str):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(str(date_str), fmt)
        except ValueError:
            continue
    return None


def check_duplicate(row: pd.Series, df: pd.DataFrame) -> RuleResult:
    rule = "check_duplicate"
    row_id = row["expense_id"]
    others = df[df["expense_id"] != row_id]

    # Exact: same receipt_file
    exact_file = others[others["receipt_file"] == row["receipt_file"]]
    if len(exact_file):
        match_id = exact_file.iloc[0]["expense_id"]
        return RuleResult(
            status=AuditStatus.FLAGGED,
            severity=Severity.HIGH,
            confidence=1.0,
            rule_name=rule,
            reason_summary=f"exact duplicate receipt file (matches {match_id})",
            detailed_reason=(
                f"Exact duplicate: same receipt_file '{row['receipt_file']}' "
                f"used by expense {match_id}.\n"
                f"This expense: vendor={row['vendor']}, amount={row['amount']}, date={row['date']}\n"
                f"Matching row:  vendor={exact_file.iloc[0]['vendor']}, "
                f"amount={exact_file.iloc[0]['amount']}, date={exact_file.iloc[0]['date']}"
            ),
            suggested_action="Investigate potential duplicate submission.",
            duplicate_match_id=str(match_id),
        )

    # Exact: same vendor + amount + date
    exact_vad = others[
        (others["vendor"] == row["vendor"]) &
        (others["amount"] == row["amount"]) &
        (others["date"] == row["date"])
    ]
    if len(exact_vad):
        match_id = exact_vad.iloc[0]["expense_id"]
        return RuleResult(
            status=AuditStatus.FLAGGED,
            severity=Severity.HIGH,
            confidence=1.0,
            rule_name=rule,
            reason_summary=f"exact duplicate vendor+amount+date (matches {match_id})",
            detailed_reason=(
                f"Identical vendor, amount, and date as expense {match_id}.\n"
                f"Vendor: {row['vendor']}, Amount: {row['amount']}, Date: {row['date']}"
            ),
            suggested_action="Investigate potential duplicate submission.",
            duplicate_match_id=str(match_id),
        )

    # Fuzzy: same vendor + amount within 5% + date within 3 days
    row_date = _parse_date(row["date"])
    for _, other in others.iterrows():
        if other["vendor"] != row["vendor"]:
            continue
        try:
            amount_diff = abs(float(other["amount"]) - float(row["amount"])) / float(row["amount"])
        except (ZeroDivisionError, ValueError):
            continue
        if amount_diff > 0.05:
            continue
        other_date = _parse_date(other["date"])
        if row_date and other_date and abs((other_date - row_date).days) <= 3:
            match_id = other["expense_id"]
            fields_matched = []
            if other["vendor"] == row["vendor"]:
                fields_matched.append("vendor")
            if amount_diff == 0:
                fields_matched.append("amount")
            if other["date"] == row["date"]:
                fields_matched.append("date")
            conf = 0.6 + 0.1 * len(fields_matched)
            return RuleResult(
                status=AuditStatus.UNCERTAIN,
                severity=Severity.MEDIUM,
                confidence=round(conf, 2),
                rule_name=rule,
                reason_summary=f"fuzzy duplicate (matches {match_id}): same vendor, ~amount, ~date",
                detailed_reason=(
                    f"Possible duplicate of expense {match_id}.\n"
                    f"Same vendor: {row['vendor']}\n"
                    f"Amount difference: {round(amount_diff * 100, 1)}% (within 5%)\n"
                    f"Date difference: {abs((other_date - row_date).days)} day(s) (within 3)\n"
                    f"Matching fields: {', '.join(fields_matched)}"
                ),
                suggested_action="Review both entries for possible duplicate submission.",
                duplicate_match_id=str(match_id),
            )

    return _ok(rule)


# ---------------------------------------------------------------------------
# 3. Missing receipt
# ---------------------------------------------------------------------------

def check_missing_receipt(row: pd.Series, ocr) -> RuleResult:
    rule = "check_missing_receipt"
    if ocr is None:
        return RuleResult(
            status=AuditStatus.FLAGGED,
            severity=Severity.HIGH,
            confidence=1.0,
            rule_name=rule,
            reason_summary=f"receipt file not found: {row['receipt_file']}",
            detailed_reason=(
                f"Expected file: {row['receipt_file']}\n"
                f"Status: not found in uploaded folder"
            ),
            suggested_action="Request the original receipt from the employee.",
        )
    if ocr.confidence < 0.6:
        return RuleResult(
            status=AuditStatus.UNCERTAIN,
            severity=Severity.LOW,
            confidence=0.5,
            rule_name=rule,
            reason_summary="receipt found but OCR confidence is low",
            detailed_reason=(
                f"Receipt file: {row['receipt_file']}\n"
                f"OCR confidence: {round(ocr.confidence * 100, 1)}% (threshold: 60%)\n"
                f"Extracted data may be incomplete or inaccurate."
            ),
            suggested_action="Verify extracted amounts against the original receipt.",
        )
    return _ok(rule)


# ---------------------------------------------------------------------------
# 4. Category check
# ---------------------------------------------------------------------------

def check_category(row: pd.Series, ocr, ai_result) -> RuleResult:
    rule = "check_category"
    approved = _load_categories()
    category = row["category"]

    if category not in approved:
        return RuleResult(
            status=AuditStatus.FLAGGED,
            severity=Severity.MEDIUM,
            confidence=1.0,
            rule_name=rule,
            reason_summary=f"category '{category}' not in approved list",
            detailed_reason=(
                f"Declared category: {category}\n"
                f"Status: not in approved category list\n"
                f"Approved categories: {', '.join(approved)}"
            ),
            suggested_action="Reclassify expense using an approved category.",
        )

    # Category is approved — evaluate AI result
    if ai_result == "category_consistent":
        return _ok(rule)

    if ai_result == "category_mismatch":
        return RuleResult(
            status=AuditStatus.FLAGGED,
            severity=Severity.MEDIUM,
            confidence=0.85,
            rule_name=rule,
            reason_summary=f"AI: receipt content inconsistent with '{category}'",
            detailed_reason=(
                f"Declared category: {category}\n"
                f"AI classification: category_mismatch\n"
                f"Receipt content appears inconsistent with the declared category."
            ),
            suggested_action="Review receipt content against declared category.",
        )

    if ai_result == "category_unclear":
        return RuleResult(
            status=AuditStatus.UNCERTAIN,
            severity=Severity.LOW,
            confidence=0.5,
            rule_name=rule,
            reason_summary=f"AI: category unclear for '{category}'",
            detailed_reason=(
                f"Declared category: {category}\n"
                f"AI classification: category_unclear\n"
                f"Receipt content is ambiguous relative to the declared category."
            ),
            suggested_action="Manual review recommended.",
        )

    # ai_result is None — AI unavailable
    return RuleResult(
        status=AuditStatus.UNCERTAIN,
        severity=Severity.LOW,
        confidence=0.4,
        rule_name=rule,
        reason_summary=f"AI-assisted check unavailable — rule-only result",
        detailed_reason=(
            f"Declared category: {category}\n"
            f"Category is in the approved list.\n"
            f"AI-assisted check unavailable — rule-only result."
        ),
        suggested_action="Manual review recommended.",
    )


# ---------------------------------------------------------------------------
# 5. Suspicious pattern
# ---------------------------------------------------------------------------

def check_suspicious_pattern(row: pd.Series, df: pd.DataFrame, preliminary_results: list) -> RuleResult:
    rule = "check_suspicious_pattern"
    emp_id = row["employee_id"]

    # Map expense_id → preliminary AuditResult-like dict for same employee
    same_emp_ids = set(df[df["employee_id"] == emp_id]["expense_id"].tolist())
    same_emp_ids.discard(row["expense_id"])

    flagged_count = 0
    duplicate_count = 0
    missing_count = 0
    related_ids = []

    for pr in preliminary_results:
        if pr["expense_id"] in same_emp_ids:
            related_ids.append(pr["expense_id"])
            if pr["audit_status"] == AuditStatus.FLAGGED:
                flagged_count += 1
            if "check_duplicate" in pr["triggered_rules"]:
                duplicate_count += 1
            if "check_missing_receipt" in pr["triggered_rules"]:
                missing_count += 1

    issues = sum([
        duplicate_count >= 2,
        missing_count >= 2,
        flagged_count >= 3,
    ])

    if issues >= 2:
        return RuleResult(
            status=AuditStatus.FLAGGED,
            severity=Severity.MEDIUM,
            confidence=0.75,
            rule_name=rule,
            reason_summary=f"suspicious pattern: {flagged_count} flags from employee {emp_id}",
            detailed_reason=(
                f"Employee {emp_id} has multiple issues in this dataset:\n"
                f"  Flagged entries: {flagged_count}\n"
                f"  Duplicate submissions: {duplicate_count}\n"
                f"  Missing receipts: {missing_count}\n"
                f"Related entries: {', '.join(related_ids) or 'none'}"
            ),
            suggested_action="Escalate for manager review; consider full audit of this employee's expenses.",
        )

    if flagged_count >= 1 or duplicate_count >= 1 or missing_count >= 1:
        return RuleResult(
            status=AuditStatus.UNCERTAIN,
            severity=Severity.LOW,
            confidence=0.5,
            rule_name=rule,
            reason_summary=f"weak pattern signal for employee {emp_id}",
            detailed_reason=(
                f"Employee {emp_id} has minor issues in this dataset:\n"
                f"  Flagged entries: {flagged_count}\n"
                f"  Duplicate submissions: {duplicate_count}\n"
                f"  Missing receipts: {missing_count}\n"
                f"Related entries: {', '.join(related_ids) or 'none'}"
            ),
            suggested_action="Monitor for recurring patterns in future submissions.",
        )

    return _ok(rule)
