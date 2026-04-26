import pandas as pd


def match_receipts(df: pd.DataFrame, uploaded_files: dict) -> tuple:
    matched = {}
    missing = []
    for filename in df["receipt_file"].unique():
        if filename in uploaded_files:
            matched[filename] = uploaded_files[filename]
        else:
            matched[filename] = None
            missing.append(filename)
    return matched, missing
