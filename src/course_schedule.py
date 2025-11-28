"""Course schedule data and helper utilities."""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional

_SCHEDULE_JSON = """
{
  "schedules": [
    {
      "course": "A1",
      "title": "Course Schedule: A1",
      "class_name": "A1 Frankfurt Klasse",
      "start_date_iso": "2025-10-23",
      "start_date_human": "Thursday, 23 October 2025",
      "timezone": "Africa/Accra",
      "days": [
        {
          "day_number": 1,
          "date": "2025-10-23",
          "weekday": "Thursday",
          "sessions": [
            {
              "chapter": "0.1",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 2,
          "date": "2025-10-24",
          "weekday": "Friday",
          "sessions": [
            {
              "chapter": "0.2",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "1.1",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 3,
          "date": "2025-10-25",
          "weekday": "Saturday",
          "sessions": [
            {
              "chapter": "1.1",
              "type": "Schreiben & Sprechen"
            },
            {
              "chapter": "1.2",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 4,
          "date": "2025-10-30",
          "weekday": "Thursday",
          "sessions": [
            {
              "chapter": "2",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 5,
          "date": "2025-10-31",
          "weekday": "Friday",
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
          "date": "2025-11-01",
          "weekday": "Saturday",
          "sessions": [
            {
              "chapter": "2.3",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 7,
          "date": "2025-11-06",
          "weekday": "Thursday",
          "sessions": [
            {
              "chapter": "3",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 8,
          "date": "2025-11-07",
          "weekday": "Friday",
          "sessions": [
            {
              "chapter": "4",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 9,
          "date": "2025-11-08",
          "weekday": "Saturday",
          "sessions": [
            {
              "chapter": "5",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 10,
          "date": "2025-11-13",
          "weekday": "Thursday",
          "sessions": [
            {
              "chapter": "6",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "2.4",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 11,
          "date": "2025-11-14",
          "weekday": "Friday",
          "sessions": [
            {
              "chapter": "7",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 12,
          "date": "2025-11-15",
          "weekday": "Saturday",
          "sessions": [
            {
              "chapter": "8",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 13,
          "date": "2025-11-20",
          "weekday": "Thursday",
          "sessions": [
            {
              "chapter": "3.5",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 14,
          "date": "2025-11-21",
          "weekday": "Friday",
          "sessions": [
            {
              "chapter": "3.6",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 15,
          "date": "2025-11-22",
          "weekday": "Saturday",
          "sessions": [
            {
              "chapter": "4.7",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 16,
          "date": "2025-11-27",
          "weekday": "Thursday",
          "sessions": [
            {
              "chapter": "9",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "10",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 17,
          "date": "2025-11-28",
          "weekday": "Friday",
          "sessions": [
            {
              "chapter": "11",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 18,
          "date": "2025-11-29",
          "weekday": "Saturday",
          "sessions": [
            {
              "chapter": "12.1",
              "type": "Lesen & Hören"
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
          "date": "2025-12-04",
          "weekday": "Thursday",
          "sessions": [
            {
              "chapter": "5.9",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 20,
          "date": "2025-12-05",
          "weekday": "Friday",
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
          "date": "2025-12-06",
          "weekday": "Saturday",
          "sessions": [
            {
              "chapter": "13",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "6.11",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 22,
          "date": "2025-12-11",
          "weekday": "Thursday",
          "sessions": [
            {
              "chapter": "14.1",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "7.12",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 23,
          "date": "2025-12-12",
          "weekday": "Friday",
          "sessions": [
            {
              "chapter": "14.2",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "7.12",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 24,
          "date": "2025-12-13",
          "weekday": "Saturday",
          "sessions": [
            {
              "chapter": "8.13",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 25,
          "date": "2025-12-18",
          "weekday": "Thursday",
          "sessions": [
            {
              "chapter": "Exam tips",
              "type": "Schreiben & Sprechen",
              "note": "Recap"
            }
          ]
        }
      ]
    },
    {
      "course": "A1",
      "title": "Course Schedule: A1",
      "class_name": "A1 Munich Klasse",
      "start_date_iso": "2025-12-03",
      "start_date_human": "Wednesday, 3 December 2025",
      "timezone": "Africa/Accra",
      "days": [
        {
          "day_number": 1,
          "date": "2025-12-03",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "0.1",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 2,
          "date": "2025-12-08",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "0.2",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "1.1",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 3,
          "date": "2025-12-09",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "1.1",
              "type": "Schreiben & Sprechen"
            },
            {
              "chapter": "1.2",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 4,
          "date": "2025-12-10",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "2",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 5,
          "date": "2025-12-15",
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
          "date": "2025-12-16",
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
          "date": "2025-12-17",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "3",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 8,
          "date": "2025-12-22",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "4",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 9,
          "date": "2025-12-23",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "5",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 10,
          "date": "2025-12-24",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "6",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "2.4",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 11,
          "date": "2025-12-29",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "7",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 12,
          "date": "2025-12-30",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "8",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 13,
          "date": "2025-12-31",
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
          "date": "2026-01-05",
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
          "date": "2026-01-06",
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
          "date": "2026-01-07",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "9",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "10",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 17,
          "date": "2026-01-12",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "11",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 18,
          "date": "2026-01-13",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "12.1",
              "type": "Lesen & Hören"
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
          "date": "2026-01-14",
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
          "date": "2026-01-19",
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
          "date": "2026-01-20",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "13",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "6.11",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 22,
          "date": "2026-01-21",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "14.1",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "7.12",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 23,
          "date": "2026-01-26",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "14.2",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "7.12",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 24,
          "date": "2026-01-27",
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
          "date": "2026-01-28",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "Exam tips",
              "type": "Schreiben & Sprechen",
              "note": "Recap"
            }
          ]
        }
      ]
    }
  ],
      "generated_note": "Schedule generated by Learn Language Education Academy."
    },
    {
      "course": "A1",
      "title": "Course Schedule: A1",
      "class_name": "A1 Bonn Klasse",
      "start_date_iso": "2025-11-10",
      "start_date_human": "Monday, 10 November 2025",
      "timezone": "Africa/Accra",
      "days": [
        {
          "day_number": 1,
          "date": "2025-11-10",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "0.1",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 2,
          "date": "2025-11-11",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "0.2",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "1.1",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 3,
          "date": "2025-11-17",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "1.1",
              "type": "Schreiben & Sprechen"
            },
            {
              "chapter": "1.2",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 4,
          "date": "2025-11-18",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "2",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 5,
          "date": "2025-11-19",
          "weekday": "Wednesday",
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
          "date": "2025-11-24",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "2.3",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 7,
          "date": "2025-11-25",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "3",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 8,
          "date": "2025-11-26",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "4",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 9,
          "date": "2025-12-01",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "5",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 10,
          "date": "2025-12-02",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "6",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "2.4",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 11,
          "date": "2025-12-03",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "7",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 12,
          "date": "2025-12-08",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "8",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 13,
          "date": "2025-12-09",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "3.5",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 14,
          "date": "2025-12-10",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "3.6",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 15,
          "date": "2025-12-15",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "4.7",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 16,
          "date": "2025-12-16",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "9",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "10",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 17,
          "date": "2025-12-17",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "11",
              "type": "Lesen & Hören"
            }
          ]
        },
        {
          "day_number": 18,
          "date": "2025-12-22",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "12.1",
              "type": "Lesen & Hören"
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
          "date": "2025-12-23",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "5.9",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 20,
          "date": "2026-01-05",
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
          "date": "2026-01-06",
          "weekday": "Tuesday",
          "sessions": [
            {
              "chapter": "13",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "6.11",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 22,
          "date": "2026-01-07",
          "weekday": "Wednesday",
          "sessions": [
            {
              "chapter": "14.1",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "7.12",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 23,
          "date": "2026-01-12",
          "weekday": "Monday",
          "sessions": [
            {
              "chapter": "14.2",
              "type": "Lesen & Hören"
            },
            {
              "chapter": "7.12",
              "type": "Schreiben & Sprechen"
            }
          ]
        },
        {
          "day_number": 24,
          "date": "2026-01-13",
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
          "date": "2026-01-14",
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
      "class_name": "A2 Bonn Klasse",
      "start_date_iso": "2025-11-25",
      "start_date_human": "Tuesday, 25 November 2025",
      "timezone": "Africa/Accra",
      "days": [
        {
          "day_number": 1,
          "date": "2025-11-25",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "1.1. Small Talk (Exercise)"
            }
          ]
        },
        {
          "day_number": 2,
          "date": "2025-11-26",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "1.2. Personen Beschreiben (Exercise)"
            }
          ]
        },
        {
          "day_number": 3,
          "date": "2025-11-27",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "1.3. Dinge und Personen vergleichen"
            }
          ]
        },
        {
          "day_number": 4,
          "date": "2025-12-02",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "2.4. Wo möchten wir uns treffen?"
            }
          ]
        },
        {
          "day_number": 5,
          "date": "2025-12-03",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "2.5. Was machst du in deiner Freizeit?"
            }
          ]
        },
        {
          "day_number": 6,
          "date": "2025-12-04",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "3.6. Möbel und Räume kennenlernen"
            }
          ]
        },
        {
          "day_number": 7,
          "date": "2025-12-09",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "3.7. Eine Wohnung suchen (Übung)"
            }
          ]
        },
        {
          "day_number": 8,
          "date": "2025-12-10",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "3.8. Rezepte und Essen (Exercise)"
            }
          ]
        },
        {
          "day_number": 9,
          "date": "2025-12-11",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "4.9. Urlaub"
            }
          ]
        },
        {
          "day_number": 10,
          "date": "2025-12-16",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "4.10. Tourismus und Traditionelle Feste"
            }
          ]
        },
        {
          "day_number": 11,
          "date": "2025-12-17",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "4.11. Unterwegs: Verkehrsmittel vergleichen"
            }
          ]
        },
        {
          "day_number": 12,
          "date": "2025-12-18",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "5.12. Ein Tag im Leben (Übung)"
            }
          ]
        },
        {
          "day_number": 13,
          "date": "2025-12-23",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "5.13. Ein Vorstellungsgesprach (Exercise)"
            }
          ]
        },
        {
          "day_number": 14,
          "date": "2025-12-24",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "5.14. Beruf und Karriere (Exercise)"
            }
          ]
        },
        {
          "day_number": 15,
          "date": "2026-01-06",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "6.15. Mein Lieblingssport"
            }
          ]
        },
        {
          "day_number": 16,
          "date": "2026-01-07",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "6.16. Wohlbefinden und Entspannung"
            }
          ]
        },
        {
          "day_number": 17,
          "date": "2026-01-08",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "6.17. In die Apotheke gehen"
            }
          ]
        },
        {
          "day_number": 18,
          "date": "2026-01-13",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "7.18. Die Bank Anrufen"
            }
          ]
        },
        {
          "day_number": 19,
          "date": "2026-01-14",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "7.19. Einkaufen ? Wo und wie? (Exercise)"
            }
          ]
        },
        {
          "day_number": 20,
          "date": "2026-01-15",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "7.20. Typische Reklamationssituationen üben"
            }
          ]
        },
        {
          "day_number": 21,
          "date": "2026-01-20",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "8.21. Ein Wochenende planen"
            }
          ]
        },
        {
          "day_number": 22,
          "date": "2026-01-21",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "8.22. Die Woche Plannung"
            }
          ]
        },
        {
          "day_number": 23,
          "date": "2026-01-22",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "9.23. Wie kommst du zur Schule / zur Arbeit?"
            }
          ]
        },
        {
          "day_number": 24,
          "date": "2026-01-27",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "9.24. Einen Urlaub planen"
            }
          ]
        },
        {
          "day_number": 25,
          "date": "2026-01-28",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "9.25. Tagesablauf (Exercise)"
            }
          ]
        },
        {
          "day_number": 26,
          "date": "2026-01-29",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "10.26. Gefühle in verschiedenen Situationen beschr"
            }
          ]
        },
        {
          "day_number": 27,
          "date": "2026-02-03",
          "weekday": "Tuesday",
          "sessions": [
            {
              "title": "10.27. Digitale Kommunikation"
            }
          ]
        },
        {
          "day_number": 28,
          "date": "2026-02-04",
          "weekday": "Wednesday",
          "sessions": [
            {
              "title": "10.28. Über die Zukunft sprechen"
            }
          ]
        }
      ],
      "generated_note": "Schedule generated by Learn Language Education Academy."
    },
    {
      "course": "B1",
      "title": "Course Schedule: B1",
      "class_name": "B1 Koln Klasse",
      "start_date_iso": "2025-11-20",
      "start_date_human": "Thursday, 20 November 2025",
      "timezone": "Africa/Accra",
      "days": [
        {
          "day_number": 1,
          "date": "2025-11-20",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "1.1. Traumwelten (Übung)"
            }
          ]
        },
        {
          "day_number": 2,
          "date": "2025-11-21",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "1.2. Freundes für Leben (Übung)"
            }
          ]
        },
        {
          "day_number": 3,
          "date": "2025-11-27",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "1.3. Erfolgsgeschichten (Übung)"
            }
          ]
        },
        {
          "day_number": 4,
          "date": "2025-11-28",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "2.4. Wohnung suchen (Übung)"
            }
          ]
        },
        {
          "day_number": 5,
          "date": "2025-12-04",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "2.5. Der Besichtigungsg termin (Übung)"
            }
          ]
        },
        {
          "day_number": 6,
          "date": "2025-12-05",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "2.6. Leben in der Stadt oder auf dem Land?"
            }
          ]
        },
        {
          "day_number": 7,
          "date": "2025-12-11",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "3.7. Fast Food vs. Hausmannskost"
            }
          ]
        },
        {
          "day_number": 8,
          "date": "2025-12-12",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "3.8. Alles für die Gesundheit"
            }
          ]
        },
        {
          "day_number": 9,
          "date": "2025-12-18",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "3.9. Work-Life-Balance im modernen Arbeitsumfeld"
            }
          ]
        },
        {
          "day_number": 10,
          "date": "2025-12-19",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "4.10. Digitale Auszeit und Selbstfürsorge"
            }
          ]
        },
        {
          "day_number": 11,
          "date": "2026-01-01",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "4.11. Teamspiele und Kooperative Aktivitäten"
            }
          ]
        },
        {
          "day_number": 12,
          "date": "2026-01-02",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "4.12. Abenteuer in der Natur"
            }
          ]
        },
        {
          "day_number": 13,
          "date": "2026-01-08",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "4.13. Eigene Filmkritik schreiben"
            }
          ]
        },
        {
          "day_number": 14,
          "date": "2026-01-09",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "5.14. Traditionelles vs. digitales Lernen"
            }
          ]
        },
        {
          "day_number": 15,
          "date": "2026-01-15",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "5.15. Medien und Arbeiten im Homeoffice"
            }
          ]
        },
        {
          "day_number": 16,
          "date": "2026-01-16",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "5.16. Prüfungsangst und Stressbewältigung"
            }
          ]
        },
        {
          "day_number": 17,
          "date": "2026-01-22",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "5.17. Wie lernt man am besten?"
            }
          ]
        },
        {
          "day_number": 18,
          "date": "2026-01-23",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "6.18. Wege zum Wunschberuf"
            }
          ]
        },
        {
          "day_number": 19,
          "date": "2026-01-29",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "6.19. Das Vorstellungsgespräch"
            }
          ]
        },
        {
          "day_number": 20,
          "date": "2026-01-30",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "6.20. Wie wird man ?? (Ausbildung und Qu)"
            }
          ]
        },
        {
          "day_number": 21,
          "date": "2026-02-05",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "7.21. Lebensformen heute ? Familie, Wohnge"
            }
          ]
        },
        {
          "day_number": 22,
          "date": "2026-02-06",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "7.22. Was ist dir in einer Beziehung wichtig?"
            }
          ]
        },
        {
          "day_number": 23,
          "date": "2026-02-12",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "7.23. Erstes Date ? Typische Situationen"
            }
          ]
        },
        {
          "day_number": 24,
          "date": "2026-02-13",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "8.24. Konsum und Nachhaltigkeit"
            }
          ]
        },
        {
          "day_number": 25,
          "date": "2026-02-19",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "8.25. Online einkaufen ? Rechte und Risiken"
            }
          ]
        },
        {
          "day_number": 26,
          "date": "2026-02-20",
          "weekday": "Friday",
          "sessions": [
            {
              "title": "9.26. Reiseprobleme und Lösungen"
            }
          ]
        },
        {
          "day_number": 27,
          "date": "2026-02-26",
          "weekday": "Thursday",
          "sessions": [
            {
              "title": "10.27. Umweltfreundlich im Alltag"
            }
          ]
        },
        {
          "day_number": 28,
          "date": "2026-02-27",
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
  "version": "2025-11-05T00:00:00Z"
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

def session_details_for_date(
    class_name: str,
    session_date: date,
) -> Optional[Dict[str, Any]]:
    """Return structured session details for ``session_date``.

    The result contains the day number (when provided in the schedule) and a
    list of formatted session labels describing each activity on that day.
    """
    schedule = get_schedule_for_class(class_name)
    if not schedule:
        return None

    target = session_date.isoformat()
    for day in _iter_days(schedule):
        if str(day.get("date")) != target:
            continue

        sessions = day.get("sessions", [])
        formatted_sessions: List[str] = []
        if isinstance(sessions, list):
            for session in sessions:
                if not isinstance(session, dict):
                    continue
                label = _format_session(session)
                if label:
                    formatted_sessions.append(label)

        if not formatted_sessions:
            return None

        day_number = day.get("day_number")
        return {
            "day_number": day_number if isinstance(day_number, int) else None,
            "sessions": formatted_sessions,
        }

    return None

def session_summary_for_date(class_name: str, session_date: date) -> Optional[str]:
    """Return a concise summary of the lessons for ``session_date``.

    Parameters
    ----------
    class_name:
        Name of the class as shown on the dashboard, e.g. ``"A1 Munich Klasse"``.
    session_date:
        The calendar date of the upcoming class.
    """
    details = session_details_for_date(class_name, session_date)
    if not details:
        return None

    summary = " • ".join(details.get("sessions", []))
    if not summary:
        return None

    day_number = details.get("day_number")
    if isinstance(day_number, int):
        return f"Day {day_number} — {summary}"
    return summary


def next_session_details(
    class_name: str, from_date: Optional[date] = None
) -> Optional[Dict[str, Any]]:
    """Return the next upcoming session for the given class.

    Parameters
    ----------
    class_name:
        Name of the class as shown on the dashboard.
    from_date:
        Date from which to search for the next session. Defaults to today.
    """

    schedule = get_schedule_for_class(class_name)
    if not schedule:
        return None

    start_date = from_date or date.today()

    for day in _iter_days(schedule):
        session_date_raw = day.get("date")
        try:
            session_date = date.fromisoformat(str(session_date_raw))
        except Exception:
            continue

        if session_date < start_date:
            continue

        details = session_details_for_date(class_name, session_date)
        if not details:
            continue

        weekday = day.get("weekday") if isinstance(day.get("weekday"), str) else None
        summary = session_summary_for_date(class_name, session_date)
        return {
            "date": session_date,
            "date_iso": session_date.isoformat(),
            "weekday": weekday,
            "day_number": details.get("day_number"),
            "sessions": details.get("sessions"),
            "summary": summary,
        }

    return None
