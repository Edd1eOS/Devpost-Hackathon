from dataclasses import dataclass, field
from enum import Enum


class AuditStatus(Enum):
    OK = "OK"
    UNCERTAIN = "UNCERTAIN"
    FLAGGED = "FLAGGED"


class Severity(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


@dataclass
class OCRResult:
    vendor: str | None
    amount: float | None
    date: str | None
    raw_text: str
    confidence: float


@dataclass
class RuleResult:
    status: AuditStatus
    severity: Severity
    confidence: float
    rule_name: str
    reason_summary: str
    detailed_reason: str
    suggested_action: str
    duplicate_match_id: str | None = None


@dataclass
class AuditResult:
    expense_id: str
    employee_id: str
    vendor: str
    amount: float
    date: str
    category: str
    receipt_file: str
    audit_status: AuditStatus
    severity: Severity
    confidence: float
    triggered_rules: list
    reason_summary: str
    detailed_reason: str
    suggested_action: str
    matched_receipt_file: str
    ocr_result: OCRResult | None
    duplicate_match_id: str | None
    ai_assisted: bool
    ai_note: str | None
    generated_at: str
