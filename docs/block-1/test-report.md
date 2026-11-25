# Block 1 — Role Setup Testing

## Test Information

| Field | Details |
|---|---|
| Feature | Block 1: Role Setup |
| Date | 25 November 2026 |
| Environment | macOS, local development (Vite on `localhost:5173`, FastAPI on `localhost:8000`) |
| Browser | Brave (E1, E2); Safari attempted for E1 but abandoned (see notes) |
| Backend | FastAPI |
| Database | SQLite |
| AI model | `gpt-5.4-mini` (default `OPENAI_MODEL` in `.env.example`) |
| Tester | Giovanni |

## Test Results

**Status key:** PASS = expected behaviour observed · FAIL = unexpected behaviour or bug · BLOCKED = could not reliably complete the test · NOT RUN = not yet tested

### A. Extraction Quality

| ID | Test | Expected Result | Status | Evidence / Notes |
|---|---|---|---|---|
| A1 | Create a role using `senior_accountant.txt` | Correct title, location and requirement categories are extracted | PASS | `screenshots/A1-role-overview.png`. Senior Accountant, Abu Dhabi, UAE (on-site). 9 must-have, 4 nice-to-have. ERP experience classified as must-have, NetSuite as nice-to-have. |
| A2 | Expand original job description | Original text is preserved and extracted requirements match the source | PASS | `screenshots/A2-original-job-description.png`. No major invented or missing requirements. |
| A3 | Test a real job posting from another industry | AI extracts the correct title, location and relevant requirements | PASS | `screenshots/A3.png`. Real noon Technology Graduate Program JD. 8 must-haves including the UAE National (Family Book) requirement. Location "Not specified", none invented. |
| A4 | Submit the same JD twice | Results remain semantically consistent across runs | PASS | Same noon JD submitted twice. Identical title, location, all 8 must-haves, ordering and classification. |

### B. Input Validation and Errors

| ID | Test | Expected Result | Status | Evidence / Notes |
|---|---|---|---|---|
| B1 | Submit an empty job description | Validation message appears; no request or role is created | PASS | Inline error under the field: "Paste the full job description. It needs at least 50 characters." Submission prevented. |
| B2 | Submit non-job-description text | Clear rejection message; no role is created | PASS | Pasted a short follow-up email. Inline error under the field: "This doesn't look like a job description. Paste the full posting and try again." |
| B3 | Close and reopen the role dialog using Escape | Dialog closes and reopens in its initial empty state | PASS | Typed text, pressed Escape, reopened. Dialog empty, no role created. |
| B4 | POST a description padded with whitespace to reach 50 characters (API, `curl`) | 422; no AI call, no role created | PASS | `"Accountant"` + 60 spaces returned `422`. Before the fix it returned `201` (found by automated test). Also covered by `test_whitespace_padding_does_not_count_towards_min_length`. |

### C. Navigation and Persistence

| ID | Test | Expected Result | Status | Evidence / Notes |
|---|---|---|---|---|
| C1 | Switch between multiple roles | Correct role and URL query parameter update | PASS | URL updates to `?role=1`, `?role=2`, etc. |
| C2 | Reload the page | Previously selected role remains selected | PASS | Reloaded on `?role=1`; Senior Accountant stayed selected and URL kept `?role=1`. |
| C3 | Open an invalid role ID in the URL | App falls back gracefully without crashing | PASS | `/?role=9999` fell back to the newest role (Technology Graduate Program, ID 3). No crash. |

### D. Failure Handling

| ID | Test | Expected Result | Status | Evidence / Notes |
|---|---|---|---|---|
| D1 | Stop backend and attempt to create a role | User sees a clear server connection error | PASS | Message: "Unable to reach the server. Check that the backend is running." |
| D2 | Cancel while a role is being created | Cancellation behavior is handled clearly; no misleading success state | PASS (after fix) | Manually BLOCKED: the request finished too fast to click Cancel, even with 3G throttling (role saved as ID 4). Code review then confirmed a bug (see Issues). After the fix, verified in the browser with the create request held open: Cancel disabled, Escape (pressed twice) ignored, dialog stays open; once the request ends, Cancel and Escape close the dialog again. Manual retest (Brave, real request): pressed Enter then Escape repeatedly; dialog stayed open, then closed and selected the one new role. Escape on an idle dialog still closes it (B3 regression check). |

### E. Accessibility and Layout

| ID | Test | Expected Result | Status | Evidence / Notes |
|---|---|---|---|---|
| E1 | Complete role creation using keyboard only | Controls are accessible and focus is visible | PASS | Brave. Tab, Enter and Escape all worked; focus rings visible; created a role without a mouse. |
| E2 | Resize browser to a narrow viewport (375 × 812) | Content remains usable without clipping or unwanted horizontal scrolling | PASS | `screenshots/E2-mobile-375.png`. Brave device toolbar, 375 × 812. Header, titles and chips wrap without overlap or clipping; no horizontal scroll. New Role dialog fits the screen, text area usable, Cancel and Create fully visible. Long role names truncated inside the native role dropdown (acceptable). |

---

## Issues and Observations

### Issues Found
- **D2 — Cancel did not cancel (fixed).** Code review showed Cancel only hid the dialog. The request kept running, the backend still called OpenAI and saved the role, and the frontend then added and selected it. If the dialog was reopened meanwhile, the finished request closed it and discarded the new text. Fix: Cancel is disabled and Escape is ignored while the role is being created (`frontend/src/RoleSetup.tsx`). True cancellation was not implemented; reasoning in NOTES.md.

### AI Extraction Observations
- Must-have and nice-to-have requirements were correctly separated in the sample Senior Accountant JD.
- ERP experience was classified as required, while NetSuite was classified as preferred.
- A3: Correctly identified the UAE National requirement, degree, experience range and programming knowledge in the noon JD. Did not invent a location. Company introduction and culture statements were not extracted as requirements.
- Some extracted requirements are broad soft skills ("eagerness to learn") rather than measurable qualifications. This reflects the source JD, not an extraction error.
- A4: Extraction was fully repeatable for the same input in this test (2 runs).

### UI Observations
- The noon JD lost some line breaks when copied from the website (A3 shows "About usnoon is…"), so those parts display as one block. The "Original job description" view keeps line breaks, as A2 shows. This comes from the paste, not the display or the extraction.
- E2: Requirement chips that wrap onto several lines keep a fully rounded pill shape and look like blobs. Cosmetic; a smaller border radius would fix it.
- B1/B2 validation errors appear inline under the text field in red, and are linked to it for screen readers.
- E1: Safari was not usable for keyboard testing because macOS/Safari does not Tab to buttons and links by default ("Press Tab to highlight each item" setting). This is a browser setting, not an app bug.

### Limitations
- AI extraction may still vary between runs on other inputs; A4 only covered two runs of one JD.
- Manual tests were run with no CPU or network throttling unless stated.

## Summary

| Result | Count |
|---|---:|
| Passed | 15 |
| Failed | 0 |
| Blocked | 0 |
| Not run | 0 |
| **Total** | **15** |

**Overall result:** 15 of 15 passed. D2 passed after fixing a cancellation bug found by code review; B4 was added after automated tests found a whitespace validation bug.
