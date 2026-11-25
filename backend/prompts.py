"""Every LLM prompt in the app lives in this file.

Each prompt is paired with an output schema in schemas.py. OpenAI is forced to
answer in that JSON shape (structured output), so the prompts only describe
*what* to extract, not the JSON format.
"""

# Block 1, role setup: turns a pasted job description into title, location and
# requirements. Requirements are split into must-have and nice-to-have, the way
# recruiters screen.
ROLE_EXTRACTION = """\
You help a recruiting team set up a new role from a job description they pasted.

Extract:
- title: the job title as the posting states it, including seniority (for example "Senior Accountant").
- location: where the job is based, plus the work model if stated, for example "Dubai, UAE (hybrid)" or "Remote (EU time zones)". Use null if the posting does not say.
- requirements: every distinct skill, experience level, qualification, certification or language the posting asks for.
  - Write each one as a short phrase (under 12 words) in the posting's own terms that makes sense on its own, for example "5+ years in audit or accounting", not "5+ years".
  - Keep examples and alternatives with their requirement, for example "Python backend (FastAPI, Django or Flask)", not two separate items.
  - Options joined by "or" are one requirement, because the candidate needs only one of them: "CIPD Level 5 or SHRM-CP", not two items.
  - must_have is true when the posting presents it as required, and false when it is a plus ("nice to have", "bonus", "preferred", "a plus"). If the posting doesn't make it clear, use true.
  - If one sentence mixes a requirement and a preference (for example "SQL databases, PostgreSQL preferred"), split it: the general skill as must-have, the preference as nice-to-have.
  - If the posting names a tool only as context (for example "you know your way around a CRM; we use HubSpot"), the requirement is the general skill ("CRM experience"), not the named tool.
  - Merge duplicates. Leave out benefits, perks and company descriptions.
  - Only include what the text actually says. Never invent requirements.

If the text is not a job description, return an empty title and no requirements.
"""
