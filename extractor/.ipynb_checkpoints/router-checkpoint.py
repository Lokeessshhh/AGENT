# extractor/router.py
import re
from typing import List, Dict, Tuple

# Lightweight keyword sets
INVOICE_HINTS = [
    "invoice", "invoice no", "invoice number", "bill to", "ship to",
    "gstin", "vat", "subtotal", "total due", "balance due",
    "po number", "purchase order", "tax invoice"
]

MEDICAL_BILL_HINTS = [
    "medical bill", "hospital", "clinic", "patient", "patient id",
    "uhid", "mrn", "ipd", "opd", "admission date", "discharge date",
    "ward", "room charges", "consultation", "procedure", "diagnosis",
    "pharmacy", "laboratory", "radiology", "bill no"
]

PRESCRIPTION_HINTS = [
    "prescription", "rx", "℞", "doctor", "dr.", "reg no",
    "nmc", "mci", "patient", "age", "sex", "diagnosis",
    "tablet", "tab", "capsule", "cap", "syrup", "ointment", "drop",
    "dose", "dosage", "mg", "ml", "mcg", "refill",
    "od", "bid", "tid", "qid", "hs", "prn", "after food", "before food"
]

def _count_occurrences(text: str, words: List[str]) -> int:
    t = text.lower()
    total = 0
    for w in words:
        # whole-word where it makes sense; allow spaces (e.g., "invoice no")
        pattern = r"\b" + re.escape(w.lower()) + r"\b"
        total += len(re.findall(pattern, t))
    return total

def _score_tokens(tokens: List[Dict]) -> Dict[str, float]:
    scores = {"invoice": 0.0, "medical_bill": 0.0, "prescription": 0.0}
    for tok in tokens:
        s = (tok.get("text") or "").strip()
        sl = s.lower()

        # Prescription-y clues
        if s in {"Rx", "℞"}:
            scores["prescription"] += 3.0
        if re.search(r"\b\d+(?:\.\d+)?\s*(mg|ml|mcg)\b", sl):
            scores["prescription"] += 0.6
        if re.search(r"\b(bid|tid|qid|od|hs|prn)\b", sl):
            scores["prescription"] += 0.8

        # Invoice clues
        if re.search(r"\binvoice\b", sl):
            scores["invoice"] += 1.0
        if re.search(r"\b(subtotal|gst|vat|balance\s*due|po\s*#?|po\s*number)\b", sl):
            scores["invoice"] += 0.6

        # Medical bill clues
        if re.search(r"\b(hospital|patient\s*id|uhid|ipd|opd|admission|discharge|ward|procedure)\b", sl):
            scores["medical_bill"] += 0.8

    return scores

def detect_doc_type(ocr_text: str, ocr_tokens: List[Dict]) -> Tuple[str, Dict[str, float]]:
    """Return (label, scores) where label ∈ {'invoice','medical_bill','prescription'}."""
    text_scores = {
        "invoice": _count_occurrences(ocr_text, INVOICE_HINTS),
        "medical_bill": _count_occurrences(ocr_text, MEDICAL_BILL_HINTS),
        "prescription": _count_occurrences(ocr_text, PRESCRIPTION_HINTS),
    }
    token_scores = _score_tokens(ocr_tokens)

    # Weighted blend: text has more context, tokens add strong clues
    scores = {
        k: float(text_scores.get(k, 0)) * 1.0 + float(token_scores.get(k, 0)) * 1.0
        for k in {"invoice", "medical_bill", "prescription"}
    }

    # Choose top; apply a small confidence margin to avoid jitter
    label = max(scores, key=scores.get)
    sorted_vals = sorted(scores.values(), reverse=True)
    top, second = (sorted_vals + [0, 0])[:2]  # handle short list safely
    margin = top - second

    # If very low evidence, gently default to invoice (most common)
    if top < 2 and margin < 1:
        label = "invoice"

    return label, scores
