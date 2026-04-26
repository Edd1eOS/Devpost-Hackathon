import re
from io import BytesIO

import pytesseract
from PIL import Image

from models.schemas import OCRResult

TESSERACT_CONFIG = "--psm 6"
CONFIDENCE_THRESHOLD = 0.6

_AMOUNT_RE = re.compile(r'\$?\d{1,6}[.,]\d{2}')
_DATE_RE   = re.compile(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}')


def extract(image_bytes: bytes) -> OCRResult:
    image = Image.open(BytesIO(image_bytes))

    data = pytesseract.image_to_data(image, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT)
    word_confs = [c for c in data["conf"] if c != -1]
    confidence = (sum(word_confs) / len(word_confs) / 100) if word_confs else 0.0

    raw_text = pytesseract.image_to_string(image, config=TESSERACT_CONFIG)

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
