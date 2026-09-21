"""
Resume text extraction — pypdf for PDF, python-docx for DOCX. Both are free,
local libraries; no external parsing service involved (sections 7 and 42).
"""
from docx import Document
from pypdf import PdfReader


def extract_text(file_path: str, file_type: str) -> str:
    if file_type == "pdf":
        return _extract_pdf(file_path)
    if file_type == "docx":
        return _extract_docx(file_path)
    raise ValueError(f"Unsupported resume file type: {file_type}")


def _extract_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _extract_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs).strip()