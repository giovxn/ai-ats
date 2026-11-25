# Draft: swipe review mode

Status: idea only, not built. Not an AI feature, so it's separate from Block 4.

## The idea
A focused way to clear the New column: one candidate at a time, full screen, and one gesture per decision.

| Gesture | Keyboard | Button | Result |
|---|---|---|---|
| Swipe right | → | Shortlist | Shortlisted |
| Swipe up | ↑ | Interview | Interview |
| Swipe left | ← | Reject | Rejected |
| Swipe down | ↓ or Space | Skip | Stays in New, goes to the end of the queue |

- **The card shows evidence, not a person:** name, current title, years, the summary, top skills and the current job's highlights. No photo, no personal details: the same rule as the profile.
- **Undo** for 5 seconds after every decision ("Kevin Lim rejected. Undo"), and every decision can be changed later on the board.
- **Progress:** "7 of 23 reviewed", and an end screen that summarises the session.
- **Buttons are always on screen.** Swipes and arrow keys are shortcuts; nobody needs a gesture to use it (WCAG 2.5.7).

## How it would fit the code
- No backend change: every decision is the existing `PATCH /api/candidates/{id}`.
- One new component (`ReviewMode.tsx`, a full-screen `<dialog>`) opened from a "Review new" button on the board, using the same `moveCandidate()` as the board.
- Touch: pointer events with a distance or speed threshold, following the card under the finger and settling with a spring; reduced motion swaps the throw animation for a fade.

## Risks to design around
- **Speed invites snap judgements.** A gesture makes rejecting feel trivial, and fast decisions lean harder on bias. Mitigations: show work evidence first; make Reject the one decision that needs the profile opened at least once; show the undo every time.
- **"Tinder for candidates" is a bad look** in front of candidates and regulators. Call it "Review mode".
- **Rejected candidates aren't told anything.** That's still true on the board; it matters more when rejecting is this fast.

## How we'd know it works
- Time to clear the New column, compared with the board.
- Undo rate and how often a rejected candidate is moved back later (too high means decisions are too hasty).
- Whether shortlists from review mode turn into interviews as often as shortlists from the board.
