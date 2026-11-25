"""Unit tests for cvs.py: reading CV files and counting years of experience. No AI involved."""

from datetime import date
from pathlib import Path

import pytest

import cvs
from schemas import Job

SAMPLES = Path(__file__).parent.parent.parent / "sample_data" / "cvs"
CV_TEXT = "Jane Doe\nAccountant\n" + "Prepared month-end close and VAT returns for two entities. " * 3


# ---------- reading files ----------

def test_reads_a_text_file():
    assert cvs.read_text("cv.txt", CV_TEXT.encode()) == CV_TEXT.strip()


def test_reads_a_text_file_saved_in_an_old_windows_encoding():
    text = cvs.read_text("cv.TXT", ("José Núñez\n" + CV_TEXT).encode("cp1252"))
    assert text.startswith("José Núñez")


def test_reads_a_pdf():
    text = cvs.read_text("cv.pdf", (SAMPLES / "acc_fatima_khoury_strong.pdf").read_bytes())
    assert "FATIMA KHOURY" in text and "NetSuite" in text


def test_reads_a_two_column_pdf_in_a_sensible_order():
    text = cvs.read_text("cv.pdf", (SAMPLES / "fse_arjun_menon_partial.pdf").read_bytes())
    assert text.index("Frontend Engineer — ShopSphere") < text.index("Software Developer — Infolane")


@pytest.mark.parametrize(
    ("filename", "data", "status", "message"),
    [
        ("cv.docx", b"anything", 415, "Upload a PDF or .txt"),
        ("cv", b"anything", 415, "Upload a PDF or .txt"),
        ("cv.txt", b"", 422, "empty"),
        ("cv.txt", b"x" * (cvs.MAX_FILE_BYTES + 1), 413, "over 5 MB"),
        ("cv.txt", b"Jane Doe, accountant", 422, "too little text"),
        ("cv.txt", b"word " * 7_000, 422, "too long"),
        ("cv.pdf", b"%PDF-1.4 this is not really a pdf", 422, "couldn't be read"),
    ],
)
def test_rejects_unusable_files(filename, data, status, message):
    with pytest.raises(cvs.CVFileError, match=message) as raised:
        cvs.read_text(filename, data)
    assert raised.value.status == status


@pytest.mark.parametrize("error", [NotImplementedError("unsupported filter"), RecursionError(), MemoryError()])
def test_any_pdf_parser_failure_becomes_a_readable_error(monkeypatch, error):
    # Damaged PDFs made pypdf raise errors beyond PdfReadError; none may turn into a 500.
    def broken_reader(*args, **kwargs):
        raise error

    monkeypatch.setattr(cvs, "PdfReader", broken_reader)
    with pytest.raises(cvs.CVFileError, match="couldn't be read") as raised:
        cvs.read_text("cv.pdf", b"%PDF-1.4 anything")
    assert raised.value.status == 422


def test_scanned_pdf_has_no_text():
    with pytest.raises(cvs.CVFileError, match="no selectable text"):
        cvs.read_text("scan.pdf", (SAMPLES / "edge_cases" / "scanned_cv.pdf").read_bytes())


def test_fingerprint_ignores_case_and_whitespace():
    assert cvs.fingerprint("Jane  Doe\nAccountant") == cvs.fingerprint("jane doe accountant")
    assert cvs.fingerprint("Jane Doe") != cvs.fingerprint("John Doe")


# ---------- years of experience ----------

TODAY = date(2026, 11, 25)


def job(start, end=None, is_current=False):
    return Job(title="x", company=None, start=start, end=end, is_current=is_current, highlights=[])


def test_years_from_month_dates():
    # Mar 2019 to Feb 2021 inclusive = 24 months.
    assert cvs.total_years([job("2019-03", "2021-02")], TODAY) == 2.0


def test_current_job_counts_up_to_today():
    # Dec 2025 to Nov 2026 inclusive = 12 months.
    assert cvs.total_years([job("2025-12", is_current=True)], TODAY) == 1.0


def test_overlapping_jobs_are_counted_once():
    jobs = [job("2022-01", is_current=True), job("2023-01", "2023-12"), job("2020-01", "2021-12")]
    # 2020-01 to 2026-11 with no gap = 83 months.
    assert cvs.total_years(jobs, TODAY) == round(83 / 12, 1)


def test_gaps_between_jobs_are_not_counted():
    assert cvs.total_years([job("2018-01", "2018-12"), job("2020-01", "2020-12")], TODAY) == 2.0


def test_year_only_dates_count_whole_years():
    assert cvs.total_years([job("2018", "2023")], TODAY) == 6.0


def test_jobs_without_usable_dates_are_skipped():
    jobs = [job(None, "2020-01"), job("2019-03"), job("sometime", "2020"), job("2021-05", "2020-01")]
    assert cvs.total_years(jobs, TODAY) is None
    assert cvs.total_years([], TODAY) is None


def test_future_end_dates_stop_at_today():
    assert cvs.total_years([job("2026-01", "2027-12")], TODAY) == round(11 / 12, 1)


# ---------- links ----------

def test_finds_profile_links_and_full_urls():
    text = """Layla Haddad · layla@example.com · github.com/example-lh
    LinkedIn: https://www.linkedin.com/in/layla-h/ (updated). Portfolio: https://layla.dev.
    Skills: Node.js, Next.js, FastAPI"""
    assert cvs.find_links(text) == [
        "https://github.com/example-lh",
        "https://www.linkedin.com/in/layla-h/",
        "https://layla.dev",
    ]


def test_email_addresses_and_bare_domains_are_not_links():
    assert cvs.find_links("jane@github.com, jane@example.com, Node.js, example.com") == []


def test_links_are_unique_and_capped():
    text = " ".join(f"https://site{i}.dev" for i in range(8)) + " https://site0.dev"
    assert cvs.find_links(text) == [f"https://site{i}.dev" for i in range(5)]


# ---------- contact details ----------

def test_finds_the_email():
    assert cvs.find_email("Layla Haddad · layla.haddad@example.com · github.com/x") == "layla.haddad@example.com"
    assert cvs.find_email("Write to me at jo+jobs@mail.example.co.uk.") == "jo+jobs@mail.example.co.uk"
    assert cvs.find_email("No address here") is None


@pytest.mark.parametrize(
    ("text", "phone"),
    [
        ("Mobile: +971 55 000 0004", "+971 55 000 0004"),
        ("Phone:\n(+351) 900 000 001\nEDUCATION", "(+351) 900 000 001"),
        ("Call 050-123-4567 after 5pm", "050-123-4567"),
        ("Dubai | +971 50 000 0001 · github.com/x", "+971 50 000 0001"),
    ],
)
def test_finds_the_phone(text, phone):
    assert cvs.find_phone(text) == phone


def test_years_dates_and_numbers_are_not_phones():
    text = "2016 – 2018, 01/03/2022 – Current, AED 60M turnover, 1.2 million records, +40%, 0.5 FTE"
    assert cvs.find_phone(text) is None


def test_a_phone_never_runs_into_the_next_line():
    assert cvs.find_phone("+971 50 000 0001\n2019 – 2021") == "+971 50 000 0001"
