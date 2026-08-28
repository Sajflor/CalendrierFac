import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from icalendar import Calendar
from dateutil.rrule import rrulestr


SOURCE = (
    "https://calendar.google.com/calendar/ical/"
    "052fksom69ic4rodovv9auf650%40group.calendar.google.com/"
    "public/basic.ics"
)

# Année universitaire 2026-2027
START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = datetime(2027, 9, 1, tzinfo=timezone.utc)


def make_aware(dt):
    if dt is None:
        return None

    if not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def event_overlaps_period(event):
    dtstart = event.get("DTSTART")

    if not dtstart:
        return False

    start = make_aware(dtstart.dt)

    # Événement récurrent
    rrule = event.get("RRULE")

    if rrule:
        parts = []

        for key, values in rrule.items():
            values = [str(value) for value in values]
            parts.append(f"{key}={','.join(values)}")

        rule_string = ";".join(parts)

        try:
            rule = rrulestr(
                rule_string,
                dtstart=start
            )

            occurrences = rule.between(
                START,
                END,
                inc=True
            )

            return len(occurrences) > 0

        except Exception as error:
            print(f"Erreur avec une récurrence : {error}")
            return start < END

    # Événement ponctuel
    dtend = event.get("DTEND")

    if dtend:
        end = make_aware(dtend.dt)
    else:
        end = start

    return start < END and end >= START


# Télécharger le calendrier de la fac
request = urllib.request.Request(
    SOURCE,
    headers={"User-Agent": "UniversityCalendarFilter/1.0"}
)

with urllib.request.urlopen(request) as response:
    data = response.read()


# Lire le calendrier
original = Calendar.from_ical(data)
filtered = Calendar()

# Copier les informations générales du calendrier
for key, value in original.items():
    filtered.add(key, value)


# Filtrer les événements
total = 0
kept = 0

for component in original.walk():

    if component.name != "VEVENT":
        continue

    total += 1

    if event_overlaps_period(component):
        filtered.add_component(component)
        kept += 1


# Écrire le calendrier filtré
Path("calendrier.ics").write_bytes(
    filtered.to_ical()
)

print(f"{total} événements trouvés.")
print(f"{kept} événements conservés.")
