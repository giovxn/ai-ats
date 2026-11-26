"""Run the Block 4 evidence check for every candidate that doesn't have it yet (pending or failed).

One AI call per candidate. Safe to run again: candidates already checked are skipped.

    uv run python backfill_evidence.py
"""

import db
import llm
from main import check_evidence


def main() -> None:
    db.init_db()  # adds the Block 4 columns to an older database
    candidates = db.candidates_without_evidence()
    print(f"{len(candidates)} candidate(s) to check")
    failed = 0
    for candidate in candidates:
        try:
            checked = check_evidence(candidate)
            buried = [r.text for r in checked.evidence.requirements if r.buried]
            print(f"  #{candidate.id} {candidate.name}: done" + (f", buried: {buried}" if buried else ""))
        except llm.LLMError as error:
            failed += 1
            print(f"  #{candidate.id} {candidate.name}: failed ({error})")
    print(f"Finished: {len(candidates) - failed} checked, {failed} failed (run again to retry)")


if __name__ == "__main__":
    main()
