"""Block 4: the plain-code rules in evidence.py. No AI involved: quotes are written by hand."""

import pytest

import evidence
from evidence import CVText, _is_heading, find_sections, verify_quote
from schemas import EvidenceExtraction, EvidenceQuote, Job, Requirement, RequirementEvidence

CV = """\
Sam Example
Senior Engineer | Dubai | sam@example.com

SUMMARY
Engineer who has written Python and React for nine years.

EXPERIENCE
Senior Engineer, Alpha Co (Dubai)                  2023 – Present
- Built React and TypeScript screens for the billing app
- Wrote Python backend services with FastAPI

Engineer, Beta Ltd                                 2021 – 2023
- Built dashboards in React for the sales team

Developer, Gamma Labs                              2019 – 2021
- Maintained a jQuery site for a travel agency

Backend Developer, Delta Systems                   2016 – 2019
- Built Django REST APIs on PostgreSQL for three clients
- Wrote Python backend services with FastAPI
- Ran the Kubernetes cluster for the staging environment

SKILLS
Python, Django, PostgreSQL, React, Kubernetes, Docker
"""

JOBS = [
    Job(title="Senior Engineer", company="Alpha Co", start="2023", end=None, is_current=True,
        highlights=["Built React and TypeScript screens for the billing app"]),
    Job(title="Engineer", company="Beta Ltd", start="2021", end="2023", is_current=False, highlights=[]),
    Job(title="Developer", company="Gamma Labs", start="2019", end="2021", is_current=False, highlights=[]),
    Job(title="Backend Developer", company="Delta Systems", start="2016", end="2019", is_current=False,
        highlights=["Built Django REST APIs on PostgreSQL for three clients"]),
]

PYTHON = Requirement(text="Python backend experience", must_have=True)
K8S = Requirement(text="Kubernetes", must_have=False)


def quote(text, job_number, tags=("action",)):
    return EvidenceQuote(text=text, job_number=job_number, tags=list(tags))


def check(quotes, requirement=PYTHON, cv=CV, jobs=JOBS):
    """Store an AI answer for one requirement, then read it back the way the API does."""
    extraction = EvidenceExtraction(
        requirements=[RequirementEvidence(requirement_number=1, status="demonstrated", quotes=quotes)],
        recent_highlights=[],
    )
    stored = evidence.from_extraction(extraction, [requirement], jobs)
    return evidence.view(stored, cv, jobs).requirements[0]


# ---------- the buried rule (spec scenarios) ----------

def test_must_have_evidence_in_job_1_is_not_buried():
    result = check([quote("Wrote Python backend services with FastAPI", 1)])
    assert result.quotes[0].verified
    assert not result.buried


def test_must_have_evidence_only_in_job_4_is_buried():
    result = check([quote("Built Django REST APIs on PostgreSQL", 4)])
    assert result.quotes[0].verified
    assert result.buried


def test_nice_to_have_only_in_job_4_is_not_buried():
    result = check([quote("Ran the Kubernetes cluster for the staging environment", 4)], requirement=K8S)
    assert result.quotes[0].verified
    assert not result.buried


def test_evidence_in_jobs_1_and_4_is_not_buried():
    result = check([
        quote("Built React and TypeScript screens", 1),
        quote("Built Django REST APIs on PostgreSQL", 4),
    ])
    assert all(q.verified for q in result.quotes)
    assert not result.buried


def test_same_quote_in_jobs_1_and_4_is_not_buried():
    # The sentence is in both jobs; the AI only named job 4. Every occurrence is checked,
    # so the copy in job 1 (inside the review window) means nothing is buried.
    result = check([quote("Wrote Python backend services with FastAPI", 4)])
    assert result.quotes[0].verified
    assert not result.buried


def test_quote_not_in_the_cv_is_not_verified_and_not_buried():
    result = check([quote("Designed Flask microservices for a bank", 4)])
    assert not result.quotes[0].verified
    assert not result.buried


def test_quote_in_a_different_jobs_section_is_not_verified():
    # The sentence is real, but it's under job 4, not job 3.
    result = check([quote("Built Django REST APIs on PostgreSQL", 3)])
    assert not result.quotes[0].verified
    assert not result.buried


def test_one_unverified_quote_keeps_the_check_quiet():
    # The paraphrased quote might be the recent evidence; we can't tell, so no prompt.
    result = check([
        quote("Python services at Alpha", 1),  # not word for word
        quote("Built Django REST APIs on PostgreSQL", 4),
    ])
    assert not result.buried


def test_short_skill_quotes_dont_hide_buried_evidence():
    # The AI sometimes quotes a single skill; it can't be verified, but it isn't tied to a job either.
    sql = Requirement(text="SQL and relational databases", must_have=True)
    result = check([quote("PostgreSQL", None), quote("Built Django REST APIs on PostgreSQL", 4)], requirement=sql)
    assert not result.quotes[0].verified
    assert result.buried


def test_job_title_on_the_anchor_line_belongs_to_that_job():
    cv = CVText("EXPERIENCE\nBackend Engineer — Alpha Co, Dubai\n- Wrote Go services\nDeveloper — Beta Ltd\n- Built React screens\n")
    jobs = [
        Job(title="Backend Engineer", company="Alpha Co", start=None, end=None, is_current=True, highlights=[]),
        Job(title="Developer", company="Beta Ltd", start=None, end=None, is_current=False, highlights=[]),
    ]
    sections = find_sections(cv, jobs)
    assert verify_quote("Developer — Beta Ltd", 1, cv, sections)
    assert not verify_quote("Developer — Beta Ltd", 0, cv, sections)


def test_jobs_that_cant_be_located_give_no_prompt():
    jobs = [*JOBS[:3], JOBS[3].model_copy(update={"company": "Omega Corp", "title": "Architect"})]
    result = check([quote("Built Django REST APIs on PostgreSQL", 4)], jobs=jobs)
    assert not result.quotes[0].verified
    assert not result.buried


def test_dates_that_contradict_the_job_order_give_no_prompt():
    jobs = [JOBS[0].model_copy(update={"start": "2015"}), *JOBS[1:]]
    assert evidence.dates_contradict_order(jobs)
    result = check([quote("Built Django REST APIs on PostgreSQL", 4)], jobs=jobs)
    assert result.quotes[0].verified
    assert not result.buried


def test_two_jobs_or_fewer_never_have_buried_evidence():
    result = check([quote("Built dashboards in React for the sales team", 2)], jobs=JOBS[:2])
    assert not result.buried


# ---------- job sections ----------

SAME_COMPANY_CV = """\
EXPERIENCE
Senior Developer, Alpha Co          2022 – Present
- Moved billing to a Python event queue
Product Engineer, Beta Ltd          2020 – 2022
- Built onboarding screens in React
Engineer, Gamma Labs                2018 – 2020
- Wrote internal tooling in Go
Developer, Alpha Co                 2015 – 2018
- Maintained the Python reporting scripts
"""

SAME_COMPANY_JOBS = [
    Job(title="Senior Developer", company="Alpha Co", start="2022", end=None, is_current=True, highlights=[]),
    Job(title="Product Engineer", company="Beta Ltd", start="2020", end="2022", is_current=False, highlights=[]),
    Job(title="Engineer", company="Gamma Labs", start="2018", end="2020", is_current=False, highlights=[]),
    Job(title="Developer", company="Alpha Co", start="2015", end="2018", is_current=False, highlights=[]),
]


def test_same_company_in_two_jobs_keeps_their_sections_apart():
    # A quote from the recent Alpha Co job, wrongly attributed to the older Alpha Co job.
    result = check([quote("Moved billing to a Python event queue", 4)], cv=SAME_COMPANY_CV, jobs=SAME_COMPANY_JOBS)
    assert not result.quotes[0].verified
    assert not result.buried
    # And the older Alpha Co job's own quote is verified there.
    result = check([quote("Maintained the Python reporting scripts", 4)], cv=SAME_COMPANY_CV, jobs=SAME_COMPANY_JOBS)
    assert result.quotes[0].verified
    assert result.buried


def test_skills_list_after_the_last_job_is_not_part_of_it():
    cv = CVText(CV)
    sections = find_sections(cv, JOBS)
    assert not verify_quote("Python, Django, PostgreSQL, React", 3, cv, sections)
    assert verify_quote("Python, Django, PostgreSQL, React", None, cv, sections)  # real, but not a job's


MARKDOWN_CV = """\
## Experience

**Developer, Alpha Co**
* Shipped the invoicing API in Python
* Wrote tests for every endpoint

**Engineer, Beta Ltd**
* Built React dashboards

## Skills
* Python
"""


def test_markdown_star_bullets_stay_inside_their_job():
    jobs = [
        Job(title="Developer", company="Alpha Co", start=None, end=None, is_current=True, highlights=[]),
        Job(title="Engineer", company="Beta Ltd", start=None, end=None, is_current=False, highlights=[]),
    ]
    cv = CVText(MARKDOWN_CV)
    sections = find_sections(cv, jobs)
    assert verify_quote("Wrote tests for every endpoint", 0, cv, sections)
    assert verify_quote("Built React dashboards", 1, cv, sections)
    assert not verify_quote("Built React dashboards", 0, cv, sections)


@pytest.mark.parametrize("line", ["SKILLS", "## Skills", "**Skills**", "Skills:", "  Education and training ", "### LANGUAGES"])
def test_known_section_names_are_headings(line):
    assert _is_heading(line)


@pytest.mark.parametrize("line", ["* Skills", "- Python", "• Education", "Built my skills in Python", "Achievements", "**Alpha Co**"])
def test_bullets_and_other_lines_are_not_headings(line):
    assert not _is_heading(line)


def test_quotes_must_be_at_least_three_words():
    cv = CVText(CV)
    assert not verify_quote("Python", None, cv, find_sections(cv, JOBS))


def test_matching_ignores_case_spacing_and_dash_style():
    cv = CVText("EXPERIENCE\nDeveloper, Alpha Co\n- Cut   load time\n  from 3s—to 1s\n")
    jobs = [Job(title="Developer", company="Alpha Co", start=None, end=None, is_current=True, highlights=[])]
    assert verify_quote("cut load time from 3s-to 1s", 0, cv, find_sections(cv, jobs))


# ---------- storing the AI's answer ----------

def test_from_extraction_drops_what_points_nowhere():
    extraction = EvidenceExtraction(
        requirements=[
            RequirementEvidence(requirement_number=1, status="demonstrated", quotes=[
                quote("Built Django REST APIs on PostgreSQL", 9),  # no job 9
                quote("Built Django REST APIs on PostgreSQL", 4, tags=("action", "outcome", "action")),
            ]),
            RequirementEvidence(requirement_number=7, status="demonstrated", quotes=[]),  # no requirement 7
        ],
        recent_highlights=[
            {"job_number": 1, "highlight_number": 1, "tags": ["action"]},
            {"job_number": 1, "highlight_number": 5, "tags": ["outcome"]},  # no bullet 5
            {"job_number": 4, "highlight_number": 1, "tags": ["action"]},  # only jobs 1 and 2 are tagged
        ],
    )
    stored = evidence.from_extraction(extraction, [PYTHON, K8S], JOBS)
    assert stored["requirements"][0]["quotes"] == [
        {"text": "Built Django REST APIs on PostgreSQL", "job_index": 3, "tags": ["action", "outcome"]},
    ]
    assert stored["requirements"][1] == {"text": "Kubernetes", "must_have": False, "status": "not_found", "quotes": []}
    assert stored["highlight_tags"] == [[["action"]], []]


# ---------- what the app shows ----------

def test_found_needs_a_verified_quote():
    # The AI says "demonstrated", but its only quote is too short to check: shown as unverified.
    result = check([quote("English (fluent)", None)])
    assert result.status == "unverified"
    assert not result.buried


def test_found_with_a_verified_quote_stays_found():
    assert check([quote("Wrote Python backend services with FastAPI", 1)]).status == "demonstrated"


def test_a_claim_with_no_quotes_at_all_is_unverified():
    assert check([]).status == "unverified"


def test_not_found_stays_not_found():
    extraction = EvidenceExtraction(
        requirements=[RequirementEvidence(requirement_number=1, status="not_found", quotes=[])],
        recent_highlights=[],
    )
    stored = evidence.from_extraction(extraction, [PYTHON], JOBS)
    assert evidence.view(stored, CV, JOBS).requirements[0].status == "not_found"


def test_evidence_stored_with_the_old_tag_name_reads_as_duty():
    stored = {
        "requirements": [{"text": "Python", "must_have": True, "status": "demonstrated", "quotes": [
            {"text": "Wrote Python backend services with FastAPI", "job_index": 0, "tags": ["responsibility"]},
        ]}],
        "highlight_tags": [[["responsibility", "action"]], []],
    }
    result = evidence.view(stored, CV, JOBS)
    assert result.requirements[0].quotes[0].tags == ["duty"]
    assert result.highlight_tags == [[["duty", "action"]], []]
