import json
import os
import streamlit as st
from groq import Groq

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "restricted_items.json")

VALID_RESPONSES = {"category_consistent", "category_unclear", "category_mismatch"}

SYSTEM_PROMPT = """You are an expense audit assistant.
Given a declared expense category and the text extracted from a receipt,
determine whether the receipt content is consistent with the category.
Respond with exactly one word: category_consistent, category_unclear, or category_mismatch.
No explanation. No punctuation. One word only."""


def _load_restricted_items() -> list:
    with open(os.path.normpath(_CONFIG_PATH), "r") as f:
        return json.load(f)


def classify(category: str, ocr_raw_text: str) -> str | None:
    restricted = _load_restricted_items()
    text_lower = ocr_raw_text.lower()
    for item in restricted:
        if item in text_lower:
            return "category_mismatch"

    try:
        api_key = st.secrets["GROQ_API_KEY"]
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Category: {category}\nReceipt text: {ocr_raw_text}"},
            ],
            max_tokens=10,
            temperature=0,
        )
        result = response.choices[0].message.content.strip().lower()
        return result if result in VALID_RESPONSES else "category_unclear"
    except Exception:
        return None
