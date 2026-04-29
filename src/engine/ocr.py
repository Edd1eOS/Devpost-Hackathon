import base64
import json
import re
import time
from io import BytesIO

import streamlit as st
from groq import Groq
from PIL import Image

from models.schemas import OCRResult

CONFIDENCE_THRESHOLD = 0.6
_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
_MAX_RETRIES = 2
_RETRY_DELAY = 1.5  # seconds; doubles each retry

_SYSTEM_PROMPT = """You are a receipt data extractor.
Given a receipt image, extract exactly three fields and return valid JSON only — no explanation, no markdown.
Format: {"vendor": "...", "amount": 12.34, "date": "MM/DD/YYYY", "raw_text": "..."}
Rules:
- vendor: the business/store name (string)
- amount: the final total charged (number, no currency symbol)
- date: the transaction date in MM/DD/YYYY format
- raw_text: all visible text on the receipt concatenated as a single string
- Use null for any field you cannot find with confidence."""

_AMOUNT_RE = re.compile(r'\$?\d{1,6}[.,]\d{2}')
_DATE_RE   = re.compile(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}')


def _encode_image(image_bytes: bytes) -> tuple[str, str]:
    image = Image.open(BytesIO(image_bytes))
    fmt = image.format or "JPEG"
    mime = f"image/{fmt.lower()}"
    encoded = base64.standard_b64encode(image_bytes).decode("utf-8")
    return encoded, mime


def _groq_extract(image_bytes: bytes) -> OCRResult | None:
    encoded, mime = _encode_image(image_bytes)
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=_VISION_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
                        {"type": "text",      "text": "Extract the receipt fields as JSON."},
                    ]},
                ],
                max_tokens=256,
                temperature=0,
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
            data = json.loads(raw)

            amount = data.get("amount")
            if isinstance(amount, str):
                try:
                    amount = float(amount.replace(",", ".").lstrip("$"))
                except ValueError:
                    amount = None

            # Confidence scales with fields found; 0 fields = unreadable image
            fields_found = sum(1 for f in [data.get("vendor"), amount, data.get("date")] if f is not None)
            confidence = [0.1, 0.6, 0.8, 0.95][fields_found]

            return OCRResult(
                vendor=data.get("vendor") or None,
                amount=amount,
                date=data.get("date") or None,
                raw_text=data.get("raw_text") or "",
                confidence=confidence,
            )

        except (json.JSONDecodeError, KeyError):
            # Malformed response — don't retry, fall through to Tesseract
            return None
        except Exception:
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY * (2 ** attempt))
            else:
                return None

    return None


def _tesseract_extract(image_bytes: bytes) -> OCRResult:
    import pytesseract
    image = Image.open(BytesIO(image_bytes))
    config = "--psm 6"

    data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
    word_confs = [c for c in data["conf"] if c != -1]
    confidence = (sum(word_confs) / len(word_confs) / 100) if word_confs else 0.0

    raw_text = pytesseract.image_to_string(image, config=config)

    amount_match = _AMOUNT_RE.search(raw_text)
    amount = None
    if amount_match:
        try:
            amount = float(amount_match.group().lstrip("$").replace(",", "."))
        except ValueError:
            pass

    date_match = _DATE_RE.search(raw_text)
    date = date_match.group() if date_match else None

    vendor = None
    for line in raw_text.splitlines():
        line = line.strip()
        if line and not line[0].isdigit():
            vendor = line
            break

    return OCRResult(vendor=vendor, amount=amount, date=date, raw_text=raw_text, confidence=confidence)


def extract(image_bytes: bytes) -> OCRResult:
    result = _groq_extract(image_bytes)
    if result is not None:
        return result
    # Groq failed after retries — fall back to Tesseract
    return _tesseract_extract(image_bytes)
