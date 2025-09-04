import re
import os
import requests
from icalendar import Calendar
from datetime import datetime
from pytz import UTC

SOURCE_ICS_URL = "https://app-public.unibocconi.it:443/Calendars/Calendari/GetCalendarioUtenteByToken?token=AmmEpSp7PctakrHP5RD9JroCeRBXTRWQCA1bi6aCFzQ1&iv=4k3mS7wfGkEEKIX6Zv2dLQ2&format=ical"

# kurzuskód → tárgynév
CODE_TO_NAME = {
    "30398": "Computer Science",
    "30408": "Statistics II",
    "30407": "Math II",
    "30509": "Computer Programming",
    "30409": "Macro",
}

def clean_summary(s: str) -> str:
    """
    Lecseréli az elején lévő kurzuskódot a tárgynévre,
    és megtartja az utána lévő szöveget (pl. Aula).
    """
    s = s.strip()

    # próbáljunk kurzuskódot találni a sor elején
    m = re.match(r"^(\d+)\s*[–—-]\s*(.*)", s)
    if m:
        code, rest = m.groups()
        if code in CODE_TO_NAME:
            name = CODE_TO_NAME[code]
            if rest:
                return f"{name} — {rest}"
            else:
                return name

    # ha nem talál kódot, hagyja úgy
    return s

def transform_calendar(ics_bytes: bytes) -> bytes:
    cal = Calendar.from_ical(ics_bytes)

    for component in cal.walk("VEVENT"):
        summary = component.get("summary")
        if summary:
            new_summary = clean_summary(str(summary))
            component["SUMMARY"] = new_summary

        if not component.get("DTSTAMP"):
            component["DTSTAMP"] = datetime.now(UTC)

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
