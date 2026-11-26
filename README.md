# OVI ATS

A one-page, AI-native applicant tracking system. Its twist, **Beyond the Scan**, makes sure a recruiter never rejects someone without seeing relevant experience outside the part of the CV they actually read.

<!-- Screenshot 1: Scan mode on Priya Raman, with the amber "Beyond the last 2 jobs" note -->

## What it does

* Paste a job ad: the AI pulls out the title, location and must-have / nice-to-have requirements, and sets aside discriminatory criteria (gender, age, nationality)
* Upload CVs (PDF or text): each becomes a profile with a job timeline
* Move candidates through New, Shortlisted, Interview and Rejected
* **Scan mode:** review new candidates one at a time, showing the last 2 jobs, like a recruiter's quick scan
* **Before you reject:** if a must-have only appears in an older job, see the exact quote first, then Look again or Reject anyway

<!-- Screenshot 2: "Before you reject" on Priya Raman -->

## Why

In the SME interview (OVI's Tim and Chris role-playing a talent team), one role got about 1,000 applications in 2 days. On long CVs: *"I look at the last 2 positions and I scan it for like 15 to 20 seconds and then I reject or go to the next."*

The AI can read the whole CV, but the person still reads the last 2 jobs. Relevant experience in job 4 gets missed at the moment of rejection, and *"it's like lost already."*

Beyond the Scan finds where each requirement shows up, with an exact quote, and only speaks up when a must-have sits outside those 2 jobs. The recruiter always decides.

* **Not a ranking.** Scoring every CV is what OVI's Milo does. In production, Milo's per-requirement output could feed this instead of its own AI call (that integration doesn't exist today).
* **Close to the brief's "rejection reason honesty check"**, but it needs no typed reason, and it shows missing information instead of judging a reason.
* **Never learns from decisions or moves anyone by itself.** A model trained on rejections learns the team's bias.

## Tech stack

* React, Vite, TypeScript
* FastAPI (Python)
* SQLite
* OpenAI API (`gpt-5.4-mini`, structured outputs)
* pypdf

## Architecture

<!-- Screenshot 3: "Where the evidence is" map on Priya Raman (amber dots in the Older columns) -->

```
React (frontend/src)  ──/api──▶  FastAPI (backend/main.py)  ──▶  SQLite
                                         │
                                         ▼
                             llm.extract()  ──▶  OpenAI
```

**The AI extracts, plain code decides.** Every AI call goes through one function, `llm.extract(prompt, text, schema)`, and OpenAI must answer in that schema. All prompts are in `backend/prompts.py`:

| Prompt | Turns | Into |
|---|---|---|
| `ROLE_EXTRACTION` | a job ad | title, location, requirements, excluded criteria |
| `CV_PARSING` | a CV | name, skills, jobs, education, a neutral summary (no rating) |
| `EVIDENCE` | requirements + CV | for each requirement: a status and exact quotes, each with its job and Outcome / Action / Duty tags |

Everything after that is code: years of experience, duplicate CVs, contact details, and in `backend/evidence.py`, checking every quote and deciding when to speak up.

**Data:** 3 SQLite tables. `roles`, `candidates` (one CV on one role, with its profile and evidence) and `decisions` (every Scan mode decision; rows are only added, so Undo is a new row).

## What failed first

* **Evidence pinned to the wrong job.** A skills-list line looked like part of the last job. Now each job's section of the CV is found in the text, sections end at headings like "Skills", and a quote counts only inside its own job.
* **False prompts.** With one quote per requirement, the AI could quote job 4 while job 1 had it too. Now it gives one quote per job, and every place a quote appears is checked.
* **"Found" without evidence.** The AI said English was shown, but its only quote was "English (fluent)", too short to check. Anything without a matching quote now shows as **Unverified**, never as found.
* **Real CVs aren't always newest first.** A CV listing the oldest job first broke matching. Now jobs are placed out of order only where their company or title appears exactly once.
* **Confident but wrong parsing.** "ACCA, 9 of 13 exams" came back as "ACCA". The prompt now requires "in progress".

All of it fails closed: if something can't be checked, the prompt doesn't appear. The risky part (matching quotes to jobs) was tested on every stored CV before any UI was built. 119 automated tests run with OpenAI mocked, so they're free.

## How we'd know it works

* **Evidence accuracy:** do the quotes support the requirement, in the right job?
* **Useful-prompt rate:** how often Look again is chosen (from the decision log)
* **Scan-gap rate:** how often must-have evidence sits outside the last 2 jobs in real CVs. Unknown: the demo CVs were written to have it

## Run locally

Needs Python 3.11+ with [uv](https://docs.astral.sh/uv/), and Node 20+. **The demo needs no API key**: the demo role and its 9 fictional CVs, with evidence already checked, ship in `backend/demo.db`. The same job ad and CVs, as PDFs, are in [sample_data/demo](sample_data/demo) for a live run.

```bash
cp .env.example .env              # add an OpenAI key, only needed for new roles and CVs
cd backend
uv run python reset_demo.py       # load the demo (no AI calls)
uv run uvicorn main:app --reload
```

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

**Demo:** pick **Full-Stack Software Engineer** and open **Scan mode**. Shortlist Layla (strong, recent evidence), reject James (no prompt), then try to reject Priya: her Python and SQL work sits in job 4 of 5. Run `reset_demo.py` again to start over.

<!-- Screenshot 4: the pipeline board for the Full-Stack role -->

## Current limitations

* Single user, local only
* PDF and .txt only; no OCR for scanned PDFs
* The check runs in Scan mode only; rejecting from the board doesn't show it yet
* Some CVs can't be matched to their jobs (functional CVs, out-of-order CVs with a repeated company, words split across PDF lines), so they get no prompt
* Older experience may not be current: the dates are shown and the recruiter judges

## Next

1. **Validate** on real, consented CVs: measure the scan gap and whether recruiters find the prompt useful
2. **Use Milo's evidence** instead of a separate AI call, and measure false prompts
3. **One pipeline for every channel** (careers page, a jobs@ email agent, LinkedIn import) and a morning briefing

More detail: [NOTES.md](NOTES.md) (decisions, cuts, where the AI can be wrong) and [the SME interview](docs/research/sme-interview.md).
