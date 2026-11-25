# Notes

A running log of decisions, cuts, AI risks and ideas, updated after each block.

## Decisions and why

**Stack**
- **FastAPI + stdlib `sqlite3`, no ORM.** Five small backend files I can explain line by line. An ORM would hide the SQL for no gain at this size.
- **Lists stored as JSON text** (requirements now, skills later). One table per concept; we never query inside these lists, so they don't need their own tables.
- **One LLM entry point (`llm.extract`).** Every AI call takes a prompt, the input text and a Pydantic schema, and returns a validated object or raises `LLMError`. New AI features plug in here without touching the rest.
- **OpenAI structured output (`responses.parse` with a Pydantic `text_format`).** The model is forced to answer in our JSON schema, and Pydantic validates it again on the way in. No regex parsing of free text.
- **Model is set in `.env` (`OPENAI_MODEL`, default `gpt-5.4-mini`).** Extraction is simple, so a small, cheap, fast model is enough. You can swap it without code changes.
- **Vite proxies `/api` to the backend.** No CORS setup, and the frontend calls `/api/...` the same way it would in production.

**Data model**
- **Candidate and application merged.** Greenhouse, Lever and Ashby all keep the *person* separate from their *application to a job*, and the stage lives on the application. Here a CV is always uploaded to one role, so one `candidates` row holds both. Splitting them is the first change if a person can apply to several roles.
- **Requirements carry a `must_have` flag.** This matches how OVI's own JD parsing splits requirements, and how recruiters actually screen.
- **The original JD is stored with the role.** It lets a recruiter check what the LLM extracted against the source.

**Role setup (Block 1)**
- **Non-JD text is rejected.** The prompt returns an empty title when the text isn't a job description, and the API answers 422 with a plain message instead of saving a junk role.
- **Input length is bounded (50 to 20,000 characters)** to stop empty submissions and very large pastes (cost, latency).
- **The selected role is kept in the URL (`?role=3`)** so a reload during a demo keeps your place.

**UI**
- **Styling follows OVI, kept quiet.** Warm off-white neutrals, a system serif only for display headings, the black halftone logo as the one signature element, and black primary buttons. No web fonts to load.
- **Native `<dialog>` for "New role".** You get focus trapping, Escape to close and a backdrop for free, with no modal library.
- **Clicking the backdrop doesn't close the dialog**, because a text selection dragged out of the textarea would close it and lose the pasted JD.
- **Accessibility.** Colour contrast is measured, not guessed (secondary text ≥ 4.75:1, input borders 3.6:1). The field is labelled, errors are linked with `aria-describedby` and focus moves to them, motion only runs when `prefers-reduced-motion` allows it, and the layout reflows at 320px.

## What we cut (and why)

- **Editing extracted requirements before saving.** OVI lets recruiters edit and reweight them. Useful, but it's outside the three blocks.
- **Auth, multiple users, teams.** It's a single-user local demo.
- **Dark mode.** One theme keeps the CSS short. The tokens are named by role, so adding a dark theme only means overriding the values.
- **Deleting and archiving roles.** Not needed to run a hiring process end to end.
- **Stage history and audit log.** Real ATSs keep the full history of stage moves. We store only the current stage.

## Where the AI can be wrong

**Role extraction**
- **Must-have versus nice-to-have is a judgement.** Postings are often vague ("ideally", "you'll have"). The prompt defaults unclear items to must-have, which can make a role look stricter than intended.
- **Requirements can be merged, split or reworded.** "ACCA, CPA or CA" might come back as one item or three. The original JD is kept so a person can check.
- **Location can be ambiguous** when a posting names several offices, or a remote role with a "preferred" city. The model returns null when no location is stated, and the UI shows "Location not specified".
- **Possible bias in the requirements themselves.** If a JD asks for something like "native Arabic speaker" or a degree that isn't really needed, the model faithfully extracts it. It doesn't question the JD.
- **Prompt injection.** A pasted JD could contain instructions aimed at the model. The impact is low here (the worst case is a wrong title or requirements on a role you can see and check). It would matter more once AI output drives decisions.

## Ideas for improvements

- **Let recruiters edit, reorder and reweight requirements** after extraction (as OVI's Sora does).
- **Show which sentence of the JD each requirement came from**, so checks are quick.
- **Keep a small evaluation set** of JDs with expected extractions, and run it whenever the prompt or model changes.
