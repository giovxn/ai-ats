# Before Block 3 — Checklist

Block 3 adds the pipeline: columns New, Shortlisted, Interview, Rejected; open a candidate; move them between stages.

## 1. Clean the data ✅

- [x] **Real CV removed.** The database was rebuilt from scratch, so the tester's own CV is gone. The old database is kept locally as `backend/ats.backup-before-block3.db` (ignored by Git; it still contains that CV, so delete it once it's no longer needed).
- [x] **Duplicate roles removed** (the old "Senior Accountant" ×2 and "Group Finance").
- [x] **Rebuilt with sample data only** (20 API calls):

| ID | Role | Candidates |
|---|---|---|
| 1 | Senior Accountant | Fatima, Rahul, Mariam, Kevin (4) |
| 2 | Full-Stack Software Engineer | Layla, Arjun, Nadia, Ahmed, Tomás, Omar (6) |
| 3 | Account Executive, Mid-Market | Khalid, Priya, Hassan, Emily (4) |
| 4 | Sales Executive (FMCG) | none: kept on purpose to demo the flagged criteria |

All 14 uploads returned 201; years of experience match the earlier manual checks.

## 2. New sample formats ✅

Checked against the real model. Each one is a format the earlier samples didn't cover.

| ID | File | Format | Result |
|---|---|---|---|
| F1 | `cvs/fse_tomas_ribeiro_europass.pdf` | EU Europass CV | **PASS.** `dd/mm/yyyy` dates read as day/month (2019-09, not 2019-01), including dates split over two lines; internship kept as a job; 7.8 years correct; date of birth and gender left out. *Observation:* CEFR levels were dropped ("English", not "English (C1)"). |
| F2 | `cvs/fse_omar_farouk_functional.txt` | Functional (skills-first) CV | **PASS with an observation.** Two undated jobs kept with no invented dates; the career break was **not** made a job. *Observation:* years show 4.0, which counts only the one dated job, and the UI doesn't say it's partial. |
| F3 | `job_descriptions/operations_manager_prose.txt` | All prose, no bullets | **PASS.** 5 must-haves and 3 nice-to-haves found inside sentences; salary, benefits and the equal-opportunity footer not extracted. The first run returned a junk excluded criterion (`"."`); fixed by a prompt rule and a code guard. |
| F4 | `job_descriptions/sales_executive_agency_post.txt` | Gulf agency post | **PASS.** "Male candidates only", "Age 25 – 35 years" and "Indian / Pakistani nationals preferred" flagged, not used as requirements. *Observation:* "Immediate joiners / visit visa holders can apply" became a must-have, although it's an invitation, not a requirement. |

## 3. Decision: discriminatory criteria in job ads ✅ (drop and flag)

**Implemented.** The role prompt now puts criteria about who someone is (gender, age, nationality, ethnicity, religion, marital status, pregnancy, appearance) in `excluded_criteria` instead of requirements. The role page shows them as "Not used for screening", as outlined chips with a one-line explanation.

- **Emiratisation is kept as a requirement:** "UAE Nationals only (Family Book required)" stays a must-have, because it's lawful. Checked with a test ad.
- **Known limitation:** "Female candidates are encouraged to apply" is still flagged, even though it's an encouragement, not a condition. That's harmless (flagged items are never used), so it was accepted rather than spending more prompt iterations.
- **Why not "flag and wait for a person to approve":** that needs an approval workflow (states, who approves, what happens meanwhile) for a rare case. Drop and flag already keeps a person informed, and the original ad is one click away.

## 4. Code and repo

- [x] Block 2 committed (in another session).
- [x] `cd backend && uv run pytest` passes (54 tests, including the flagged criteria and the upgrade of an older database).
- [x] `.env` not tracked: `git ls-files | grep -E '^\.env$'` prints nothing.
- [x] NOTES.md updated with the drop-and-flag decision.
- [x] `candidates.stage` already exists (default `new`, limited to the 4 stages), so Block 3 needs no change to the candidates table.
- [x] Commit this work (excluded criteria, new samples, checklist).

## 5. Block 3 decisions to make before coding

- **How to move a candidate.** Drag-and-drop alone fails keyboard and screen-reader users. Recommended: a stage menu or buttons on the card and in the profile; drag-and-drop optional on top.
- **API.** One `PATCH /api/candidates/{id}` with `{"stage": "..."}`. It must reject unknown stages (422) and unknown ids (404).
- **Small screens.** Four columns don't fit at 375 px. Decide between horizontal scroll per board, stacked columns, or a stage filter.
- **Cut on purpose** (already in NOTES.md): stage history, rejection reasons, emailing candidates.

## Sources (format research)

- CV layouts (chronological, functional, combination): [Coursera](https://www.coursera.org/articles/types-of-resumes), [Toptal](https://www.toptal.com/resume/career-center/chronological-vs-functional-vs-combination-resume), [Robert Half](https://www.roberthalf.com/us/en/insights/landing-job/which-resume-format-is-best-for-you)
- What breaks CV parsing (tables, columns, headers, images): [Jobscan](https://jobscan.co/blog/resume-tables-columns-ats/), [Workable](https://resources.workable.com/blog/how-ATS-reads-resumes/), [Enhancv](https://enhancv.com/blog/how-ats-parse-creative-resumes/)
- Gulf and UAE CVs (nationality, visa, photo, date of birth): [VisualCV: Gulf CV](https://visualcv.com/international/gulf-gcc-cv), [GulfTalent](https://www.gulftalent.com/resources/dubai-jobs-guide/building-your-profile)
- Job description structure: [Built In](https://builtin.com/job-descriptions/how-to-write-a-job-description), [Greenhouse template](https://www.greenhouse.com/uk/guidance/bookmark-this-template-for-job-descriptions), [SHRM](https://shrm.org/topics-tools/tools/how-to-guides/how-to-develop-job-description)
