"""Small reusable validators for uploads and contact details."""
import os
import re

MAX_UPLOAD_MB = 10
ALLOWED = {
    'image': {'.jpg', '.jpeg', '.png', '.webp', '.gif'},
    'document': {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.jpg', '.jpeg', '.png'},
}


def validate_upload(f, kind='document'):
    """Return an error message string, or None if the file is acceptable."""
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in ALLOWED[kind]:
        return f"File type '{ext or 'unknown'}' is not allowed. Allowed: {', '.join(sorted(ALLOWED[kind]))}."
    if f.size > MAX_UPLOAD_MB * 1024 * 1024:
        return f"File is too large (max {MAX_UPLOAD_MB} MB)."
    return None


def valid_email(value):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value or ''))


def valid_phone(value):
    return bool(re.fullmatch(r"\+?\d{10,13}", (value or '').replace(' ', '')))
