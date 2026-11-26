"""Block 4, Beyond the Scan: checks the AI's evidence with plain code. No AI in this file.

The AI (prompts.EVIDENCE) says where each requirement shows up in a CV, with quotes. This file
decides what to trust and when to speak up:

1. A quote is verified only if it is in the CV text AND inside the section of the job it was
   attributed to. Job sections are found by locating each parsed job in the text.
2. A must-have is "buried" when its verified evidence sits only in jobs older than the 2 most
   recent ones: the 2 a recruiter reads, and the 2 on the scan card.

Everything fails closed: if anything can't be checked, the evidence isn't verified and the
"Before you reject" check never appears.
"""

import re

from cvs import _month_index
from schemas import EvidenceExtraction, EvidenceView, Job, QuoteView, Requirement, RequirementView

RECENT_JOBS = 2  # the review window: recruiters read the last 2 jobs (SME interview)
MIN_QUOTE_WORDS = 3  # a quote like "Python" proves nothing about where it came from

# Section headings that end a job's section, so a skills list or education entry after the last
# job is never counted as part of it. Only these names count: an unknown heading doesn't end a
# section (the job's section just runs on until the next known boundary).
HEADINGS = {
    "education", "education and training", "skills", "technical skills", "digital skills",
    "key skills", "core skills", "key skills and achievements", "certifications", "certification",
    "certificates", "licences and certifications", "languages", "language skills", "projects",
    "personal projects", "side projects", "open source", "interests", "hobbies", "references",
    "awards", "publications", "volunteering", "volunteer experience", "driving licence",
    "courses", "training", "talks", "talks and writing",
}

_BULLET = re.compile(r"^[-*•·▪◦‣]\s+")


# ---------- text ----------

def _normalise(text: str) -> str:
    """Lowercase, one kind of quote and dash, no bullet marker, single spaces."""
    text = text.lower()
    text = re.sub(r"[‘’´`]", "'", text)
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[‐‑‒–—―−]", "-", text)
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")  # PDF ligatures
    text = _BULLET.sub("", text.strip())
    return re.sub(r"\s+", " ", text).strip()


def _is_heading(raw_line: str) -> bool:
    """True for a line that is only a known section name: "SKILLS", "## Skills", "**Skills**", "Skills:".

    A bullet line ("* Skills", "- Python") is never a heading: in Markdown, "* " starts a bullet.
    """
    line = raw_line.strip()
    if _BULLET.match(line):
        return False
    line = line.lstrip("#").strip()
    if line.startswith("**") and line.rstrip(":").endswith("**"):
        line = line.strip(":").strip("*")
    return line.strip().rstrip(":").strip().lower() in HEADINGS


class CVText:
    """The CV text as one normalised string, plus where its known headings start."""

    def __init__(self, raw: str):
        parts, self.headings, self.line_starts, position = [], [], [], 0
        for raw_line in raw.splitlines():
            line = _normalise(raw_line)
            if not line:
                continue
            self.line_starts.append(position)
            if _is_heading(raw_line):
                self.headings.append(position)
            parts.append(line)
            position += len(line) + 1  # +1 for the joining space
        self.text = " ".join(parts)

    def line_start(self, position: int) -> int:
        return max(start for start in self.line_starts if start <= position)

    def find_all(self, phrase: str) -> list[int]:
        return [m.start() for m in re.finditer(re.escape(phrase), self.text)]


# ---------- job sections ----------

def _anchors_in_order(cv: CVText, jobs: list[Job]) -> list[int] | None:
    """Each job searched after the previous one (most recent first, as most CVs are written), by
    company first (rarely in a headline) and then title. This keeps two jobs at the same company apart."""
    anchors, position = [], 0
    for job in jobs:
        found = -1
        for key in (job.company, job.title):
            if key and _normalise(key):
                found = cv.text.find(_normalise(key), position)
                if found >= 0:
                    break
        if found < 0:
            return None
        anchors.append(cv.line_start(found))
        position = found + 1
    return anchors


def _anchors_unique(cv: CVText, jobs: list[Job]) -> list[int] | None:
    """For CVs not written most recent first (oldest first, or projects before jobs): each job is
    placed only where its company or title appears exactly once. Anything ambiguous fails closed."""
    anchors = []
    for job in jobs:
        found = None
        for key in (job.company, job.title):
            hits = cv.find_all(_normalise(key)) if key and _normalise(key) else []
            if len(hits) == 1:
                found = hits[0]
                break
        if found is None:
            return None
        anchors.append(cv.line_start(found))
    return anchors if len(set(anchors)) == len(anchors) else None


def find_sections(cv: CVText, jobs: list[Job]) -> list[tuple[int, int]] | None:
    """Each job's (start, end) in cv.text, or None if the jobs can't be placed with confidence.

    A section starts at the beginning of the line where its job is found ("Frontend Engineer, ShopSphere"),
    and ends at the next job (in text order) or the next known heading.
    """
    anchors = _anchors_in_order(cv, jobs) or _anchors_unique(cv, jobs)
    if anchors is None:
        return None
    boundaries = sorted(set(anchors + cv.headings + [len(cv.text)]))
    return [(start, min(b for b in boundaries if b > start)) for start in anchors]


def verify_quote(quote: str, job_index: int | None, cv: CVText, sections: list[tuple[int, int]] | None) -> bool:
    """In the CV text, and (for a job quote) inside that job's section. Any occurrence counts."""
    phrase = _normalise(quote)
    if len(phrase.split()) < MIN_QUOTE_WORDS:
        return False
    starts = cv.find_all(phrase)
    if not starts:
        return False
    if job_index is None:
        return True  # from the summary or skills list: real, but not tied to a job
    if sections is None or not 0 <= job_index < len(sections):
        return False
    start, end = sections[job_index]
    return any(start <= s and s + len(phrase) <= end for s in starts)


def dates_contradict_order(jobs: list[Job]) -> bool:
    """True if a job listed as more recent clearly started before the one listed after it."""
    for newer, older in zip(jobs, jobs[1:]):
        if not (newer.start and older.start):
            continue
        if len(newer.start) == 4 or len(older.start) == 4:  # a year alone: compare years only
            if int(newer.start[:4]) < int(older.start[:4]):
                return True
            continue
        a, b = _month_index(newer.start, False), _month_index(older.start, False)
        if a is not None and b is not None and a < b:
            return True
    return False


# ---------- storing and reading ----------

def from_extraction(extraction: EvidenceExtraction, requirements: list[Requirement], jobs: list[Job]) -> dict:
    """Turn the AI's answer into what's stored: requirement text and must-have copied in, 0-based job
    indexes, and anything pointing at a requirement, job or bullet that doesn't exist dropped."""
    by_number = {}
    for item in extraction.requirements:
        if 1 <= item.requirement_number <= len(requirements):
            by_number.setdefault(item.requirement_number, item)

    stored = []
    for number, requirement in enumerate(requirements, start=1):
        item = by_number.get(number)
        quotes = []
        for quote in (item.quotes if item else [])[:3]:
            job_index = quote.job_number - 1 if quote.job_number and 1 <= quote.job_number <= len(jobs) else None
            if quote.job_number is not None and job_index is None:
                continue  # a job that doesn't exist: can't be checked, so not kept
            quotes.append({"text": quote.text, "job_index": job_index, "tags": sorted(set(quote.tags))})
        stored.append({
            "text": requirement.text,
            "must_have": requirement.must_have,
            "status": item.status if item else "not_found",
            "quotes": quotes,
        })

    highlight_tags = [[[] for _ in job.highlights] for job in jobs[:RECENT_JOBS]]
    for item in extraction.recent_highlights:
        j, h = item.job_number - 1, item.highlight_number - 1
        if 0 <= j < len(highlight_tags) and 0 <= h < len(highlight_tags[j]):
            highlight_tags[j][h] = sorted(set(item.tags))
    return {"requirements": stored, "highlight_tags": highlight_tags}


def _is_buried(quotes: list[QuoteView], raw_quotes: list[dict], cv: CVText,
               sections: list[tuple[int, int]], jobs: list[Job]) -> bool:
    if len(jobs) <= RECENT_JOBS or not quotes or dates_contradict_order(jobs):
        return False
    if any(q.job_index is not None and not q.verified for q in quotes):
        return False  # a job quote we couldn't check might be the recent evidence: stay quiet
    # (An unverified quote with no job, like a one-word skill, says nothing about where evidence sits.)
    # Recent evidence anywhere wins, whichever job the AI named: if any quote also occurs inside the
    # last 2 jobs' text (e.g. the same sentence in jobs 1 and 4), the recruiter can see it.
    recent = sections[:RECENT_JOBS]
    for raw in raw_quotes:
        phrase = _normalise(raw["text"])
        if len(phrase.split()) < MIN_QUOTE_WORDS:
            continue  # a single word like "python" shows up everywhere and proves nothing
        if any(start <= s < end for s in cv.find_all(phrase) for start, end in recent):
            return False
    return any(q.job_index is not None and q.job_index >= RECENT_JOBS for q in quotes)


def _tags(tags: list[str]) -> list[str]:
    # Evidence stored before the tag was renamed says "responsibility"; it means "duty".
    return ["duty" if tag == "responsibility" else tag for tag in tags]


def shown_status(ai_status: str, quotes: list[QuoteView]) -> str:
    """"Found" and "Partly" need at least one verified quote. Without one, the AI's claim is shown as
    "unverified", never like real evidence."""
    if ai_status != "not_found" and not any(q.verified for q in quotes):
        return "unverified"
    return ai_status


def view(stored: dict, cv_text: str, jobs: list[Job]) -> EvidenceView:
    """Verify every quote and apply the buried rule. Runs on every read, so the rules can change
    without new AI calls."""
    cv = CVText(cv_text)
    sections = find_sections(cv, jobs)
    requirements = []
    for item in stored["requirements"]:
        quotes = [
            QuoteView(**{**quote, "tags": _tags(quote["tags"])},
                      verified=verify_quote(quote["text"], quote["job_index"], cv, sections))
            for quote in item["quotes"]
        ]
        buried = (
            item["must_have"]
            and sections is not None
            and _is_buried(quotes, item["quotes"], cv, sections, jobs)
        )
        requirements.append(RequirementView(
            **{**item, "quotes": quotes, "status": shown_status(item["status"], quotes)}, buried=buried,
        ))
    return EvidenceView(
        requirements=requirements,
        highlight_tags=[[_tags(tags) for tags in job] for job in stored["highlight_tags"]],
        sections_found=sections is not None,
    )


def ai_input(requirements: list[Requirement], jobs: list[Job], cv_text: str) -> str:
    """What the model reads: numbered requirements, numbered jobs with numbered bullets, the CV."""
    lines = ["REQUIREMENTS"]
    for number, requirement in enumerate(requirements, start=1):
        kind = "must-have" if requirement.must_have else "nice-to-have"
        lines.append(f"{number}. [{kind}] {requirement.text}")
    lines += ["", "JOBS (most recent first)"]
    for number, job in enumerate(jobs, start=1):
        dates = f"{job.start or '?'} to {'present' if job.is_current else job.end or '?'}"
        lines.append(f"{number}. {job.title}, {job.company or 'no company'}, {dates}")
        for h_number, highlight in enumerate(job.highlights, start=1):
            lines.append(f"   {number}.{h_number} {highlight}")
    lines += ["", "CV TEXT", cv_text]
    return "\n".join(lines)
