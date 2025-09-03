"""Utility module providing writing prompts by CEFR level."""
from __future__ import annotations

WRITING_PROMPTS = {
    "A1": [
        {
            "Thema": "Schreiben Sie eine E-Mail an Ihren Arzt und sagen Sie Ihren Termin ab.",
            "Punkte": [
                "Warum schreiben Sie?",
                "Sagen Sie: den Grund für die Absage.",
                "Fragen Sie: nach einem neuen Termin."
            ],
        }
    ],
    "A2": [],
    "B1": [],
}


def get_prompts_for_level(level: str):
    """Return writing prompts for a given CEFR level."""
    return WRITING_PROMPTS.get(level.upper(), [])
