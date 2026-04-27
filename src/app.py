import streamlit as st
from ui.upload_view import render_upload
from ui.processing_view import render_processing
from ui.results_view import render_results

st.set_page_config(page_title="NexAudit", layout="wide")

if "step" not in st.session_state:
    st.session_state["step"] = "upload"

step = st.session_state["step"]
if step == "upload":
    render_upload()
elif step == "processing":
    render_processing()
elif step == "results":
    render_results()
