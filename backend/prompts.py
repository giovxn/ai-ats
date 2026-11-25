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
  - Write each one as a short phrase (under 10 words) in the posting's own terms, for example "5+ years in audit or accounting".
  - must_have is true when the posting presents it as required, and false when it is a plus ("nice to have", "bonus", "preferred"). If the posting doesn't make it clear, use true.
  - Merge duplicates. Leave out benefits, perks and company descriptions.
  - Only include what the text actually says. Never invent requirements.

If the text is not a job description, return an empty title and no requirements.
"""
