"""Generate edge-case receipt images for case_2, case_3, case_4."""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os


def font(size=16):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def base_receipt(vendor, date, items, total, W=420, H=560):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    lg, md, sm = font(22), font(16), font(13)
    y = 20

    def line(text, f=None, center=False):
        nonlocal y
        f = f or md
        x = (W - d.textlength(text, font=f)) // 2 if center else 30
        d.text((x, y), text, fill="black", font=f)
        y += int(d.textbbox((0, 0), text, font=f)[3]) + 7

    line(vendor, f=lg, center=True)
    line("-" * 44, f=sm, center=True)
    line(f"Date: {date}", f=sm)
    line("-" * 44, f=sm, center=True)
    for item, price in items:
        line(f"{item:<30}${price:>7.2f}", f=sm)
    line("-" * 44, f=sm, center=True)
    sub = sum(p for _, p in items)
    line(f"{'Subtotal:':<30}${sub:>7.2f}", f=sm)
    line(f"{'Tax:':<30}${total - sub:>7.2f}", f=sm)
    line("=" * 44, f=sm, center=True)
    line(f"{'TOTAL:':<30}${total:>7.2f}", f=lg)
    line("=" * 44, f=sm, center=True)
    line("Thank you!", f=sm, center=True)
    return img


# ── Case 2: Blurred images ────────────────────────────────────────────────

OUT2 = "data/case_2/receipts"

img = base_receipt("STARBUCKS #4821", "04/15/2026",
                   [("Caffe Latte", 5.50), ("Blueberry Muffin", 3.75)], 10.80)
img.filter(ImageFilter.GaussianBlur(radius=3)).save(f"{OUT2}/blur_mild.jpg")
print("case_2: blur_mild.jpg  (radius=3, LLM should still read)")

img = base_receipt("DELTA AIRLINES", "04/17/2026",
                   [("Flight SEA-JFK", 312.00), ("Baggage Fee", 35.00)], 360.00)
img.filter(ImageFilter.GaussianBlur(radius=9)).save(f"{OUT2}/blur_heavy.jpg")
print("case_2: blur_heavy.jpg  (radius=9, very hard to read)")

img = base_receipt("OFFICE DEPOT", "04/19/2026",
                   [("Printer Paper", 42.00), ("Ink Cartridge", 38.00)], 89.99)
# Simulate motion blur via repeated horizontal box blurs
for _ in range(12):
    img = img.filter(ImageFilter.BoxBlur(radius=(6, 0)))
img.save(f"{OUT2}/blur_motion.jpg")
print("case_2: blur_motion.jpg  (horizontal motion blur)")

# ── Case 3: Wrong image type (not a receipt) ──────────────────────────────

OUT3 = "data/case_3/receipts"

# Business card
img = Image.new("RGB", (420, 260), "#f0f0f0")
d = ImageDraw.Draw(img)
d.rectangle([(15, 15), (405, 245)], outline="#333", width=2)
d.text((40, 50),  "JOHN SMITH",               fill="black", font=font(24))
d.text((40, 90),  "Senior Account Manager",   fill="#555",  font=font(14))
d.text((40, 130), "john.smith@acmecorp.com",  fill="black", font=font(13))
d.text((40, 155), "Tel: +1 (555) 847-2910",   fill="black", font=font(13))
d.text((40, 180), "ACME Corporation",         fill="black", font=font(14))
d.text((40, 205), "123 Business Ave, NY 10001", fill="#555", font=font(11))
img.save(f"{OUT3}/business_card.jpg")
print("case_3: business_card.jpg  (no prices, contact info only)")

# Meeting agenda
img = Image.new("RGB", (420, 560), "white")
d = ImageDraw.Draw(img)
d.text((30, 20), "MEETING AGENDA",                fill="black", font=font(20))
d.text((30, 60), "Project Sync - April 29, 2026", fill="#333",  font=font(14))
d.line([(30, 85), (390, 85)], fill="#999", width=1)
agenda = [
    "1. Review Q1 targets (15 min)",
    "2. Budget allocation update (20 min)",
    "3. Team OKRs for Q2 (25 min)",
    "4. Product roadmap alignment (20 min)",
    "5. AOB / Next steps (10 min)",
]
y = 105
for item in agenda:
    d.text((30, y), item, fill="black", font=font(13))
    y += 35
d.text((30, 320), "Attendees: Alice, Bob, Carol, Dave", fill="#555", font=font(12))
d.text((30, 345), "Room: Conference B, Floor 4",        fill="#555", font=font(12))
d.text((30, 370), "Duration: 90 minutes",               fill="#555", font=font(12))
img.save(f"{OUT3}/meeting_agenda.jpg")
print("case_3: meeting_agenda.jpg  (no prices, meeting notes)")

# Nutritional label — has numbers but none are prices
img = Image.new("RGB", (420, 560), "white")
d = ImageDraw.Draw(img)
d.rectangle([(20, 20), (400, 540)], outline="black", width=3)
d.text((30, 30), "Nutrition Facts",             fill="black", font=font(22))
d.text((30, 65), "Serving Size: 1 cup (240ml)", fill="black", font=font(12))
d.line([(20, 90), (400, 90)], fill="black", width=4)
rows = [
    ("Calories", "120"), ("Total Fat", "4.5g"), ("Sodium", "140mg"),
    ("Total Carbs", "18g"), ("Sugars", "12g"), ("Protein", "3g"),
    ("Vitamin D", "2mcg"), ("Calcium", "300mg"), ("Iron", "0mg"),
]
y = 100
for label, val in rows:
    d.text((30, y),  label, fill="black", font=font(13))
    d.text((340, y), val,   fill="black", font=font(13))
    y += 30
d.line([(20, 385), (400, 385)], fill="black", width=2)
d.text((30, 395), "Lot: 2026-04-29  Exp: 12/2027", fill="#555", font=font(11))
img.save(f"{OUT3}/nutrition_label.jpg")
print("case_3: nutrition_label.jpg  (numbers present, no prices)")

# ── Case 4: Ambiguous numbers (date/ref could be mistaken for cost) ────────

OUT4 = "data/case_4/receipts"

# Parking ticket — date 12/29/2026 dominates; "Amount Due: SEE INVOICE" = no price
img = Image.new("RGB", (420, 560), "white")
d = ImageDraw.Draw(img)
d.text((90, 25),  "PARK & RIDE SERVICES",      fill="black", font=font(20))
d.text((30, 65),  "Location: Terminal 2 Garage", fill="black", font=font(12))
d.text((30, 85),  "Entry: 12/29/2026  08:14 AM", fill="black", font=font(12))
d.text((30, 105), "Exit:  12/29/2026  11:47 AM", fill="black", font=font(12))
d.text((30, 125), "Duration: 3h 33m",            fill="black", font=font(12))
d.line([(30, 150), (390, 150)], fill="#aaa", width=1)
d.text((30, 160), "Parking Rate: FLAT",     fill="black", font=font(12))
d.text((30, 180), "Ref #: 2026-1229-0047",  fill="black", font=font(12))
d.text((30, 200), "Validated: YES",          fill="black", font=font(12))
d.line([(30, 225), (390, 225)], fill="black", width=2)
d.text((30, 240), "Amount Due: SEE INVOICE", fill="black", font=font(15))
d.text((30, 290), "Thank you for parking!",  fill="#555",  font=font(12))
img.save(f"{OUT4}/date_as_cost.jpg")
print("case_4: date_as_cost.jpg  (12/29/2026 dominates, no total)")

# Invoice where ref number INV-124.50 matches currency pattern, real cost is $85.00
img = Image.new("RGB", (420, 560), "white")
d = ImageDraw.Draw(img)
d.text((30, 25),  "NEXPRINT SOLUTIONS",          fill="black", font=font(20))
d.text((30, 60),  "Invoice #: INV-124.50",        fill="black", font=font(15))
d.text((30, 85),  "Date: 04/22/2026",             fill="black", font=font(13))
d.text((30, 105), "Due:  05/22/2026",             fill="black", font=font(13))
d.line([(30, 130), (390, 130)], fill="black", width=1)
d.text((30, 145), "Service: Business Card Print", fill="black", font=font(13))
d.text((30, 165), "Qty: 500 cards",               fill="black", font=font(13))
d.text((30, 185), "Unit: $0.17 each",             fill="black", font=font(13))
d.line([(30, 210), (390, 210)], fill="black", width=1)
d.text((30, 225), "Subtotal:  $85.00",  fill="black", font=font(14))
d.text((30, 250), "Tax (0%):  $0.00",   fill="black", font=font(14))
d.text((30, 280), "TOTAL:     $85.00",  fill="black", font=font(20))
img.save(f"{OUT4}/inv_ref_confusion.jpg")
print("case_4: inv_ref_confusion.jpg  (INV-124.50 ref vs $85.00 total)")

# Order slip — no TOTAL, order number and table number look like amounts
img = Image.new("RGB", (420, 560), "white")
d = ImageDraw.Draw(img)
d.text((140, 25), "ORDER SLIP",          fill="black", font=font(20))
d.text((30, 65),  "Order #: 04292026",   fill="black", font=font(13))
d.text((30, 85),  "Table:   29",         fill="black", font=font(13))
d.text((30, 105), "Server:  04",         fill="black", font=font(13))
d.text((30, 125), "Date: 04/29/2026",    fill="black", font=font(13))
d.line([(30, 150), (390, 150)], fill="black", width=1)
d.text((30, 165), "Burger Deluxe",       fill="black", font=font(13))
d.text((30, 185), "Fries (large)",       fill="black", font=font(13))
d.text((30, 205), "Soda x2",             fill="black", font=font(13))
d.line([(30, 230), (390, 230)], fill="black", width=1)
d.text((30, 245), "** PAY AT COUNTER **", fill="black", font=font(14))
d.text((30, 270), "Ref: 2026/04/29-T29",  fill="black", font=font(12))
img.save(f"{OUT4}/no_total_order_slip.jpg")
print("case_4: no_total_order_slip.jpg  (no TOTAL line, refs mimic amounts)")

print("\nAll edge-case images generated.")
