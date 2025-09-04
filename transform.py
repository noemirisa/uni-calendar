import re
import os
import requests
from icalendar import Calendar
from datetime import datetime
from pytz import UTC

# Forrás feed (https, nem webcal)
SOURCE_ICS_URL = "https://app-public.unibocconi.it:443/Calendars/Calendari/GetCalendarioUtenteByToken?token=AmmEpSp7PctakrHP5RD9JroCeRBXTRWQCA1bi6aCFzQ1&iv=4k3mS7wfGkEEKIX6Zv2dLQ2&format=ical"

def clean_summary(s: str) -> str:
    """
    Leveszi az elején álló kurzuskódot + kötőjelet.
    Példa: '30407 – Math II — Aula N17 [L]*' -> 'Math II — Aula N17 [L]*'
    Kezeli: normál kötőjel (-), en dash (–), em dash (—), tetszőleges szóközök.
    """
    s = s.strip()
    # elején: számok + (kötőjel vagy gondolatjel) + szóközök -> törlés
    s = re.sub(r"^\d+\s*[–—-]\s*", "", s)
    return s

def transform_calendar(ics_bytes: bytes) -> bytes:
    cal = Calendar.from_ical(ics_bytes)

    for component in cal.walk("VEVENT"):
        summary = component.get("summary")
        if summary:
            new_summary = clean_summary(str(summary))
            component["SUMMARY"] = new_summary

        # iCloud szereti, ha van DTSTAMP
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
