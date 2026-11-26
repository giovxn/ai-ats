# Presentation script: Beyond the Scan

20 minutes + 10 minutes Q&A, in the brief's order: live demo (8), how it works (5), why it works this way (5), next 2 weeks (2). Deck: `beyond-the-scan.pptx` (timings are also in its speaker notes). Demo files: `sample_data/demo/`.

## Before you start (10 minutes before)

1. `.env` has a working OpenAI key. Do one test request beforehand.
2. Start empty, so you can create the role live:
   ```bash
   cd backend && mv ats.db ats.before-demo.db
   uv run uvicorn main:app --reload
   ```
   In a second terminal: `cd frontend && npm run dev`, then open http://localhost:5173.
3. Open Finder at `sample_data/demo/cvs` and `job_description.txt` in a text editor, side by side with the browser.
4. Browser zoom 125% so the room can read it. Close other tabs and notifications (Do Not Disturb).
5. **Fallback** if the AI or Wi-Fi fails: `cd backend && uv run python reset_demo.py`, then reload. The same role and 9 CVs appear instantly.

| Time | Slide | Part |
|---|---|---|
| 0:00 | 1 Title | Live demo (8 min) |
| 0:20 | 2 What I built | |
| 0:50 | 3 Discovery | |
| 1:40 | 4 The quote | |
| 2:10 | 5 Live demo, in the app | |
| 7:00 | 6 Beyond the Scan in 3 steps | |
| 7:30 | 7 When the check appears | |
| 8:00 | 8 Architecture | How it works (5 min) |
| 9:45 | 9 AI extracts, code decides | |
| 11:15 | 10 Data model and prompts | |
| 13:00 | 11 What I cut | Why it works this way (5 min) |
| 14:45 | 12 Where it can be wrong | |
| 16:30 | 13 What it solves | |
| 18:00 | 14 Next 2 weeks | Next 2 weeks (2 min) |
| 19:30 | 15 Close | |

## Talk track

**1. Title (0:00).** "Hi, I'm Gio. I built a one-page, AI-native ATS: role setup, CV parsing and a pipeline, plus one twist I call Beyond the Scan. I'll show it working, then how it's built, why it's built this way, and what I'd do next."

**2. What I built (0:20).** "Blocks 1 to 3 are the brief's must-haves and all work end to end. Block 4 is the twist. Behind it: 119 automated tests with OpenAI mocked, so they're free and fast, plus 18 manual tests on the twist. The demo uses one job ad and nine fictional CVs."

**3. Discovery (0:50).** "Before picking the twist, I ran a 15-minute role-play with Tim and Chris as a Head of Talent and a CHRO hiring an AI engineering intern. A thousand applications in two days. They read about a hundred. And on long CVs, 15 to 20 seconds each, reading only the last two jobs. This was a role-play, so I treat it as a hypothesis to test, not as proof."

**4. The quote (1:40).** Read the quote, pause. "That's the shortcut the whole feature is built around. OVI's Milo already reads and scores every CV, so 'read the other 900' isn't my twist. What's left, even after AI has read everything, is human attention: the person still reads two jobs, and what's further down gets missed at the moment they reject."

**5. Live demo (2:10 to 7:00).** Switch to the browser.

1. **Create the role (about 45 s).** New role, paste `job_description.txt`, create. While it reads (about 8 s): "The AI pulls out the title, location and requirements, split into must-haves and nice-to-haves." Point at **Not used for screening: Preferred age 25 to 35**: "Gulf job ads often include age, gender or nationality. The app keeps it visible but never screens on it."
2. **Upload CVs (about 1 min 15 s).** Upload CVs, select all 9 PDFs, drop. While it runs (about 35 s): "Each CV gets two AI calls: one turns it into a profile, one finds where each requirement shows up, with an exact quote. Duplicates are caught before any AI call. Years of experience are counted in code from the job dates, not by the AI." When they land: "Nine real PDFs, including a two-column layout and a two-page CV."
3. **Profile and pipeline (about 45 s).** Open **Layla**: "Timeline of her jobs, contact details found by code, the original CV one click away." Move her to **Shortlisted** with the stage buttons. Close. On the board, move **Sara** to Interview with the card's menu (or drag): "Menu, buttons or drag: one code path."
4. **Scan mode (about 2 min).** Open Scan mode. "This is how recruiters already screen: one candidate at a time, the last two jobs on the card. It goes through New, oldest upload first. No scores, no ranking."
   * Reach **James** (Skip as needed) and Reject: "Clearly the wrong field. It goes straight through. It doesn't nag."
   * Reach **Priya**. "Page one of her CV says frontend manager. Most people reject here, because the role needs Python backend." Point at the amber note: "Two must-haves only show up in job four of five." Click **Reject**.
   * The check appears: "Before you reject, it shows the exact quote from job four: Python, Django, PostgreSQL. It doesn't question why I'm rejecting: presentation or seniority are fair reasons. It just shows what isn't on the card."
   * **Look again**: "Nothing moves. It opens the evidence: requirements down the side, her jobs across, and the dots outside the shaded two jobs are what a 20-second scan never reaches." Then move her to **Interview**.
   * Optional if time: reject **Daniel**: "No Python anywhere, so there's nothing to show, and it doesn't interrupt."

**6. In 3 steps (7:00).** "So: the AI reads the whole CV and finds quotes per requirement. Scan mode shows the two jobs people actually read. And only before a reject does it surface what's outside them. The recruiter always decides."

**7. When the check appears (7:30).** "It only appears when all four are true: a must-have, nothing in the last two jobs, evidence in an older job, and the quote verified in that job's text. It never blocks, scores, or moves anyone. Every decision is logged, and Undo adds a row rather than erasing one."

**8. Architecture (8:00).** "React on one page, FastAPI, SQLite. The AI sits behind one function, `llm.extract`: a prompt, the text, and a schema OpenAI must answer in. Three calls: role extraction, CV parsing, evidence. About two calls per CV, well under a cent."

**9. AI extracts, code decides (9:45).** "LLMs are bad at arithmetic and can invent text, so anything that has to be exact is code: years, duplicates, contact details, and above all whether a quote is real. Code checks every quote word for word, inside that job's section of the CV. It fails closed: anything it can't verify never interrupts the recruiter, and shows as Unverified rather than found."

**10. Data model and prompts (11:15).** "Three tables: roles, candidates and an append-only decisions log. Each prompt has rules that came from testing: discriminatory criteria are set aside, instructions inside a CV are ignored (I tested a CV telling AI tools to rank him first), and the evidence prompt must quote the CV's own words and never judge years."

**11. What I cut (13:00).** "No score or ranking: that's Milo. No learning from swipes: it would learn bias, like Amazon's 2018 hiring model, and hiring AI is high-risk under the EU AI Act. No 'years of Python': three years at a job isn't three years of a skill. And the check runs in Scan mode only for now; the board's reject is next."

**12. Where it can be wrong (14:45).** "The AI can link weak evidence to a requirement, older skills may not be current, and CVs inflate. I mitigate with exact quotes, dates and 'as claimed in the CV' labels. How I'd know it works: evidence accuracy, how often recruiters choose Look again, and the scan-gap rate on real CVs. My demo CVs were written to trigger it, so they prove the mechanism, not the value."

**13. What it solves (16:30).** "Long CVs read only at the top: solved. Good people lost at reject: caught before it happens. 'Did they contribute value?': partly, with outcome labels. The 900 unread CVs: not this feature, that's Milo. Excel and scattered channels: next steps."

**14. Next 2 weeks (18:00).** "Week 1: validate on real, consented CVs, and measure the scan gap and whether recruiters find the check useful. If they don't, nothing else here matters. Week 2: use Milo's per-requirement output as the evidence instead of a second engine, add the check to the board, and measure false alarms. After that: one inbox for every channel, no LinkedIn auto-rejects, and a morning briefing."

**15. Close (19:30).** "You don't have to read the whole CV. We just make sure you don't reject someone without seeing what's in it. Thank you, happy to take questions."

## Likely questions

* **"Isn't this our 'rejection reason honesty check' idea?"** "It's adjacent. That one judges whether a typed reason is honest. Mine needs no reason and doesn't judge: it shows information the recruiter didn't see, based on a habit you described."
* **"Doesn't Milo already do this?"** "Milo reads and scores every CV. This is about the moment a human decides, relative to what they actually read. In production I'd feed it Milo's per-requirement output instead of my own AI call."
* **"What if the AI quotes the wrong thing?"** "Every quote is checked word for word inside the job it's attributed to. If it can't be verified, it never triggers the check."
* **"Won't recruiters find it annoying?"** "It only fires for must-haves with evidence outside the last two jobs: 2 of 9 in the demo. That's exactly what week 1 measures, through the Look again rate."
* **"How often does this happen in real CVs?"** "I don't know yet, and I say so: the scan-gap rate is the first thing I'd measure."
* **"Why not rank candidates?"** "Ranking is Milo's job, and ranking from past decisions learns bias."

## The 3 to 5 minute recording

The brief asks for the repo and a running demo or a 3 to 5 minute screen recording, sent at least 24 hours before the talk.

1. Record with macOS: press Cmd+Shift+5, choose "Record Selected Portion" around the browser, set Options to your microphone, record. Or use Loom.
2. Use a clean start (empty database, as above) at 125% zoom.
3. Script, about 4 minutes:
   * 0:00 One sentence: "This is a one-page AI-native ATS with a twist called Beyond the Scan."
   * 0:15 Create the role from the job ad; point out "Not used for screening".
   * 0:45 Upload the 9 CVs (cut or speed up the wait in editing, and say so on screen).
   * 1:30 Open Layla's profile; move her to Shortlisted; move Sara on the board.
   * 2:10 Scan mode: reject James (no check), then Priya: the check, Look again, the evidence map, move her to Interview.
   * 3:40 One sentence on why: "Recruiters read the last two jobs; this makes sure what's further down is seen before a reject."
4. Upload as an unlisted YouTube video, a Google Drive link (anyone with the link can view) or Loom. Check the link in a private window.

## Email to send (at least 24 hours before)

To: tim@ovi-me.com, chris@ovi-me.com

> Subject: OVI case study: AI-native ATS (Gio)
>
> Hi Tim and Chris,
>
> Here's my case study ahead of the presentation:
>
> * Repo: https://github.com/giovxn/ai-ats (README covers setup, architecture and the prompts)
> * Demo recording (4 min): [link]
>
> The twist is Beyond the Scan, based on our interview: recruiters read the last two jobs of a long CV, so before a reject it surfaces must-have evidence that sits further down, with the exact quote. The demo runs without an API key via `reset_demo.py`.
>
> Looking forward to walking you through it.
>
> Best,
> Gio
