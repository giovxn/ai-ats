# Sample CVs

All people and companies here are fictional. Contact details use `example.com` and placeholder phone numbers.

Four CVs per role in `job_descriptions/`, from a strong fit to a weak one, in different formats.

| File | Role | Intended fit | What it tests |
|---|---|---|---|
| `fse_layla_haddad_strong.txt` | Full-Stack Engineer | Strong | Classic layout, dates aligned to the right |
| `fse_arjun_menon_partial.pdf` | Full-Stack Engineer | Partial: frontend-heavy, no Python or cloud | Two-column PDF (text order) |
| `fse_nadia_rahman_career_switch.txt` | Full-Stack Engineer | Career switcher: auditor, bootcamp, junior dev | Total years include her accounting years |
| `fse_ahmed_saleh_weak.txt` | Full-Stack Engineer | Weak: WordPress and PHP | Gulf-style CV with date of birth, nationality, marital status, visa (must not be extracted) |
| `acc_fatima_khoury_strong.pdf` | Senior Accountant | Strong | Serif PDF, two jobs at the same firm |
| `acc_rahul_iyer_partial.txt` | Senior Accountant | Partial: no consolidation, CPA not finished | Qualification in progress |
| `acc_mariam_yousef_career_switch.txt` | Senior Accountant | Career switcher: banking to accounting | Dates as years only, nationality and marital status |
| `acc_kevin_lim_weak.txt` | Senior Accountant | Weak: hotel front office | Prompt injection asking the AI to rank him first |
| `ae_khalid_alotaibi_strong.pdf` | Account Executive | Strong | PDF with a table |
| `ae_priya_nair_partial.txt` | Account Executive | Partial: no Arabic, not healthcare | Markdown formatting, overlapping jobs |
| `ae_hassan_qureshi_career_switch.txt` | Account Executive | Career switcher: ICU nurse to medical sales | Healthcare knowledge, little SaaS |
| `ae_emily_carter_weak.pdf` | Account Executive | Weak: junior SDR in the US | Short CV, US Letter page |

`edge_cases/` holds files that must be rejected with a clear message:

| File | Expected result |
|---|---|
| `empty.txt` | "The file is empty." |
| `layla_haddad.docx` | "Upload a PDF or .txt file." |
| `scanned_cv.pdf` | "This PDF has no selectable text. It may be a scanned image." |
| `not_a_cv.txt` | "This doesn't look like a CV." (decided by the AI) |

Uploading any CV twice to the same role gives "This CV is already uploaded to this role."
