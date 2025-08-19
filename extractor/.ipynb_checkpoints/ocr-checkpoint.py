# extractor/ocr.py
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
import io

def pdf_bytes_to_images(pdf_bytes, dpi=200):
    """Return list of PIL Images (one per page)."""
    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        return images
    except Exception as e:
        print(f"[OCR ERROR] Failed to convert PDF to images: {e}")
        return []

def image_to_ocr_data(pil_image):
    """Return words with bboxes and confidences using tesseract TSV output."""
    try:
        from pytesseract import Output
        data = pytesseract.image_to_data(pil_image, output_type=Output.DICT)
    except Exception as e:
        print(f"[OCR ERROR] pytesseract failed: {e}")
        return []

    results = []
    n = len(data['level'])
    for i in range(n):
        text = data['text'][i].strip()
        if text == "":
            continue
        try:
            conf = float(data['conf'][i])
        except Exception:
            conf = 0.0
        left, top, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        bbox = [left, top, left + w, top + h]
        results.append({
            "text": text,
            "conf": max(0.0, conf) / 100.0,
            "bbox": bbox
        })
    return results
