import io
import pandas as pd

REQUIRED_COLUMNS = ["expense_id", "employee_id", "vendor", "amount", "date", "category", "receipt_file"]


class ValidationError(Exception):
    pass


def parse_csv(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(file_bytes))
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValidationError(
            f"Missing columns: {missing}. Expected schema: "
            "expense_id, employee_id, vendor, amount, date, category, receipt_file"
        )
    return df


def generate_sample_csv() -> bytes:
    data = {
        "expense_id":   ["EXP001", "EXP002", "EXP003", "EXP004", "EXP005"],
        "employee_id":  ["EMP01",  "EMP02",  "EMP01",  "EMP03",  "EMP02"],
        "vendor":       ["Starbucks", "Delta Airlines", "Office Depot", "Marriott Hotel", "Starbucks"],
        "amount":       [24.50, 350.00, 89.99, 210.00, 24.50],
        "date":         ["2026-04-01", "2026-04-03", "2026-04-05", "2026-04-06", "2026-04-01"],
        "category":     ["Meals", "Travel", "Office Supplies", "Accommodation", "Meals"],
        "receipt_file": ["receipt_001.jpg", "receipt_002.jpg", "receipt_003.jpg", "receipt_004.jpg", "receipt_001.jpg"],
    }
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode("utf-8")
