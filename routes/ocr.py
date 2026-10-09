"""
OCR Module (Module 5).

Extracts raw text from an uploaded document so that it can be stored against
the Document row. This is the hand-off point for the future NLP
cross-document-matching module (Phase 2): that module will consume
Document.extracted_text and look for consistency across a property's
documents.

- Image files (png/jpg/jpeg) are read with Pillow and passed to pytesseract.
- PDF files have their embedded text extracted with PyPDF2. If a PDF is a
  pure scanned image with no embedded text layer, PyPDF2 will return an
  empty string; adding page-rasterization + OCR for scanned PDFs is a
  natural Phase-2 enhancement and is called out in the README.
"""
import os

from flask import current_app


def extract_text_from_file(filepath):
    """
    Returns (status, text) where status is one of Document.OCR_STATUS_CHOICES.
    Never raises -- OCR failures are reported as a 'Failed' status so the
    upload flow itself never breaks because of an OCR problem.
    """
    ext = filepath.rsplit(".", 1)[-1].lower()

    try:
        if ext in {"png", "jpg", "jpeg"}:
            return _extract_from_image(filepath)
        if ext == "pdf":
            return _extract_from_pdf(filepath)
        return "Failed", ""
    except Exception as exc:  # noqa: BLE001 - we want any OCR failure captured, not crashed on
        current_app.logger.warning("OCR failed for %s: %s", filepath, exc)
        return "Failed", ""


def _extract_from_image(filepath):
    import pytesseract
    from PIL import Image

    tesseract_cmd = current_app.config.get("TESSERACT_CMD")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    with Image.open(filepath) as img:
        text = pytesseract.image_to_string(img)

    text = text.strip()
    return ("Completed", text) if text else ("Completed", "")


def _extract_from_pdf(filepath):
    from PyPDF2 import PdfReader

    reader = PdfReader(filepath)
    pages_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages_text).strip()
    return "Completed", text
