# Demo set: 1 job ad, 9 CVs

Everything here is fictional (people, companies, contact details). The CVs are real PDFs with selectable text, in common modern layouts: reverse-chronological, Profile / Experience / Education / Skills, mostly single-column, one two-column sidebar design and one long senior CV.

* `job_description.txt`: paste this into **New role**. It includes one line on purpose, "Preferred age 25 to 35", which the app moves to **Not used for screening**.
* `cvs/`: select all 9 PDFs and drop them into **Upload CVs** in one go (about 35 seconds, 3 at a time).
* `source/build_cvs.py`: regenerates the PDFs (needs Google Chrome).

The same role and CVs, already processed, are in `backend/demo.db`: `cd backend && uv run python reset_demo.py` loads them with no AI calls. Use it as the fallback if the AI or Wi-Fi fails during a live demo.

## What each CV shows

Checked with the real AI on 26 Nov 2026: only Priya and Rafael trigger "Before you reject".

| # | Candidate | Why they're in the set | In Scan mode |
|---|---|---|---|
| 01 | **Layla Mansour**, Senior Full-Stack Engineer | Strong fit, every must-have in her last 2 jobs | Shortlist. No check needed |
| 02 | **James Whitfield**, Digital Marketing Executive | Wrong field, one web course | Reject goes straight through: it doesn't nag |
| 03 | **Priya Raman**, Engineering Manager (2-page CV) | Page 1 says "frontend manager". Her Python (Django) backend and PostgreSQL work is job 4 of 5, on page 2 | **Check appears**: "2 must-haves only show up in job 4 of 5" |
| 04 | **Daniel Okoro**, Frontend Engineer | No Python anywhere in his CV | Reject goes straight through: there's nothing older to show |
| 05 | **Sara Al Hashimi**, Full-Stack Developer | Two-column sidebar layout, a solid fit | Parsed cleanly; Interview |
| 06 | **Marco Bellini**, Full-Stack Developer | Right stack, written as "Responsible for…" | Bullets labelled **Duty**, no Outcome |
| 07 | **Aisha Karimi**, Software Engineer (ex-auditor) | Career switcher; Python in her current job | No check. Her years include accounting (a known limitation) |
| 08 | **Kenji Watanabe**, Software Engineer | Kubernetes and payments only in older jobs, but those are nice-to-haves | Reject goes straight through: nice-to-haves never trigger it |
| 09 | **Rafael Costa**, Senior Mobile Engineer | Python (Flask) and PostgreSQL only in job 3 of 3 | **Check appears** (backup if Priya's doesn't) |

Scan mode goes through New in upload order. Uploads run 3 at a time, so the order can shift slightly from the file numbers: use **Skip for now** to reach the candidate you want.
