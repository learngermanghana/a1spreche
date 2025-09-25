import pandas as pd

from src.lesson_language_support import gather_language_support


def test_gather_language_support_prioritises_keyword_matches():
    info = {
        "goal": "Learn to greet people and introduce yourself in German.",
        "grammar_topic": "Formal and informal greetings",
        "lesen_hören": [
            {"chapter": "0.1", "note": "Focus on greetings and introductions."},
        ],
    }
    df = pd.DataFrame(
        [
            {"level": "A1", "german": "Der Preis", "english": "the price", "example": "Der Preis ist hoch."},
            {
                "level": "A1",
                "german": "Guten Tag",
                "english": "formal greeting",
                "example": "Guten Tag! Wie geht es Ihnen?",
            },
            {
                "level": "A1",
                "german": "sich vorstellen",
                "english": "to introduce oneself",
                "example": "Ich möchte mich vorstellen.",
            },
        ]
    )

    fallback = {"A1": [("Danke", "thank you")]}

    suggestions = gather_language_support(info, "A1", df, fallback, limit=3)

    assert len(suggestions) == 2
    assert suggestions[0]["german"] == "Guten Tag"
    assert "introduce" in suggestions[1]["english"]


def test_gather_language_support_falls_back_to_vocab_lists():
    info = {"goal": "Review travel vocabulary."}
    fallback = {"A1": [("reisen", "to travel"), ("der Flughafen", "the airport")]}

    suggestions = gather_language_support(info, "A1", pd.DataFrame(), fallback, limit=2)

    assert [s["german"] for s in suggestions] == ["reisen", "der Flughafen"]
