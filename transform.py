import re
import os
import requests
from icalendar import Calendar
from datetime import datetime
from pytz import UTC

# ---- 1) Forrás feed ----
SOURCE_ICS_URL = "https://app-public.unibocconi.it:443/Calendars/Calendari/GetCalendarioUtenteByToken?token=AmmEpSp7PctakrHP5RD9JroCeRBXTRWQCA1bi6aCFzQ1&iv=4k3mS7wfGkEEKIX6Zv2dLQ2&format=ical"

# ---- 2) Kód -> tárgynév (marad, hogy a címek szépek legyenek) ----
CODE_TO_NAME = {
    "30398": "Computer Science",
    "30408": "Statistics II",
    "30407": "Math II",
    "30509": "Computer Programming",
    "30409": "Macro",
}

# ---- 3) SZŰRÉS beállítás ----
# Pontosan EGYIKET használd:
# a) CSAK ezek a kódok maradjanak:
INCLUDE_CODES = {
   "30407", "30408" , "30398" , "30409" , "30509"
}


def parse_code_and_rest(summary: str):
    """
    Visszaadja (code, rest) párost, ha a sor elején kurzuskód áll.
    Példa: '30407 – Aula N17 [L]*' -> ('30407', 'Aula N17 [L]*')
    Ha nincs kód a sor elején, (None, summary)-t ad vissza.
    """
    s = summary.strip()
    m = re.match(r"^(\d+)\s*[–—-]\s*(.*)", s)
    if m:
        return m.group(1), m.group(2)
    return None, s

def make_new_summary(code: str, rest: str) -> str:
    """
    A kódot tárgynévre cseréli, és hozzárakja a '— rest' részt, ha van.
    """
    name = CODE_TO_NAME.get(code, code)  # ha nincs név, marad a kód (ritka)
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

        # ---- SZŰRÉS LOGIKA ----
        # Ha meg van adva INCLUDE_CODES, akkor csak azokat tartjuk meg
        if INCLUDE_CODES:
            if not code or code not in INCLUDE_CODES:
                to_remove.append(component)
                continue

        # ---- CÍM ÁTÍRÁS ----
        if code:
            new_summary = make_new_summary(code, rest)
            component["SUMMARY"] = new_summary
        # Ha nincs kód, hagyjuk érintetlenül

        if not component.get("DTSTAMP"):
            component["DTSTAMP"] = datetime.now(UTC)

    # Nem kívánt események eltávolítása
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
