"""
NexAudit test runner — runs the full audit pipeline against test_expenses.csv
and saves results to data/results/test_results_<timestamp>.csv

Usage (from repo root):
    python data/test_runner.py
"""

import os
import sys
import types
from datetime import datetime

# --- path setup ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
RESULTS_DIR = os.path.join(DATA_DIR, "results")
sys.path.insert(0, os.path.join(ROOT, "src"))

# --- mock streamlit so engine modules import cleanly outside Streamlit ---
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

CSV_PATH = os.path.join(DATA_DIR, "test_expenses.csv")

EXPECTED = {
    "EXP001": "FLAGGED",            # duplicate — shares receipt_001.jpg with EXP006
    "EXP002": "UNCERTAIN",          # suspicious pattern — EMP02 also owns flagged EXP005
    "EXP003": "FLAGGED",            # amount mismatch >10% ($89.99 reported vs $115.00 on receipt)
    "EXP004": ["OK", "UNCERTAIN"],  # LLM variance: consistent or unclear for Accommodation
    "EXP005": "FLAGGED",            # restricted item (wine) → category_mismatch
    "EXP006": "FLAGGED",            # duplicate — shares receipt_001.jpg with EXP001
    "EXP007": "FLAGGED",            # missing receipt + invalid category (Gambling)
}


def load_receipts() -> dict:
    receipts = {}
    for fname in os.listdir(DATA_DIR):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            with open(os.path.join(DATA_DIR, fname), "rb") as f:
                receipts[fname] = f.read()
    return receipts


def run():
    print("=" * 60)
    print("NexAudit Test Runner")
    print(f"CSV:     {CSV_PATH}")
    print(f"Results: {RESULTS_DIR}")
    print("=" * 60)

    with open(CSV_PATH, "rb") as f:
        df = parse_csv(f.read())
    print(f"\nLoaded {len(df)} expense rows")

    uploaded = load_receipts()
    print(f"Loaded {len(uploaded)} receipt image(s): {list(uploaded.keys())}")

    matched, missing = match_receipts(df, uploaded)
    if missing:
        print(f"Missing receipts (intentional): {missing}")

    print("\nRunning audit pipeline...\n")
    results = run_audit(df, matched)

    # --- print summary ---
    passed = 0
    failed = 0
    rows = []

    for r in results:
        expected = EXPECTED.get(r.expense_id, "?")
        actual = r.audit_status.value
        acceptable = expected if isinstance(expected, list) else [expected]
        match = "PASS" if actual in acceptable else "FAIL"
        if match == "PASS":
            passed += 1
        else:
            failed += 1

        print(
            f"[{match}] {r.expense_id:8} | expected={str(acceptable):16} got={actual:8} | "
            f"{r.severity.value:6} | {r.reason_summary[:55]}"
        )

        rows.append({
            "expense_id":       r.expense_id,
            "employee_id":      r.employee_id,
            "vendor":           r.vendor,
            "amount":           r.amount,
            "category":         r.category,
            "receipt_file":     r.receipt_file,
            "expected_status":  expected,
            "actual_status":    actual,
            "severity":         r.severity.value,
            "confidence":       round(r.confidence, 3),
            "triggered_rules":  ", ".join(r.triggered_rules),
            "reason_summary":   r.reason_summary,
            "ai_assisted":      r.ai_assisted,
            "pass_fail":        match,
            "generated_at":     r.generated_at,
        })

    print(f"\nResults: {passed} passed / {failed} failed / {len(results)} total")

    # --- save to results/ ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(RESULTS_DIR, f"test_results_{timestamp}.csv")
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Saved:   {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    run()
