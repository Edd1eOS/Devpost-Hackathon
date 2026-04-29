"""
NexAudit test runner

Usage (from repo root):
    python data/test_runner.py              # runs case_1 by default
    python data/test_runner.py case_1
    python data/test_runner.py case_2

Structure expected:
    data/<case>/
        test_expenses.csv
        receipts/           <- receipt images
        results/            <- output saved here
"""

import os
import sys
import types
from datetime import datetime

# --- path setup ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

# --- mock streamlit ---
st_mock = types.ModuleType("streamlit")
st_mock.session_state = {}
secrets_path = os.path.join(ROOT, ".streamlit", "secrets.toml")
_api_key = ""
if os.path.exists(secrets_path):
    with open(secrets_path) as f:
        for line in f:
            if "GROQ_API_KEY" in line:
                _api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
st_mock.secrets = {"GROQ_API_KEY": _api_key}
sys.modules["streamlit"] = st_mock

# --- imports ---
import pandas as pd
from engine.matcher import match_receipts
from engine.orchestrator import run_audit
from engine.parser import parse_csv

# ---------------------------------------------------------------------------
# Expected outcomes per case
# ---------------------------------------------------------------------------

EXPECTED = {
    "case_1": {
        "EXP001": ["OK"],                    # clean — all rules pass
        "EXP002": ["OK"],                    # clean — all rules pass
        "EXP003": ["UNCERTAIN"],             # amount mismatch 7% (tip/rounding range)
        "EXP004": ["FLAGGED"],               # amount mismatch 28% (>10% threshold)
        "EXP005": ["UNCERTAIN"],             # fuzzy duplicate of EXP006
        "EXP006": ["UNCERTAIN"],             # fuzzy duplicate of EXP005
        "EXP007": ["FLAGGED"],               # exact duplicate — same receipt file as EXP008
        "EXP008": ["FLAGGED"],               # exact duplicate — same receipt file as EXP007
        "EXP009": ["FLAGGED"],               # restricted item (wine) in receipt
        "EXP010": ["FLAGGED"],               # missing receipt + invalid category (Gambling)
        "EXP011": ["FLAGGED"],               # missing receipt + suspicious pattern (EMP05)
        "EXP012": ["FLAGGED"],               # missing receipt + suspicious pattern (EMP05)
        "EXP013": ["FLAGGED"],               # exact duplicate + suspicious pattern (EMP05)
        "EXP014": ["FLAGGED"],               # exact duplicate + suspicious pattern (EMP05)
    }
}

# ---------------------------------------------------------------------------

def load_receipts(receipts_dir: str) -> dict:
    receipts = {}
    if not os.path.isdir(receipts_dir):
        return receipts
    for fname in os.listdir(receipts_dir):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            with open(os.path.join(receipts_dir, fname), "rb") as f:
                receipts[fname] = f.read()
    return receipts


def run(case: str = "case_1"):
    case_dir     = os.path.join(ROOT, "data", case)
    csv_path     = os.path.join(case_dir, "test_expenses.csv")
    receipts_dir = os.path.join(case_dir, "receipts")
    results_dir  = os.path.join(case_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    expected_map = EXPECTED.get(case, {})

    print("=" * 65)
    print(f"NexAudit Test Runner — {case}")
    print(f"CSV:      {csv_path}")
    print(f"Receipts: {receipts_dir}")
    print(f"Results:  {results_dir}")
    print("=" * 65)

    with open(csv_path, "rb") as f:
        df = parse_csv(f.read())
    print(f"\nLoaded {len(df)} expense rows")

    uploaded = load_receipts(receipts_dir)
    print(f"Loaded {len(uploaded)} receipt image(s): {sorted(uploaded.keys())}")

    matched, missing = match_receipts(df, uploaded)
    if missing:
        print(f"Missing (intentional): {missing}")

    print("\nRunning audit pipeline...\n")
    results = run_audit(df, matched)

    passed = failed = 0
    rows = []

    for r in results:
        acceptable = expected_map.get(r.expense_id, [])
        actual     = r.audit_status.value
        match      = "PASS" if (not acceptable or actual in acceptable) else "FAIL"
        if match == "PASS":
            passed += 1
        else:
            failed += 1

        label = "/".join(acceptable) if acceptable else "?"
        print(
            f"[{match}] {r.expense_id:7} | expected={label:16} got={actual:8} "
            f"| {r.severity.value:6} | {r.reason_summary[:50]}"
        )

        rows.append({
            "expense_id":      r.expense_id,
            "employee_id":     r.employee_id,
            "vendor":          r.vendor,
            "amount":          r.amount,
            "category":        r.category,
            "receipt_file":    r.receipt_file,
            "expected_status": "/".join(acceptable),
            "actual_status":   actual,
            "severity":        r.severity.value,
            "confidence":      round(r.confidence, 3),
            "triggered_rules": ", ".join(r.triggered_rules),
            "reason_summary":  r.reason_summary,
            "ai_assisted":     r.ai_assisted,
            "pass_fail":       match,
            "generated_at":    r.generated_at,
        })

    print(f"\nResults: {passed} passed / {failed} failed / {len(results)} total")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path  = os.path.join(results_dir, f"test_results_{timestamp}.csv")
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Saved:   {out_path}")
    print("=" * 65)


if __name__ == "__main__":
    case_name = sys.argv[1] if len(sys.argv) > 1 else "case_1"
    run(case_name)
