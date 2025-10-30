"""Course schedule data and helper utilities."""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Tuple

_SCHEDULE_JSON = """
{
  "schedules": [
    {
      "course": "A1",
      "title": "Course Schedule: A1",
      "class_name": "A1 Munich Klasse",
      "start_date_iso": "2025-09-17",
      "start_date_human": "Wednesday, 17 September 2025",
      "timezone": "Africa/Accra",
      "days": [
        {
          "day_number": 1,
          "date": "2025-09-17",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "0.1",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 2,
          "date": "2025-09-22",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "0.2",
              "type": "Lesen & H\u00f6ren"
            },
            {
              "chapter": "1.1",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 3,
          "date": "2025-09-23",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "1.1",
              "type": "Schreiben & Sprechen"
            },
            {
              "chapter": "1.2",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 4,
          "date": "2025-09-24",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "2",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 5,
          "date": "2025-09-29",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "1.2",
              "type": "Schreiben & Sprechen",
              "note": "Recap"
            }
          ]
        },
        {
          "day_number": 6,
          "date": "2025-09-30",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "2.3",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 7,
          "date": "2025-10-01",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "3",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 8,
          "date": "2025-10-06",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "4",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 9,
          "date": "2025-10-07",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "5",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 10,
          "date": "2025-10-08",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "6",
              "type": "Lesen & H\u00f6ren"
            },
            {
              "chapter": "2.4",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 11,
          "date": "2025-10-13",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "7",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 12,
          "date": "2025-10-14",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "8",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 13,
          "date": "2025-10-15",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "3.5",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 14,
          "date": "2025-10-20",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "3.6",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 15,
          "date": "2025-10-21",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "4.7",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 16,
          "date": "2025-10-22",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "9",
              "type": "Lesen & H\u00f6ren"
            },
            {
              "chapter": "10",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 17,
          "date": "2025-10-27",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "11",
              "type": "Lesen & H\u00f6ren"
            }
          ]
        },
        {
          "day_number": 18,
          "date": "2025-10-28",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "12.1",
              "type": "Lesen & H\u00f6ren"
            },
            {
              "chapter": "12.1",
              "type": "Schreiben & Sprechen",
              "note": "including 5.8"
            }
          ]
        },
        {
          "day_number": 19,
          "date": "2025-10-29",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "5.9",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 20,
          "date": "2025-11-03",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "6.10",
              "type": "Schreiben & Sprechen",
              "note": "Intro to letter writing"
            }
          ]
        },
        {
          "day_number": 21,
          "date": "2025-11-04",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "13",
              "type": "Lesen & H\u00f6ren"
            },
            {
              "chapter": "6.11",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 22,
          "date": "2025-11-05",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "14.1",
              "type": "Lesen & H\u00f6ren"
            },
            {
              "chapter": "7.12",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 23,
          "date": "2025-11-10",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "14.2",
              "type": "Lesen & H\u00f6ren"
            },
            {
              "chapter": "7.12",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 24,
          "date": "2025-11-11",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "8.13",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 25,
          "date": "2025-11-12",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "Exam tips",
              "type": "Schreiben & Sprechen",
              "note": "Recap"
            }
          ]
        }
      ],
      "generated_note": "Schedule generated by Learn Language Education Academy."
    },
    {
      "course": "A2",
      "title": "Course Schedule: A2",
      "class_name": "A2 Munich Klasse",
      "start_date_iso": "2025-09-16",
      "start_date_human": "Tuesday, 16 September 2025",
      "timezone": "Africa/Accra",
      "days": [
        {
          "day_number": 1,
          "date": "2025-09-16",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "1.1. Small Talk (Exercise)"
            }
          ]
        },
        {
          "day_number": 2,
          "date": "2025-09-17",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "1.2. Personen Beschreiben (Exercise)"
            }
          ]
        },
        {
          "day_number": 3,
          "date": "2025-09-22",
          "weekday": "Monday",
          "sessions": [
            {
              "title": "1.3. Dinge und Personen vergleichen"
            }
          ]
        },
        {
          "day_number": 4,
          "date": "2025-09-23",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "2.4. Wo m\u00f6chten wir uns treffen?"
            }
          ]
        },
        {
          "day_number": 5,
          "date": "2025-09-24",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "2.5. Was machst du in deiner Freizeit?"
            }
          ]
        },
        {
          "day_number": 6,
          "date": "2025-09-29",
          "weekday": "Monday",
          "sessions": [
            {
              "title": "3.6. M\u00f6bel und R\u00e4ume kennenlernen"
            }
          ]
        },
        {
          "day_number": 7,
          "date": "2025-09-30",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "3.7. Eine Wohnung suchen (\u00dcbung)"
            }
          ]
        },
        {
          "day_number": 8,
          "date": "2025-10-01",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "3.8. Rezepte und Essen (Exercise)"
            }
          ]
        },
        {
          "day_number": 9,
          "date": "2025-10-06",
          "weekday": "Monday",
          "sessions": [
            {
              "title": "4.9. Urlaub"
            }
          ]
        },
        {
          "day_number": 10,
          "date": "2025-10-07",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "4.10. Tourismus und Traditionelle Feste"
            }
          ]
        },
        {
          "day_number": 11,
          "date": "2025-10-08",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "4.11. Unterwegs: Verkehrsmittel vergleichen"
            }
          ]
        },
        {
          "day_number": 12,
          "date": "2025-10-13",
          "weekday": "Monday",
          "sessions": [
            {
              "title": "5.12. Ein Tag im Leben (\u00dcbung)"
            }
          ]
        },
        {
          "day_number": 13,
          "date": "2025-10-14",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "5.13. Ein Vorstellungsgesprach (Exercise)"
            }
          ]
        },
        {
          "day_number": 14,
          "date": "2025-10-15",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "5.14. Beruf und Karriere (Exercise)"
            }
          ]
        },
        {
          "day_number": 15,
          "date": "2025-10-20",
          "weekday": "Monday",
          "sessions": [
            {
              "title": "6.15. Mein Lieblingssport"
            }
          ]
        },
        {
          "day_number": 16,
          "date": "2025-10-21",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "6.16. Wohlbefinden und Entspannung"
            }
          ]
        },
        {
          "day_number": 17,
          "date": "2025-10-22",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "6.17. In die Apotheke gehen"
            }
          ]
        },
        {
          "day_number": 18,
          "date": "2025-10-27",
          "weekday": "Monday",
          "sessions": [
            {
              "title": "7.18. Die Bank Anrufen"
            }
          ]
        },
        {
          "day_number": 19,
          "date": "2025-10-28",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "7.19. Einkaufen ? Wo und wie? (Exercise)"
            }
          ]
        },
        {
          "day_number": 20,
          "date": "2025-10-29",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "7.20. Typische Reklamationssituationen \u00fcben"
            }
          ]
        },
        {
          "day_number": 21,
          "date": "2025-11-03",
          "weekday": "Monday",
          "sessions": [
            {
              "title": "8.21. Ein Wochenende planen"
            }
          ]
        },
        {
          "day_number": 22,
          "date": "2025-11-04",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "8.22. Die Woche Plannung"
            }
          ]
        },
        {
          "day_number": 23,
          "date": "2025-11-05",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "9.23. Wie kommst du zur Schule / zur Arbeit?"
            }
          ]
        },
        {
          "day_number": 24,
          "date": "2025-11-10",
          "weekday": "Monday",
          "sessions": [
            {
              "title": "9.24. Einen Urlaub planen"
            }
          ]
        },
        {
          "day_number": 25,
          "date": "2025-11-11",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "9.25. Tagesablauf (Exercise)"
            }
          ]
        },
        {
          "day_number": 26,
          "date": "2025-11-12",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "10.26. Gef\u00fchle in verschiedenen Situationen beschr"
            }
          ]
        },
        {
          "day_number": 27,
          "date": "2025-11-17",
          "weekday": "Monday",
          "sessions": [
            {
              "title": "10.27. Digitale Kommunikation"
            }
          ]
        },
        {
          "day_number": 28,
          "date": "2025-11-18",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "10.28. \u00dcber die Zukunft sprechen"
            }
          ]
        }
      ],
      "generated_note": "Schedule generated by Learn Language Education Academy."
    },
    {
      "course": "B1",
      "title": "Course Schedule: B1",
      "class_name": "B1 Munich Klasse",
      "start_date_iso": "2025-08-07",
      "start_date_human": "Thursday, 07 August 2025",
      "timezone": "Africa/Accra",
      "days": [
        {
          "day_number": 1,
          "date": "2025-08-07",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "1.1. Traumwelten (\u00dcbung)"
            }
          ]
        },
        {
          "day_number": 2,
          "date": "2025-08-08",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "1.2. Freundes f\u00fcr Leben (\u00dcbung)"
            }
          ]
        },
        {
          "day_number": 3,
          "date": "2025-08-14",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "1.3. Erfolgsgeschichten (\u00dcbung)"
            }
          ]
        },
        {
          "day_number": 4,
          "date": "2025-08-15",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "2.4. Wohnung suchen (\u00dcbung)"
            }
          ]
        },
        {
          "day_number": 5,
          "date": "2025-08-21",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "2.5. Der Besichtigungsg termin (\u00dcbung)"
            }
          ]
        },
        {
          "day_number": 6,
          "date": "2025-08-22",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "2.6. Leben in der Stadt oder auf dem Land?"
            }
          ]
        },
        {
          "day_number": 7,
          "date": "2025-08-28",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "3.7. Fast Food vs. Hausmannskost"
            }
          ]
        },
        {
          "day_number": 8,
          "date": "2025-08-29",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "3.8. Alles f\u00fcr die Gesundheit"
            }
          ]
        },
        {
          "day_number": 9,
          "date": "2025-09-04",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "3.9. Work-Life-Balance im modernen Arbeitsumfeld"
            }
          ]
        },
        {
          "day_number": 10,
          "date": "2025-09-05",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "4.10. Digitale Auszeit und Selbstf\u00fcrsorge"
            }
          ]
        },
        {
          "day_number": 11,
          "date": "2025-09-11",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "4.11. Teamspiele und Kooperative Aktivit\u00e4ten"
            }
          ]
        },
        {
          "day_number": 12,
          "date": "2025-09-12",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "4.12. Abenteuer in der Natur"
            }
          ]
        },
        {
          "day_number": 13,
          "date": "2025-09-18",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "4.13. Eigene Filmkritik schreiben"
            }
          ]
        },
        {
          "day_number": 14,
          "date": "2025-09-19",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "5.14. Traditionelles vs. digitales Lernen"
            }
          ]
        },
        {
          "day_number": 15,
          "date": "2025-09-25",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "5.15. Medien und Arbeiten im Homeoffice"
            }
          ]
        },
        {
          "day_number": 16,
          "date": "2025-09-26",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "5.16. Pr\u00fcfungsangst und Stressbew\u00e4ltigung"
            }
          ]
        },
        {
          "day_number": 17,
          "date": "2025-10-02",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "5.17. Wie lernt man am besten?"
            }
          ]
        },
        {
          "day_number": 18,
          "date": "2025-10-03",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "6.18. Wege zum Wunschberuf"
            }
          ]
        },
        {
          "day_number": 19,
          "date": "2025-10-09",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "6.19. Das Vorstellungsgespr\u00e4ch"
            }
          ]
        },
        {
          "day_number": 20,
          "date": "2025-10-10",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "6.20. Wie wird man ?? (Ausbildung und Qu)"
            }
          ]
        },
        {
          "day_number": 21,
          "date": "2025-10-16",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "7.21. Lebensformen heute ? Familie, Wohnge"
            }
          ]
        },
        {
          "day_number": 22,
          "date": "2025-10-17",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "7.22. Was ist dir in einer Beziehung wichtig?"
            }
          ]
        },
        {
          "day_number": 23,
          "date": "2025-10-23",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "7.23. Erstes Date ? Typische Situationen"
            }
          ]
        },
        {
          "day_number": 24,
          "date": "2025-10-24",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "8.24. Konsum und Nachhaltigkeit"
            }
          ]
        },
        {
          "day_number": 25,
          "date": "2025-10-30",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "8.25. Online einkaufen ? Rechte und Risiken"
            }
          ]
        },
        {
          "day_number": 26,
          "date": "2025-10-31",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "9.26. Reiseprobleme und L\u00f6sungen"
            }
          ]
        },
        {
          "day_number": 27,
          "date": "2025-11-06",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "10.27. Umweltfreundlich im Alltag"
            }
          ]
        },
        {
          "day_number": 28,
          "date": "2025-11-07",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "10.28. Klimafreundlich leben"
            }
          ]
        }
      ],
      "generated_note": "Schedule generated by Learn Language Education Academy."
    }
  ],
  "version": "2025-10-30T00:00:00Z"
}
"""


@lru_cache(maxsize=1)
def _load_schedule_data() -> Dict[str, Any]:
    return json.loads(_SCHEDULE_JSON)


def all_schedules() -> List[Dict[str, Any]]:
    """Return all course schedules as a list."""

    data = _load_schedule_data()
    schedules = data.get("schedules", []) if isinstance(data, dict) else []
    return [s for s in schedules if isinstance(s, dict)]


def get_schedule_for_class(class_name: str) -> Optional[Dict[str, Any]]:
    """Return the schedule mapping for ``class_name`` if available."""

    class_name = (class_name or "").strip().lower()
    if not class_name:
        return None
    for schedule in all_schedules():
        if str(schedule.get("class_name", "")).strip().lower() == class_name:
            return schedule
    return None


def _iter_days(schedule: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    days = schedule.get("days", []) if isinstance(schedule, dict) else []
    for day in days:
        if isinstance(day, dict):
            yield day


def _format_session(session: Dict[str, Any]) -> Optional[str]:
    title = session.get("title")
    if isinstance(title, str) and title.strip():
        cleaned = " ".join(title.split())
        note = session.get("note")
        if isinstance(note, str) and note.strip():
            return f"{cleaned} ({note.strip()})"
        return cleaned

    chapter = session.get("chapter")
    session_type = session.get("type")
    parts: List[str] = []
    if isinstance(session_type, str) and session_type.strip():
        parts.append(session_type.strip())
    if isinstance(chapter, str) and chapter.strip():
        parts.append(f"Chapter {chapter.strip()}")
    label = " — ".join(parts)
    if not label:
        return None
    note = session.get("note")
    if isinstance(note, str) and note.strip():
        label = f"{label} ({note.strip()})"
    return label


def _format_sessions(sessions: Iterable[Dict[str, Any]]) -> Optional[str]:
    formatted = []
    for session in sessions:
        if isinstance(session, dict):
            label = _format_session(session)
            if label:
                formatted.append(label)
    if not formatted:
        return None
    return " • ".join(formatted)


def _coerce_day_date(day: Dict[str, Any]) -> Optional[date]:
    """Return the ``datetime.date`` for a schedule entry if available."""

    raw = day.get("date") if isinstance(day, dict) else None
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _build_session_metadata(day: Dict[str, Any], session_date: date) -> Dict[str, Any]:
    """Construct a consistent metadata dictionary for a schedule entry."""

    day_number = day.get("day_number") if isinstance(day.get("day_number"), int) else None
    sessions = day.get("sessions", []) if isinstance(day, dict) else []
    summary = _format_sessions(sessions if isinstance(sessions, list) else [])
    label = summary or ""
    if day_number is not None:
        prefix = f"Day {day_number}"
        label = f"{prefix} — {summary}" if summary else prefix
    return {
        "day_number": day_number,
        "summary": summary,
        "label": label,
        "date": session_date,
        "raw": day,
    }


def session_details_for_date(
    class_name: str,
    session_date: date,
    *,
    course: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return structured metadata for the class meeting on ``session_date``."""

    schedule = get_schedule_for_class(class_name)
    if not schedule and course:
        course_key = (course or "").strip().lower()
        if course_key:
            for candidate in all_schedules():
                course_value = str(candidate.get("course", "")).strip().lower()
                if course_value == course_key:
                    schedule = candidate
                    break
    if not schedule:
        return None

    target = session_date.isoformat()
    for day in _iter_days(schedule):
        if str(day.get("date")) == target:
            meta = _build_session_metadata(day, session_date)
            if not meta.get("label"):
                return None
            return meta
    return None


def session_summary_for_date(class_name: str, session_date: date) -> Optional[str]:
    """Return a concise summary of the lessons for ``session_date``."""

    meta = session_details_for_date(class_name, session_date)
    if not meta:
        return None
    return meta.get("label") or meta.get("summary")


def class_progress_for_date(
    class_name: str,
    reference_date: date,
    *,
    course: Optional[str] = None,
) -> Dict[str, Optional[Dict[str, Any]]]:
    """Return the latest completed and upcoming sessions for ``class_name``."""

    schedule = get_schedule_for_class(class_name)
    if not schedule and course:
        course_key = (course or "").strip().lower()
        if course_key:
            for candidate in all_schedules():
                course_value = str(candidate.get("course", "")).strip().lower()
                if course_value == course_key:
                    schedule = candidate
                    break
    if not schedule:
        return {"previous": None, "upcoming": None}

    day_entries: List[Tuple[date, Dict[str, Any]]] = []
    for day in _iter_days(schedule):
        session_date = _coerce_day_date(day)
        if session_date is None:
            continue
        day_entries.append((session_date, day))

    if not day_entries:
        return {"previous": None, "upcoming": None}

    day_entries.sort(key=lambda item: item[0])

    previous_meta: Optional[Dict[str, Any]] = None
    upcoming_meta: Optional[Dict[str, Any]] = None

    for session_date, day in day_entries:
        meta = _build_session_metadata(day, session_date)
        if session_date <= reference_date:
            previous_meta = meta
        if upcoming_meta is None and session_date >= reference_date:
            upcoming_meta = meta
            if session_date > reference_date:
                break

    return {"previous": previous_meta, "upcoming": upcoming_meta}

