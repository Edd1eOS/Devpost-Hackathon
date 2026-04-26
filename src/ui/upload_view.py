import streamlit as st

from engine.parser import ValidationError, generate_sample_csv, parse_csv


def render_upload():
    st.title("AI Audit Assistant")
    st.caption("Upload your expense CSV and receipt images to begin the audit.")

    st.download_button(
        "Download sample CSV template",
        data=generate_sample_csv(),
        file_name="sample_expenses.csv",
        mime="text/csv",
    )

    st.divider()

    csv_file = st.file_uploader("Upload expense CSV", type=["csv"])
    receipt_files = st.file_uploader(
        "Upload receipt images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    csv_valid = False
    csv_df = None

    if csv_file is not None:
        try:
            csv_df = parse_csv(csv_file.getvalue())
            csv_valid = True
            st.success(f"CSV validated: {len(csv_df)} expense rows found.")
        except ValidationError as e:
            st.error(str(e))

    receipts_uploaded = len(receipt_files) > 0

    if st.button("Run Audit", disabled=not (csv_valid and receipts_uploaded)):
        st.session_state["csv_df"] = csv_df
        st.session_state["receipt_files"] = {f.name: f.getvalue() for f in receipt_files}
        st.session_state["step"] = "processing"
        st.rerun()
