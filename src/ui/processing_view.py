import streamlit as st

from engine.matcher import match_receipts
from engine.orchestrator import run_audit
from models.schemas import OCRResult


def _step_icon(current_step: int, this_step: int) -> str:
    if this_step < current_step:
        return "✓"
    if this_step == current_step:
        return "⟳"
    return "·"


def render_processing():
    st.title("Processing Audit…")

    step_labels = [
        "Loading expense data",
        "Matching receipts",
        "Running validation rules",
        "AI-assisted checks",
    ]

    if "processing_step" not in st.session_state:
        st.session_state["processing_step"] = 0

    step_placeholder = st.empty()

    def render_steps(active: int):
        lines = []
        for i, label in enumerate(step_labels):
            icon = _step_icon(active, i)
            lines.append(f"**{icon}**  {label}")
        step_placeholder.markdown("\n\n".join(lines))

    render_steps(0)

    df = st.session_state.get("csv_df")
    uploaded = st.session_state.get("receipt_files", {})

    if df is None:
        st.error("No CSV data found. Please return to the upload screen.")
        if st.button("Back to Upload"):
            st.session_state["step"] = "upload"
            st.rerun()
        return

    # Step 1: CSV loaded
    render_steps(1)

    # Step 2: Match receipts
    matched, missing = match_receipts(df, uploaded)
    render_steps(2)

    if missing:
        st.warning("Missing receipt files (these rows will be flagged):")
        for fname in missing:
            st.caption(f"⚠ {fname} — not found in uploaded folder")

    # Handle OCR low-confidence recovery before running rules
    # Run a quick OCR pass to catch low-confidence cases upfront
    from engine import ocr as ocr_engine
    from engine.ocr import CONFIDENCE_THRESHOLD

    low_conf_overrides = {}  # filename → OCRResult or None

    ocr_cache = {}
    for fname, img_bytes in matched.items():
        if img_bytes is not None:
            try:
                ocr_cache[fname] = ocr_engine.extract(img_bytes)
            except Exception:
                ocr_cache[fname] = None

    low_conf_files = {
        fname: result
        for fname, result in ocr_cache.items()
        if result is not None and result.confidence < CONFIDENCE_THRESHOLD
    }

    if low_conf_files:
        st.info(f"{len(low_conf_files)} receipt(s) have low OCR confidence. Review or accept below:")
        for fname, ocr_result in low_conf_files.items():
            with st.expander(f"Low confidence: {fname} ({round(ocr_result.confidence * 100, 1)}%)"):
                st.text(f"Raw text preview:\n{ocr_result.raw_text[:300]}")
                choice = st.radio(
                    "Action",
                    ["Accept as UNCERTAIN and continue", "Edit extracted fields", "Replace receipt image"],
                    key=f"choice_{fname}",
                )
                if choice == "Edit extracted fields":
                    vendor = st.text_input("Vendor", value=ocr_result.vendor or "", key=f"vendor_{fname}")
                    amount_str = st.text_input("Amount", value=str(ocr_result.amount or ""), key=f"amount_{fname}")
                    date = st.text_input("Date", value=ocr_result.date or "", key=f"date_{fname}")
                    try:
                        amount = float(amount_str) if amount_str else None
                    except ValueError:
                        amount = None
                    low_conf_overrides[fname] = OCRResult(
                        vendor=vendor or None,
                        amount=amount,
                        date=date or None,
                        raw_text=ocr_result.raw_text,
                        confidence=ocr_result.confidence,
                    )
                elif choice == "Replace receipt image":
                    new_file = st.file_uploader(f"Replace {fname}", type=["jpg", "jpeg", "png"], key=f"replace_{fname}")
                    if new_file:
                        matched[fname] = new_file.getvalue()
                        st.success("Image replaced. Processing will use the new image.")
                # "Accept as UNCERTAIN" → no override; orchestrator handles via confidence threshold

    # Step 3 & 4: Run full pipeline
    render_steps(2)

    # Inject any manually edited OCR overrides into the receipt map signal via a patched extract
    if low_conf_overrides:
        import engine.ocr as _ocr_mod
        _original_extract = _ocr_mod.extract

        def _patched_extract(image_bytes):
            # Find which filename this corresponds to by matching bytes
            for fname, img in matched.items():
                if img == image_bytes and fname in low_conf_overrides:
                    return low_conf_overrides[fname]
            return _original_extract(image_bytes)

        _ocr_mod.extract = _patched_extract

    with st.spinner("Running audit pipeline…"):
        results = run_audit(df, matched)

    if low_conf_overrides:
        _ocr_mod.extract = _original_extract

    render_steps(4)

    st.session_state["results"] = results
    st.session_state["step"] = "results"
    st.rerun()
