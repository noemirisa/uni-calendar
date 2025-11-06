# transform.py
import re
import os
import requests
from icalendar import Calendar
from datetime import datetime
from pytz import UTC

# --- Hardcoded source URL (as requested) ---
SOURCE_ICS_URL = "https://app-public.unibocconi.it:443/Calendars/Calendari/GetCalendarioUtenteByToken?token=AmmEpSp7PctakrHP5RD9JroCeRBXTRWQCA1bi6aCFzQ1&iv=4k3mS7wfGkEEKIX6Zv2dLQ2&format=ical"

# --- Course code → name map (current + next semester) ---
CODE_TO_NAME = {
    # current semester
    "30398": "Computer Science",
    "30408": "Statistics II",
    "30509": "Computer Programming",
    "30407": "Mathematics",

    # next semester
    "30650": "IP Law",
    "30412": "Machine Learning",
    "30413": "Econometrics",
    "30414": "Finance",
    "30405": "IT Law",
}

# Keep ONLY these codes (union of both semesters)
INCLUDE_CODES = set(CODE_TO_NAME.keys())


def parse_code_and_rest(summary: str):
    """
    Extract (code, rest) if the summary begins with a numeric code followed by a dash.
    Matches: '30407 – Aula N17', '30407 - Aula N17', '30407—Aula N17'
    """
    s = summary.strip()
    m = re.match(r"^(\d+)\s*[–—-]\s*(.*)", s)
    if m:
        return m.group(1), m.group(2)
    return None, s


def make_new_summary(code: str, rest: str) -> str:
    name = CODE_TO_NAME.get(code, code)
    return f"{name} — {rest}" if rest else name


def transform_calendar(ics_bytes: bytes) -> bytes:
    cal = Calendar.from_ical(ics_bytes)
    to_remove = []

    for component in cal.walk("VEVENT"):
        if component.name != "VEVENT":
            continue

        summary = component.get("summary")
        if not summary:
            continue

        code, rest = parse_code_and_rest(str(summary))

        # Filter: keep only selected course codes
        if INCLUDE_CODES and (not code or code not in INCLUDE_CODES):
            to_remove.append(component)
            continue

        # Rename: replace code with friendly course name
        if code:
            component["SUMMARY"] = make_new_summary(code, rest)

        # Ensure DTSTAMP exists
        if not component.get("DTSTAMP"):
            component["DTSTAMP"] = datetime.now(UTC)

    # Remove unwanted events
    for ev in to_remove:
        cal.subcomponents.remove(ev)

    return cal.to_ical()


def main():
    url = SOURCE_ICS_URL.replace("webcal://", "https://")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    out = transform_calendar(r.content)

    os.makedirs("docs", exist_ok=True)
    with open("docs/feed.ics", "wb") as f:
        f.write(out)


if __name__ == "__main__":
    main()
