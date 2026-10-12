from pypdf import PdfReader
import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file."""
    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n\n".join(text_parts)

def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from a plain text file."""
    return file_bytes.decode("utf-8", errors="ignore")

def parse_document(filename: str, file_bytes: bytes) -> str:
    """
    Parse a document and extract its text content.
    Supports: .pdf, .txt, .md
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("txt", "md", "csv", "json"):
        return extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}. Supported: pdf, txt, md, csv, json")
