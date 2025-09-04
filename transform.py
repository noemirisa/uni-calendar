import re
import requests
from icalendar import Calendar
from datetime import datetime
from pytz import UTC

SOURCE_ICS_URL = "https://app-public.unibocconi.it:443/Calendars/Calendari/GetCalendarioUtenteByToken?token=AmmEpSp7PctakrHP5RD9JroCeRBXTRWQCA1bi6aCFzQ1&iv=4k3mS7wfGkEEKIX6Zv2dLQ2&format=ical"

CODE_TO_NAME = {
    "30398": "Computer Science",
    "30408": "Statistics II",
    "30407":  "Math II",
    "30509":  "Computer Programming",
    "30409":  "Macro",
}

SUMMARY_FORMAT = "{code} – {name}"

def best_match(summary: str):
    s = summary.strip()
    if s in CODE_TO_NAME:
        name = CODE_TO_NAME[s]
        return s, SUMMARY_FORMAT.format(code=s, name=name)

    for code in CODE_TO_NAME.keys():
        pattern_start = r"^\s*\b" + re.escape(code) + r"\b"
        if re.search(pattern_start, s):
            name = CODE_TO_NAME[code]
            rest = re.sub(pattern_start, "", s, count=1).lstrip(" -:–—[]()")
            new_summary = SUMMARY_FORMAT.format(code=code, name=name)
            return code, (f"{new_summary} — {rest}" if rest else new_summary)

    for token in re.findall(r"\b\w+\b", s):
        if token in CODE_TO_NAME:
            name = CODE_TO_NAME[token]
            new_summary = SUMMARY_FORMAT.format(code=token, name=name)
            return token, new_summary

    return None, summary

def transform_calendar(ics_bytes: bytes) -> bytes:
    cal = Calendar.from_ical(ics_bytes)
    for component in cal.walk("VEVENT"):
        summary = component.get("summary")
        if summary:
            code, new_summary = best_match(str(summary))
            if code:
                component["SUMMARY"] = new_summary
        if not component.get("DTSTAMP"):
            component["DTSTAMP"] = datetime.now(UTC)
    return cal.to_ical()

def main():
    r = requests.get(SOURCE_ICS_URL, timeout=30)
    r.raise_for_status()
    out = transform_calendar(r.content)
    import os
    os.makedirs("docs", exist_ok=True)
    with open("docs/feed.ics", "wb") as f:
        f.write(out)

if __name__ == "__main__":
    main()
