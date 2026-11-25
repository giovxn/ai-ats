"""CV files: turn an uploaded PDF or .txt into plain text, and count years of experience.

No AI here. The text goes to the LLM in main.py, and the years are counted from the
job dates the LLM extracted, because code does arithmetic reliably and LLMs don't.
"""

import hashlib
import io
import re
from datetime import date
from pathlib import Path

from pypdf import PdfReader

from schemas import Job

MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB is far more than any text CV needs
MAX_TEXT_CHARS = 30_000           # about 10 pages; keeps OpenAI cost and time bounded
MIN_TEXT_CHARS = 100              # less than this can't be a CV


class CVFileError(Exception):
    """The file can't be used. `status` is the HTTP code, the message is shown to the user."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def read_text(filename: str, data: bytes) -> str:
    """Return the text of a PDF or .txt CV, or raise CVFileError with a plain message."""
    suffix = Path(filename).suffix.lower()
    if suffix not in (".pdf", ".txt"):
        raise CVFileError(415, "Upload a PDF or .txt file.")
    if not data:
        raise CVFileError(422, "The file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise CVFileError(413, "The file is over 5 MB.")

    text = _pdf_text(data) if suffix == ".pdf" else _txt_text(data)

    if len(text.strip()) < MIN_TEXT_CHARS:
        if suffix == ".pdf":
            raise CVFileError(422, "This PDF has no selectable text. It may be a scanned image.")
        raise CVFileError(422, "The file has too little text to be a CV.")
    if len(text) > MAX_TEXT_CHARS:
        raise CVFileError(422, "The CV is too long. Upload a file under 30,000 characters (about 10 pages).")
    return text.strip()


def _pdf_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            reader.decrypt("")  # many PDFs are "encrypted" with an empty password
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as error:
        # pypdf is reading an untrusted file and can fail in many ways (PdfReadError,
        # LimitReachedError, NotImplementedError and more, found by feeding it damaged
        # PDFs). Whatever the cause, the user's answer is the same: this file can't be read.
        raise CVFileError(422, "This PDF couldn't be read. It may be damaged or password-protected.") from error


def _txt_text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")  # utf-8-sig also drops a byte-order mark
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")  # older Windows exports


def fingerprint(text: str) -> str:
    """Same CV text gives the same hash, ignoring case and whitespace. Used to spot duplicates."""
    normalised = " ".join(text.lower().split())
    return hashlib.sha256(normalised.encode()).hexdigest()


# ---------- years of experience ----------

_DATE = re.compile(r"^(\d{4})(?:-(\d{1,2}))?$")


def _month_index(value: str | None, is_end: bool) -> int | None:
    """Turn "2019-03" into a month number. A year alone counts from January, or to December for an end date."""
    match = _DATE.match((value or "").strip())
    if not match:
        return None
    year, month = int(match[1]), match[2]
    month = int(month) if month else (12 if is_end else 1)
    if not 1 <= month <= 12:
        return None
    return year * 12 + month - 1


def total_years(jobs: list[Job], today: date | None = None) -> float | None:
    """Years of work covered by the jobs, counting overlapping jobs once. None when no job has usable dates."""
    today = today or date.today()
    now = today.year * 12 + today.month - 1

    spans = []
    for job in jobs:
        start = _month_index(job.start, is_end=False)
        end = now if job.is_current else _month_index(job.end, is_end=True)
        if start is None or end is None:
            continue  # a job without usable dates can't be counted
        end = min(end, now)  # an end date in the future counts up to today
        if start <= end:
            spans.append((start, end))
    if not spans:
        return None

    # Merge overlapping spans, then add up the months (both ends included).
    spans.sort()
    months, (current_start, current_end) = 0, spans[0]
    for start, end in spans[1:]:
        if start <= current_end + 1:
            current_end = max(current_end, end)
        else:
            months += current_end - current_start + 1
            current_start, current_end = start, end
    months += current_end - current_start + 1
    return round(months / 12, 1)
