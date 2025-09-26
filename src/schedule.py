"""Course schedule utilities."""
from __future__ import annotations

from typing import Dict, List
import re
import streamlit as st


def _strip_topic_chapter(schedule: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Remove trailing chapter references from lesson topics.

    Some schedule entries duplicate the chapter number in the ``topic`` field
    (e.g. ``"Mein Lieblingssport 6.15"`` with ``chapter="6.15"``).  The UI
    already displays the chapter separately, so keep the chapter number solely
    in the ``chapter`` field and ensure ``topic`` only holds the lesson name.
    """

    for item in schedule:
        topic = item.get("topic")
        chapter = item.get("chapter")
        if isinstance(topic, str) and isinstance(chapter, str) and chapter:
            pattern = rf"\s*{re.escape(chapter)}$"
            item["topic"] = re.sub(pattern, "", topic).strip()
    return schedule


def make_day0_tutorial_entry() -> Dict[str, object]:
    """Return the shared Day 0 tutorial entry.

    The entry introduces learners to the daily course structure and is reused
    across the intermediate-level schedules.
    """

    return {
        "day": 0,
        "topic": "Tutorial – Course Overview",
        "chapter": "Tutorial",
        "goal": (
            "Welcome to Day 0! This orientation page introduces how our four-part "
            "course is organized and how you’ll navigate the overview, assignment, "
            "and submit tabs each day."
        ),
        "instruction": """1. Overview

Purpose: Recommends your learning path and the order to approach each day’s materials.

Course Structure: Each day is divided into four Teile (parts).

    Teil 1 – Group Practice (no assignment)
        • Read this section one chapter ahead to prepare for class discussions.
        • It includes a topic-of-the-day and tips to spark conversation.
        • Participation here is essential; unprepared students may find it difficult to contribute.
        • For extra practice, open Chat • Grammar • Exams. Copy or type the daily question into Chat • Grammar • Exams; the AI will offer tips so you arrive “three times prepared.”

    Teil 2 – Schreiben (Writing Assignment)
        • Use the Schreibentrainer tools to draft and refine your writing.
        • This segment is part of your daily assignment.

    Teil 3 – Lesen (Reading Assignment)
        • Contains seven comprehension questions.
        • This segment is also part of your assignment.

    Teil 4 – Hören (Listening Assignment)
        • Includes five listening questions.
        • This segment completes your assignment set.

2. Assignment

    Workbook: All assignment tasks (Teile 2–4) are housed here.

    Recorded Lecture & Grammar Notes: Each day offers a recorded lecture and grammar notebook.
        • The grammar section serves as your personal notes.
        • The workbook portion is the space where you complete Teile 2–4.

3. Submit

    Submission Steps:
        • Copy the completed answers from Teile 2, 3, and 4 in your workbook.
        • Paste them into the Submit tab.
        • Tick the two confirmation boxes.
        • Click “Submit.”

    Feedback:
        • Your results will be sent by email.
        • If you opt in to Telegram notifications, you’ll receive them automatically as well.

Summary
    • Teil 1: Prepare for group discussion (no submission).
    • Teil 2–4: Complete writing, reading, and listening assignments daily.
    • Stay Ahead: Always read Teil 1 one chapter in advance.
    • Be Prepared: Use Chat • Grammar • Exams to practice the question of the day.
    • Use Tools: Schreibentrainer for writing, recorded lectures for each topic, and grammar notes for quick reference.
    • Submit Work: Teile 2–4 only, via the Submit tab.

Good luck and viel Erfolg on your language journey!
""",
        "grammar_topic": None,
        "assignment": False,
        "lesen_hören": {
            "video": None,
            "youtube_link": None,
            "grammarbook_link": None,
            "workbook_link": None,
        },
    }


def full_lesson_title(lesson: dict) -> str:
    """Return the full lesson title for display.

    The format is ``"Day X: Topic (Chapter Y)"`` so callers can present a
    concise, duplication-free summary in the UI.
    """

    return (
        f"Day {lesson.get('day', '?')}: {lesson.get('topic', '')} "
        f"(Chapter {lesson.get('chapter', '')})"
    )

def get_a1_schedule():
    schedule = [
        # DAY 0
        {
            "day": 0,
            "topic": "Tutorial",
            "chapter": "Tutorial",
            "goal": "Start with a quick orientation so you're ready for Day 1.",
            "instruction": (
                "Walk through the core areas of your Course Book before the first lesson.\n\n"
                "**Overview tab** — Preview how each day is organised so you always know what's next.\n"
                "**Assignment tab** — Watch lectures and download resources you'll submit later.\n"
                "**Submit tab** — Practise uploading a file or saving a draft so handing in Day 1 feels easy.\n"
                "**Classroom tab** — Review announcements, mark attendance, and confirm you can join class."
            ),
            "grammar_topic": None,
            "assignment": False,
            "lesen_hören": {
                "video": None,
                "youtube_link": None,
                "grammarbook_link": None,
                "workbook_link": None,
            },
        },

        # DAY 1
        {
            "day": 1,
            "topic": "Lesen & Hören 0.1",
            "chapter": "0.1",
            "goal": "You will learn to greet others in German, and ask about people's well-being.",
            "instruction": "Watch the video, review grammar, do the workbook, submit assignment.",
            "grammar_topic": "Formal and Informal Greetings",
            "assignment": True,
            "lesen_hören": {
                "video": "https://youtu.be/NmaHd9xsGvw",
                "youtube_link": "https://youtu.be/NmaHd9xsGvw",
                "grammarbook_link": "https://drive.google.com/file/d/10UPl4n5FzukSDiTIlcM-WjmNuJGz9OgL/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/1wjtEyPphP0N7jLbF3AWb5wN_FuJZ5jUQ/view?usp=sharing"
            }
        },
        # DAY 2 – Multi chapter
        {
            "day": 2,
            "topic": "Lesen & Hören 0.2 and 1.1 ",
            "chapter": "0.2_1.1",
            "goal": "Understand the German alphabets, personal pronouns and verb conjugation in German.",
            "instruction": "You are doing Lesen and Hören chapter 0.2 and 1.1. Make sure to follow up attentively.",
            "grammar_topic": "German Alphabets and Personal Pronouns",
            "lesen_hören": [
                {
                    "chapter": "0.2",
                    "video": "https://youtu.be/S7n6TlAQRLQ",
                    "youtube_link": "https://youtu.be/S7n6TlAQRLQ",
                    "grammarbook_link": "https://drive.google.com/file/d/1KtJCF15Ng4cLU88wdUCX5iumOLY7ZA0a/view?usp=sharing",
                    "assignment": True,
                    "workbook_link": "https://drive.google.com/file/d/1R6PqzgsPm9f5iVn7JZXSNVa_NttoPU9Q/view?usp=sharing",
                },
                {
                    "chapter": "1.1",
                    "video": "https://youtu.be/AjsnO1hxDs4",
                    "youtube_link": "https://youtu.be/AjsnO1hxDs4",
                    "grammarbook_link": "https://drive.google.com/file/d/1DKhyi-43HX1TNs8fxA9bgRvhylubilBf/view?usp=sharing",
                    "assignment": True,
                    "workbook_link": "https://drive.google.com/file/d/1A1D1pAssnoncF1JY0v54XT2npPb6mQZv/view?usp=sharing",
                }
            ]
        },
        # DAY 3
        {
            "day": 3,
            "topic": "Schreiben & Sprechen 1.1 and Lesen & Hören 1.2",
            "chapter": "1.1_1.2",
            "goal": "Recap what we have learned so far: be able to introduce yourself in German and know all the pronouns.",
            "instruction": (
                "Begin with the practicals at **Schreiben & Sprechen** (writing & speaking). "
                "Then, move to **Lesen & Hören** (reading & listening). "
                "**Do assignments only at Lesen & Hören.**\n\n"
                "Schreiben & Sprechen activities are for self-practice and have answers provided for self-check. "
                "Main assignment to be marked is under Lesen & Hören below."
            ),
            "grammar_topic": "German Pronouns",
            "schreiben_sprechen": {
                "chapter": "1.1",
                "video": "https://youtu.be/hEe6rs0lkRg",
                "youtube_link": "https://youtu.be/hEe6rs0lkRg",
                "workbook_link": "https://drive.google.com/file/d/1GXWzy3cvbl_goP4-ymFuYDtX4X23D70j/view?usp=sharing",
                "assignment": False,
            },
            "lesen_hören": [
                {
                    "chapter": "1.2",
                    "video": "https://youtu.be/NVCN4fZXEk0",
                    "youtube_link": "https://youtu.be/NVCN4fZXEk0",
                    "grammarbook_link": "https://drive.google.com/file/d/1OUJT9aSU1XABi3cdZlstUvfBIndyEOwb/view?usp=sharing",
                    "workbook_link": "https://drive.google.com/file/d/1Lubevhd7zMlbvPcvHHC1D0GzW7xqa4Mp/view?usp=sharing",
                    "assignment": True
                }
            ]
        },
        # DAY 4
        {
            "day": 4,
            "topic": "Lesen & Hören 2",
            "chapter": "2",
            "goal": "Learn numbers from one to 10 thousand. Also know the difference between city and street",
            "instruction": "Watch the video, study the grammar, complete the workbook, and send your answers.",
            "grammar_topic": "German Numbers",
            "assignment": True,
            "lesen_hören": {
                "video": "https://youtu.be/BzI2n4A8Oak",
                "youtube_link": "https://youtu.be/QTB8eJIPo94",
                "grammarbook_link": "https://drive.google.com/file/d/12jHQvlNK-2JV0G6vY1UMho_UvzlcIrB8/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/1C4VZDUj7VT27Qrn9vS5MNc3QfRqpmDGE/view?usp=sharing",
                "assignment": True
            }
        },
        # DAY 5
        {
            "day": 5,
            "topic": "Schreiben & Sprechen 1.2 (Recap)",
            "chapter": "1.2",
            "goal": "Consolidate your understanding of introductions.",
            "instruction": "Use self-practice workbook and review answers for self-check.",
            "assignment": False,
            "schreiben_sprechen": {
                "video": "",
                "youtube_link": "",
                "workbook_link": "https://drive.google.com/file/d/1-fDUBzfJ4n-fukM9ROPx-dSC7g9gamEb/view?usp=sharing"
            }
        },
        # DAY 6
        {
            "day": 6,
            "topic": "Schreiben & Sprechen 2.3",
            "chapter": "2.3",
            "goal": "Learn about family and expressing your hobby",
            "assignment": False,
            "instruction": "Use self-practice workbook and review answers for self-check.",
            "schreiben_sprechen": {
                "video": "https://youtu.be/FCHYoAySK_s",
                "youtube_link": "https://youtu.be/FCHYoAySK_s",
                "workbook_link": "https://drive.google.com/file/d/1xellIzaxzoBTFOUdaCEHu_OiiuEnFeWT/view?usp=sharing"
            }
        },
        # DAY 7
        {
            "day": 7,
            "topic": "Lesen & Hören 3",
            "chapter": "3",
            "goal": "Know how to ask for a price and also the use of mogen and gern to express your hobby",
            "instruction": "Watch the video, study the grammar, complete the workbook, and send your answers.Do schreiben and sprechen 2.3 before this chapter for better understanding",
            "grammar_topic": "Fragen nach dem Preis; gern/lieber/mögen (Talking about price and preferences)",
            "assignment": True,
            "lesen_hören": {
                "video": "https://youtu.be/Ioq0_bNJ1bE",
                "youtube_link": "https://youtu.be/Ioq0_bNJ1bE",
                "grammarbook_link": "https://drive.google.com/file/d/1U7uNx3nhyAwOLXLNYZKZP2-Ie_LoL4hu/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/1W5GCdtp-NzSQWMz_ir7uQSKJc3F4LGPb/view?usp=sharing"
            }
        },
        # DAY 8
        {
            "day": 8,
            "topic": "Lesen & Hören 4",
            "chapter": "4",
            "goal": "Learn about schon mal and noch nie, irregular verbs and all the personal pronouns",
            "instruction": "Watch the video, study the grammar, complete the workbook, and send your answers.",
            "grammar_topic": "schon mal, noch nie; irregular verbs; personal pronouns",
            "assignment": True,
            "lesen_hören": {
                "video": "https://youtu.be/0HjCQKxMl5Q",
                "youtube_link": "https://youtu.be/0HjCQKxMl5Q",
                "grammarbook_link": "https://drive.google.com/file/d/1obsYT3dP3qT-i06SjXmqRzCT2pNoJJZp/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/1woXksV9sTZ_8huXa8yf6QUQ8aUXPxVug/view?usp=sharing"
            }
        },
        # DAY 9
        {
            "day": 9,
            "topic": "Lesen & Hören 5",
            "chapter": "5",
            "goal": "Learn about the German articles and cases",
            "instruction": "Watch the video, study the grammar, complete the workbook, and send your answers.",
            "grammar_topic": "Nominative & Akkusative, Definite & Indefinite Articles",
            "assignment": True,
            "lesen_hören": {
                "video": "https://youtu.be/Yi5ZA-XD-GY?si=nCX_pceEYgAL-FU0",
                "youtube_link": "https://youtu.be/Yi5ZA-XD-GY?si=nCX_pceEYgAL-FU0",
                "grammarbook_link": "https://drive.google.com/file/d/17y5fGW8nAbfeVgolV7tEW4BLiLXZDoO6/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/1zjAqvQqNb7iKknuhJ79bUclimEaTg-mt/view?usp=sharing"
            }
        },
        # DAY 10
        {
            "day": 10,
            "topic": "Lesen & Hören 6 and Schreiben & Sprechen 2.4",
            "chapter": "6",
            "goal": "Understand Possessive Determiners and its usage in connection with nouns",
            "instruction": "The assignment is the lesen and horen chapter 6 but you must also go through schreiben and sprechnen 2.4 for full understanding",
            "lesen_hören": {
                "chapter": "6",
                "video": "https://youtu.be/SXwDqcwrR3k",
                "youtube_link": "https://youtu.be/SXwDqcwrR3k",
                "grammarbook_link": "https://drive.google.com/file/d/1Fy4bKhaHHb4ahS2xIumrLtuqdQ0YAFB4/view?usp=sharing",
                "assignment": True,
                "workbook_link": "https://drive.google.com/file/d/1Da1iw54oAqoaY-UIw6oyIn8tsDmIi1YR/view?usp=sharing"
            },
            "schreiben_sprechen": {
                "chapter": "2.4",
                "video": "https://youtu.be/lw9SsojpKf8",
                "youtube_link": "https://youtu.be/lw9SsojpKf8",
                "workbook_link": "https://drive.google.com/file/d/1GbIc44ToWh2upnHv6eX3ZjFrvnf4fcEM/view?usp=sharing",
                "assignment": False,
            }
        },
        # DAY 11
        {
            "day": 11,
            "topic": "Lesen & Hören 7",
            "chapter": "7",
            "goal": "Understand the 12 hour clock system",
            "instruction": "Watch the video, study the grammar, complete the workbook, and send your answers.",
            "assignment": True,
            "lesen_hören": {
                "video": "https://youtu.be/uyvXoCoqjiE",
                "youtube_link": "https://youtu.be/uyvXoCoqjiE",
                "grammarbook_link": "https://drive.google.com/file/d/1pSaloRhfh8eTKK_r9mzwp6xkbfdkCVox/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/1QyDdRae_1qv_umRb15dCJZTPdXi7zPWd/view?usp=sharing"
            }
        },
        # DAY 12
        {
            "day": 12,
            "topic": "Lesen & Hören 8",
            "chapter": "8",
            "goal": "Understand the 24 hour clock and date system in German",
            "instruction": "Watch the video, study the grammar, complete the workbook, and send your answers.",
            "assignment": True,
            "lesen_hören": {
                "video": "https://youtu.be/hLpPFOthVkU",
                "youtube_link": "https://youtu.be/hLpPFOthVkU",
                "grammarbook_link": "https://drive.google.com/file/d/1fW2ChjnDKW_5SEr65ZgE1ylJy1To46_p/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/1onzokN8kQualNO6MSsPndFXiRwsnsVM9/view?usp=sharing"
            }
        },
        # DAY 13
        {
            "day": 13,
            "topic": "Schreiben & Sprechen 3.5",
            "chapter": "3.5",
            "goal": "Recap from the lesen and horen. Understand numbers, time, asking of price and how to formulate statements in German",
            "instruction": "Use the statement rule to talk about your weekly routine using the activities listed. Share with your tutor when done",
            "schreiben_sprechen": {
                "video": "https://youtu.be/PwDLGmfBUDw",
                "youtube_link": "https://youtu.be/PwDLGmfBUDw",
                "assignment": False,
                "workbook_link": "https://drive.google.com/file/d/12oFKrKrHBwSpSnzxLX_e-cjPSiYtCFVs/view?usp=sharing"
            }
        },
        # DAY 14
        {
            "day": 14,
            "topic": "Schreiben & Sprechen 3.6",
            "chapter": "3.6",
            "goal": "Understand how to use modal verbs with main verbs and separable verbs",
            "assignment": False,
            "instruction": "This is a practical exercise. All the answers are included in the document except for the last paragraph. You can send a screenshot of that to your tutor",
            "grammar_topic": "Modal Verbs",
            "schreiben_sprechen": {
                "video": "https://youtu.be/G08nQJh1Trc",
                "youtube_link": "https://youtu.be/G08nQJh1Trc",
                "workbook_link": "https://drive.google.com/file/d/1oOT_b3S4MZIqZ10Kui-dR6qlM0AZfWZ4/view?usp=sharing"
            }
        },
        # DAY 15
        {
            "day": 15,
            "topic": "Schreiben & Sprechen 4.7",
            "chapter": "4.7",
            "assignment": False,
            "goal": "Understand imperative statements and learn how to use them in your Sprechen exams, especially in Teil 3.",
            "instruction": "After completing this chapter, open Chat • Grammar • Exams, pick A1 as your level, and ask for Teil 3-style prompts to practice.",
            "grammar_topic": "Imperative",
            "schreiben_sprechen": {
                "video": "https://youtu.be/IVtUc9T3o0Y",
                "youtube_link": "https://youtu.be/IVtUc9T3o0Y",
                "workbook_link": "https://drive.google.com/file/d/1953B01hB9Ex7LXXU0qIaGU8xgCDjpSm4/view?usp=sharing"
            }
        },
        # DAY 16
        {
            "day": 16,
            "topic": "Lesen & Hören 9 and 10",
            "chapter": "9_10",
            "goal": "Understand how to negate statements using nicht,kein and nein",
            "instruction": "This chapter has two assignments. Do the assignments for chapter 9 and after chapter 10. Chapter 10 has no grammar",
            "grammar_topic": "Negation",
            "lesen_hören": [
                {
                    "chapter": "9",
                    "video": "https://youtu.be/MrB3BPtQN6A",
                    "youtube_link": "https://youtu.be/MrB3BPtQN6A",
                    "assignment": True,
                    "grammarbook_link": "https://drive.google.com/file/d/1g-qLEH1ZDnFZCT83TW-MPLxNt2nO7UAv/view?usp=sharing",
                    "workbook_link": "https://drive.google.com/file/d/1hKtQdXg5y3yJyFBQsCMr7fZ11cYbuG7D/view?usp=sharing"
                },
                {
                    "chapter": "10",
                    "video": "",
                    "youtube_link": "",
                    "grammarbook_link": "",
                    "assignment": True,
                    "workbook_link": "https://drive.google.com/file/d/1rJXshXQSS5Or4ipv1VmUMsoB0V1Vx4VK/view?usp=sharing"
                }
            ]
        },
        # DAY 17
        {
            "day": 17,
            "topic": "Lesen & Hören 11",
            "chapter": "11",
            "goal": "Understand instructions and request in German using the Imperative rule",
            "grammar_topic": "Direction",
            "instruction": "",
            "lesen_hören": {
                "video": "https://youtu.be/k2ZC3rXPe1k",
                "youtube_link": "https://youtu.be/k2ZC3rXPe1k",
                "assignment": True,
                "grammarbook_link": "https://drive.google.com/file/d/1lMzZrM4aAItO8bBmehODvT6gG7dz8I9s/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/17FNSfHBxyga9sKxzicT_qkP7PA4vB5-A/view?usp=sharing"
            }
        },
        # DAY 18
        {
            "day": 18,
            "topic": "Lesen & Hören 12.1 and 12.2",
            "chapter": "12.1_12.2",
            "goal": "Learn about German professions and how to use two-way prepositions",
            "instruction": "Do assignments for 12.1 and 12.2 and use the schreiben and sprechen below for practicals for full understanding",
            "grammar_topic": "Two Case Preposition",
            "lesen_hören": [
                {
                    "chapter": "12.1",
                    "video": "https://youtu.be/-vTEvx9a8Ts",
                    "youtube_link": "https://youtu.be/-vTEvx9a8Ts",
                    "assignment": True,
                    "grammarbook_link": "https://drive.google.com/file/d/1wdWYVxBhu4QtRoETDpDww-LjjzsGDYva/view?usp=sharing",
                    "workbook_link": "https://drive.google.com/file/d/1A0NkFl1AG68jHeqSytI3ygJ0k7H74AEX/view?usp=sharing"
                },
                {
                    "chapter": "12.2",
                    "video": "",
                    "youtube_link": "",
                    "assignment": True,
                    "grammarbook_link": "",
                    "workbook_link": "https://drive.google.com/file/d/1xojH7Tgb5LeJj3nzNSATUVppWnJgJLEF/view?usp=sharing"
                }
            ],
            "schreiben_sprechen": {
                "chapter": "12.2",
                "video": "https://youtu.be/xVyYo7upDGo",
                "youtube_link": "https://youtu.be/xVyYo7upDGo",
                "assignment": False,
                "workbook_link": "https://drive.google.com/file/d/1iyYBuxu3bBEovxz0j9QeSu_1URX92fvN/view?usp=sharing"
            }
        },
        # DAY 19
        {
            "day": 19,
            "topic": "Schreiben & Sprechen 5.9",
            "chapter": "5.9",
            "goal": "Understand the difference between Erlaubt and Verboten and how to use it in the exams hall",
            "instruction": "Review the workbook and do the practicals in it. Answers are attached",
            "grammar_topic": "Erlaubt and Verboten",
            "schreiben_sprechen": {
                "video": "",
                "youtube_link": "",
                "assignment": False,
                "workbook_link": "https://drive.google.com/file/d/1CkoYa_qeqsGju0kTS6ElurCAlEW6pVFL/view?usp=sharing"
            }
        },
        # DAY 20
        {
            "day": 20,
            "topic": "Introduction to Letter Writing 12.3 ",
            "chapter": "12.3",
            "goal": "Practice how to write both formal and informal letters",
            "assignment": True,
            "instruction": "Write all the two letters in this document and send to your tutor for corrections",
            "grammar_topic": "Formal and Informal Letter",
            "schreiben_sprechen": {
                "video": "https://youtu.be/n9Y0kt_XRZY",
                "youtube_link": "https://youtu.be/n9Y0kt_XRZY",
                "workbook_link": "https://drive.google.com/file/d/1SjaDH1bYR7O-BnIbM2N82XOEjeLCfPFb/view?usp=sharing"
            }
        },
        # DAY 21
        {
            "day": 21,
            "topic": "Lesen & Hören 13",
            "chapter": "13",
            "assignment": True,
            "goal": "",
            "instruction": "Watch the video, study the grammar, complete the workbook, and send your answers.",
            "grammar_topic": "Weather and Past Tense. How to form Perfekt statement in German",
            "lesen_hören": {
                "video": "https://youtu.be/oz1asSrG8d0",
                "youtube_link": "https://youtu.be/oz1asSrG8d0",
                "assignment": True,
                "grammarbook_link": "https://drive.google.com/file/d/1PCXsTIg9iNlaAUkwH8BYekw_3v1HJjGq/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/1GZeUi5p6ayDGnPcebFVFfaNavmoWyoVM/view?usp=sharing"
            }
        },
        # DAY 22
        {
            "day": 22,
            "topic": "Lesen & Hören 14.1",
            "chapter": "14.1",
            "goal": "Understand health and talking about body parts in German",
            "instruction": "Watch the video, study the grammar, complete the workbook, and send your answers.",
            "grammar_topic": "Health and Body Parts",
            "lesen_hören": {
                "video": "https://youtu.be/Zx_TFF9FNGo",
                "youtube_link": "https://youtu.be/Zx_TFF9FNGo",
                "assignment": True,
                "grammarbook_link": "https://drive.google.com/file/d/1QoG4mNxA1w8AeTMPfLtMQ_rAHrmC1DdO/view?usp=sharing",
                "workbook_link": "https://drive.google.com/file/d/1LkDUU7r78E_pzeFnHKw9vfD9QgUAAacu/view?usp=sharing"
            }
        },
        # DAY 23
        {
            "day": 23,
            "topic": "Lesen & Hören 14.2",
            "chapter": "14.2",
            "goal": "Understand adjective declension and dative verbs",
            "instruction": " This chapter has no assignment. Only grammar",
            "grammar_topic": "Adjective Declension and Dative Verbs",
            "lesen_hören": {
                "video": "https://youtu.be/sAd8rWu9O0Q",
                "youtube_link": "https://youtu.be/sAd8rWu9O0Q",
                "assignment": False,
                "grammarbook_link": "https://drive.google.com/file/d/16h-yS0gkB2_FL1zxCC4MaqRBbKne7GI1/view?usp=sharing",
                "workbook_link": ""
            }
        },
        # DAY 24
        {
            "day": 24,
            "topic": "Schreiben & Sprechen 5.10",
            "chapter": "5.10",
            "goal": "Learn about conjunctions and how to apply them in your exams",
            "instruction": "This chapter has no assignments. It gives you ideas to progress for A2 and how to use conjunctions",
            "grammar_topic": "German Conjunctions",
            "assignment": False,
            "schreiben_sprechen": {
                "video": "https://youtu.be/WVq9x69dCeE",
                "youtube_link": "https://youtu.be/WVq9x69dCeE",
                "workbook_link": "https://drive.google.com/file/d/1LE1b9ilkLLobE5Uw0TVLG0RIVpLK5k1t/view?usp=sharing"
            }
        },
        # DAY 25 - CONGRATULATIONS
        {
            "day": 25,
            "topic": "Course Completed!",
            "chapter": None,
            "goal": "🎯 Goal: Celebrate your achievement and plan your next steps.",
            "instruction": """📝 Instruction: Congratulations on finishing your A1 course. 
You worked hard and made great progress. The school will confirm your results and send your completion certificate to your email. 

Kindly communicate with us what you would like to do next by emailing **learngermanghana@gmail.com**. 
You can prepare for the A1 exams or progress to A2. We wish you continued success in your journey. 

Use:
- **Chat • Grammar • Exams** for guided speaking practice and pronunciation feedback.
- **Vocabulary Trainer**  
- **Schreiben Trainer** (includes pre-filled questions on typical exam topics)  

ℹ️ Note: You’ll keep access to your tutor until your contract officially ends.  
🎉 If you enjoyed the course, please [leave us a positive review on Google](https://g.page/r/Cdogveq3Hy69EBE/review).  
            """,
            "grammar_topic": None,
            "assignment": False,
            "lesen_hören": {
                "video": None,
                "youtube_link": None,
                "grammarbook_link": None,
                "workbook_link": None
            }
        }
    ]
    return _strip_topic_chapter(schedule)


def get_a2_schedule():
    schedule = [
        # DAY 0 - TUTORIAL
        make_day0_tutorial_entry(),

        # DAY 1
        {
            "day": 1,
            "topic": "Small Talk 1.1 (Exercise)",
            "chapter": "1.1",
            "goal": "Practice basic greetings and small talk.",
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "assignment": True,
            "video": "https://youtu.be/siF0jWZdIwk",
            "youtube_link": "https://youtu.be/siF0jWZdIwk",
            "grammarbook_link": "https://drive.google.com/file/d/1NsCKO4K7MWI-queLWCeBuclmaqPN04YQ/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1LXDI1yyJ4aT4LhX5eGDbKnkCkJZ2EE2T/view?usp=sharing"
        },
        # DAY 2
        {
            "day": 2,
            "topic": "Personen Beschreiben 1.2 (Exercise)",
            "chapter": "1.2",
            "goal": "Describe people and their appearance.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Subordinate Clauses (Nebensätze) with dass and weil",
            "video": "https://youtu.be/FYaXSvZsEDM?si=0e_sHxslHQL7FGDk",
            "youtube_link": "https://youtu.be/FYaXSvZsEDM?si=0e_sHxslHQL7FGDk",
            "grammarbook_link": "https://drive.google.com/file/d/1xMpEAPD8C0HtIFsmgqYO-wZaKDrQtiYp/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/128lWaKgCZ2V-3tActM-dwNy6igLLlzH3/view?usp=sharing"
        },
        # DAY 3
        {
            "day": 3,
            "topic": "Dinge und Personen vergleichen 1.3",
            "chapter": "1.3",
            "goal": "Learn to compare things and people.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Positive, Comparative, and Superlative in German",
            "video": "https://youtu.be/oo3pUo5OSDE",
            "youtube_link": "https://youtu.be/oo3pUo5OSDE",
            "grammarbook_link": "https://drive.google.com/file/d/1Z3sSDCxPQz27TDSpN9r8lQUpHhBVfhYZ/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/18YXe9mxyyKTars1gL5cgFsXrbM25kiN8/view?usp=sharing"
        },
        # DAY 4
        {
            "day": 4,
            "topic": "Wo möchten wir uns treffen? 2.4",
            "chapter": "2.4",
            "goal": "Arrange and discuss meeting places.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Nominalization of Verbs",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/14qE_XJr3mTNr6PF5aa0aCqauh9ngYTJ8/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1RaXTZQ9jHaJYwKrP728zevDSQHFKeR0E/view?usp=sharing"
        },
        # DAY 5
        {
            "day": 5,
            "topic": "Was machst du in deiner Freizeit? 2.5 ",
            "chapter": "2.5",
            "goal": "Talk about free time activities.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Dative Preposition",
            "video": "https://youtu.be/8dX40NXG_gI",
            "youtube_link": "https://youtu.be/8dX40NXG_gI",
            "grammarbook_link": "https://drive.google.com/file/d/11yEcMioSB9x1ZD-x5_67ApFzP53iau-N/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1dIsFg7wNaqyyOHm95h7xv4Ssll5Fm0V1/view?usp=sharing"
        },
        # DAY 6
        {
            "day": 6,
            "topic": "Möbel und Räume kennenlernen 3.6",
            "chapter": "3.6",
            "goal": "Identify furniture and rooms.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Two Case Preposition",
            "video": "https://youtu.be/am3WqQaCibE",
            "youtube_link": "https://youtu.be/am3WqQaCibE",
            "grammarbook_link": "https://drive.google.com/file/d/1MSahBEyElIiLnitWoJb5xkvRlB21yo0y/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/16UfBIrL0jxCqWtqqZaLhKWflosNQkwF4/view?usp=sharing"
        },
        # DAY 7
        {
            "day": 7,
            "topic": "Eine Wohnung suchen (Übung) 3.7",
            "chapter": "3.7",
            "goal": "Practice searching for an apartment.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Identifying German Nouns and their Gender",
            "video": "https://youtu.be/ScU6w8VQgNg", 
            "youtube_link": "https://youtu.be/ScU6w8VQgNg",
            "grammarbook_link": "https://drive.google.com/file/d/1clWbDAvLlXpgWx7pKc71Oq3H2p0_GZnV/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1EF87TdHa6Y-qgLFUx8S6GAom9g5EBQNP/view?usp=sharing"
        },
        # DAY 8
        {
            "day": 8,
            "topic": "Rezepte und Essen (Exercise) 3.8",
            "chapter": "3.8",
            "assignment": True,
            "goal": "Learn about recipes and food. Practice using sequence words like zuerst', 'nachdem', and 'außerdem' to organize your letter.",
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Zuerst, Nachdem, and Talking About Sequence in German",
            "video": "https://youtu.be/_xQMNp3qcDQ",
            "youtube_link": "https://youtu.be/_xQMNp3qcDQ",
            "grammarbook_link": "https://drive.google.com/file/d/16lh8sPl_IDZ3dLwYNvL73PqOFCixidrI/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1c8JJyVlKYI2mz6xLZZ6RkRHLnH3Dtv0c/view?usp=sharing"
        },
        # DAY 9
        {
            "day": 9,
            "topic": "Urlaub 4.9",
            "chapter": "4.9",
            "goal": "Discuss vacation plans.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Understanding Präteritum and Perfekt",
            "video": "https://youtu.be/NxoQH-BY9Js",
            "youtube_link": "https://youtu.be/NxoQH-BY9Js",
            "grammarbook_link": "https://drive.google.com/file/d/1kOb7c08Pkxf21OQE_xIGEaif7Xq7k-ty/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1NzRxbGUe306Vq0mq9kKsc3y3HYqkMhuA/view?usp=sharing"
        },
        # DAY 10
        {
            "day": 10,
            "topic": "Tourismus und Traditionelle Feste 4.10",
            "chapter": "4.10",
            "assignment": True,
            "goal": "Learn about tourism and festivals.",
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Präteritum",
            "video": "https://youtu.be/XFxV3GSSm8E",
            "youtube_link": "https://youtu.be/XFxV3GSSm8E",
            "grammarbook_link": "https://drive.google.com/file/d/1snFsDYBK8RrPRq2n3PtWvcIctSph-zvN/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1vijZn-ryhT46cTzGmetuF0c4zys0yGlB/view?usp=sharing"
        },
        # DAY 11
        {
            "day": 11,
            "topic": "Unterwegs: Verkehrsmittel vergleichen 4.11",
            "chapter": "4.11",
            "assignment": True,
            "goal": "Compare means of transportation.",
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Prepositions in and naxh",
            "video": "https://youtu.be/RkvfRiPCZI4",
            "youtube_link": "https://youtu.be/RkvfRiPCZI4",
            "grammarbook_link": "https://drive.google.com/file/d/19I7oOHX8r4daxXmx38mNMaZO10AXHEFu/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1c7ITea0iVbCaPO0piark9RnqJgZS-DOi/view?usp=sharing"
        },
        # DAY 12
        {
            "day": 12,
            "topic": "Mein Traumberuf (Übung) 5.12",
            "chapter": "5.12",
            "assignment": True,
            "goal": "Learn how to talk about a dream job and future goals.",
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Konjunktiv II",
            "video": "https://youtu.be/w81bsmssGXQ",
            "youtube_link": "https://youtu.be/w81bsmssGXQ",
            "grammarbook_link": "https://drive.google.com/file/d/1dyGB5q92EePy8q60eWWYA91LXnsWQFb1/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/18u6FnHpd2nAh1Ev_2mVk5aV3GdVC6Add/view?usp=sharing"
        },
        # DAY 13
        {
            "day": 13,
            "topic": "Ein Vorstellungsgespräch (Exercise) 5.13",
            "chapter": "5.13",
            "assignment": True,
            "goal": "Prepare for a job interview.",
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Konjunktive II with modal verbs",
            "video": "https://youtu.be/urKBrX5VAYU",
            "youtube_link": "https://youtu.be/urKBrX5VAYU",
            "grammarbook_link": "https://drive.google.com/file/d/1tv2tYzn9mIG57hwWr_ilxV1My7kt-RKQ/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1sW2yKZptnYWPhS7ciYdi0hN5HV-ycsF0/view?usp=sharing"
        },
        # DAY 14
        {
            "day": 14,
            "topic": "Beruf und Karriere (Exercise) 5.14",
            "chapter": "5.14",
            "assignment": True,
            "goal": "Discuss jobs and careers.",
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Modal Verbs",
            "video": "https://youtu.be/IyBvx-yVT-0",
            "youtube_link": "https://youtu.be/IyBvx-yVT-0",
            "grammarbook_link": "https://drive.google.com/file/d/13mVpVGfhY1NQn-BEb7xYUivnaZbhXJsK/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1rlZoo49bYBRjt7mu3Ydktzgfdq4IyK2q/view?usp=sharing"
        },
        # DAY 15
        {
            "day": 15,
            "topic": "Mein Lieblingssport 6.15",
            "chapter": "6.15",
            "assignment": True,
            "goal": "Talk about your favorite sport.",
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Reflexive Pronouns",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1dGZjcHhdN1xAdK2APL54RykGH7_msUyr/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1iiExhUj66r5p0SJZfV7PsmCWOyaF360s/view?usp=sharing"
        },
        # DAY 16
        {
            "day": 16,
            "topic": "Wohlbefinden und Entspannung 6.16",
            "chapter": "6.16",
            "goal": "Express well-being and relaxation.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Verbs and Adjectives with Prepositions",
            "video": "https://youtu.be/r4se8KuS8cA",
            "youtube_link": "https://youtu.be/r4se8KuS8cA",
            "grammarbook_link": "https://drive.google.com/file/d/1BiAyDazBR3lTplP7D2yjaYmEm2btUT1D/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1G_sRFKG9Qt5nc0Zyfnax-0WXSMmbWB70/view?usp=sharing"
        },
        # DAY 17
        {
            "day": 17,
            "topic": "In die Apotheke gehen 6.17",
            "chapter": "6.17",
            "goal": "Learn phrases for the pharmacy.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Notes on German Indefinite Pronouns",
            "video": "https://youtu.be/Xjp2A1hU1ag",
            "youtube_link": "https://youtu.be/Xjp2A1hU1ag",
            "grammarbook_link": "https://drive.google.com/file/d/1O040UoSuBdy4llTK7MbGIsib63uNNcrV/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1vsdVR_ubbu5gbXnm70vZS5xGFivjBYoA/view?usp=sharing"
        },
        # DAY 18
        {
            "day": 18,
            "topic": "Die Bank anrufen 7.18",
            "chapter": "7.18",
            "goal": "Practice calling the bank.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "grammar_topic": "Notes on Opening a Bank Account in Germany",
            "video": "https://youtu.be/ahIUVAbsuxU",
            "youtube_link": "https://youtu.be/ahIUVAbsuxU",
            "grammarbook_link": "https://drive.google.com/file/d/1qNHtY8MYOXjtBxf6wHi6T_P_X1DGFtPm/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1GD7cCPU8ZFykcwsFQZuQMi2fiNrvrCPg/view?usp=sharing"
        },
        # DAY 19
        {
            "day": 19,
            "topic": "Einkaufen? Wo und wie? (Exercise) 7.19",
            "chapter": "7.19",
            "goal": "Shop and ask about locations.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "https://youtu.be/TOTK1yohCTg",
            "youtube_link": "https://youtu.be/TOTK1yohCTg",
            "grammarbook_link": "https://drive.google.com/file/d/1Qt9oxn-74t8dFdsk-NjSc0G5OT7MQ-qq/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1CEFn14eYeomtf6CpZJhyW00CA2f_6VRc/view?usp=sharing"
        },
        # DAY 20
        {
            "day": 20,
            "topic": "Typische Reklamationssituationen üben 7.20",
            "chapter": "7.20",
            "goal": "Handle typical complaints.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "https://youtu.be/utAO9hvGF18",
            "youtube_link": "https://youtu.be/utAO9hvGF18",
            "grammarbook_link": "https://drive.google.com/file/d/1-72wZuNJE4Y92Luy0h5ygWooDnBd9PQW/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1_GTumT1II0E1PRoh6hMDwWsTPEInGeed/view?usp=sharing"
        },
        # DAY 21
        {
            "day": 21,
            "topic": "Ein Wochenende planen 8.21",
            "chapter": "8.21",
            "goal": "Plan a weekend.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1FcCg7orEizna4rAkX3_FCyd3lh_Bb3IT/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1mMtZza34QoJO_lfUiEX3kwTa-vsTN_RK/view?usp=sharing"
        },
        # DAY 22
        {
            "day": 22,
            "topic": "Die Woche Planung 8.22",
            "chapter": "8.22",
            "goal": "Make a weekly plan.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "https://youtu.be/rBuEEFfee1c?si=YJpKuM0St2gWN67H",
            "youtube_link": "https://youtu.be/rBuEEFfee1c?si=YJpKuM0St2gWN67H",
            "grammarbook_link": "https://drive.google.com/file/d/1AvLYxZKq1Ae6_4ACJ20il1LqCOv2jQbb/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1mg_2ytNAYF00_j-TFQelajAxgQpmgrhW/view?usp=sharing"
        },
        # DAY 23
        {
            "day": 23,
            "topic": "Wie kommst du zur Schule / zur Arbeit? 9.23",
            "chapter": "9.23",
            "goal": "Talk about your route to school or work.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "https://youtu.be/c4TpUe3teBE",
            "youtube_link": "https://youtu.be/c4TpUe3teBE",
            "grammarbook_link": "https://drive.google.com/file/d/1XbWKmc5P7ZAR-OqFce744xqCe7PQguXo/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1Ialg19GIE_KKHiLBDMm1aHbrzfNdb7L_/view?usp=sharing"
        },
        # DAY 24
        {
            "day": 24,
            "topic": "Einen Urlaub planen 9.24",
            "chapter": "9.24",
            "goal": "Plan a vacation.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1tFXs-DNKvt97Q4dsyXsYvKVQvT5Qqt0y/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1t3xqddDJp3-1XeJ6SesnsYsTO5xSm9vG/view?usp=sharing"
        },
        # DAY 25
        {
            "day": 25,
            "topic": "Tagesablauf (Exercise) 9.25",
            "chapter": "9.25",
            "goal": "Describe a daily routine.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "",
            "youtube_link": "",
            "workbook_link": "https://drive.google.com/file/d/1jfWDzGfXrzhfGZ1bQe1u5MXVQkR5Et43/view?usp=sharing"
        },
        # DAY 26
        {
            "day": 26,
            "topic": "Gefühle in verschiedenen Situationen beschreiben 10.26",
            "chapter": "10.26",
            "goal": "Express feelings in various situations.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "",
            "youtube_link": "",
            "workbook_link": "https://drive.google.com/file/d/126MQiti-lpcovP1TdyUKQAK6KjqBaoTx/view?usp=sharing"
        },
        # DAY 27
        {
            "day": 27,
            "topic": "Digitale Kommunikation 10.27",
            "chapter": "10.27",
            "goal": "Talk about digital communication.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "",
            "youtube_link": "",
            "workbook_link": "https://drive.google.com/file/d/1UdBu6O2AMQ2g6Ot_abTsFwLvT87LHHwY/view?usp=sharing"
        },
        # DAY 28
        {
            "day": 28,
            "topic": "Über die Zukunft sprechen 10.28",
            "chapter": "10.28",
            "goal": "Discuss the future.",
            "assignment": True,
            "instruction": "Watch the video, review grammar, and complete your workbook.",
            "video": "",
            "youtube_link": "",
            "workbook_link": "https://drive.google.com/file/d/1164aJFtkZM1AMb87s1-K59wuobD7q34U/view?usp=sharing"
        },

        # DAY 29 - CONGRATULATIONS
        {
            "day": 29,
            "topic": "Course Completed!",
            "chapter": None,
            "goal": "🎯 Goal: Celebrate your achievement and plan your next steps.",
            "instruction": """📝 Instruction: Congratulations on finishing your A2 course. 
You worked hard and made excellent progress. The school will confirm your results and send your completion certificate to your email. 

Kindly communicate with us what you would like to do next by emailing **learngermanghana@gmail.com**. 
You can prepare for the A2 exams or progress to B1. We wish you continued success in your journey. 

Use:
- **Chat • Grammar • Exams** for guided speaking practice and pronunciation feedback.  
- **Vocabulary Trainer**  
- **Schreiben Trainer** (includes pre-filled questions on typical exam topics)  

ℹ️ Note: You’ll keep access to your tutor until your contract officially ends.  
🎉 If you enjoyed the course, please [leave us a positive review on Google](https://g.page/r/Cdogveq3Hy69EBE/review).  
            """,
            "grammar_topic": None,
            "assignment": False,
            "lesen_hören": {
                "video": None,
                "youtube_link": None,
                "grammarbook_link": None,
                "workbook_link": None
            }
        },
    ]
    return _strip_topic_chapter(schedule)


def get_b1_schedule():
    schedule = [
        # DAY 0 - TUTORIAL
        make_day0_tutorial_entry(),

        # DAY 1
        {
            "day": 1,
            "topic": "Traumwelten (Übung) 1.1",
            "chapter": "1.1",
            "goal": "Über Traumwelten und Fantasie sprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Präsens & Perfekt",
            "video": "https://youtu.be/wMrdW2DhD5o",
            "youtube_link": "https://youtu.be/wMrdW2DhD5o",
            "grammarbook_link": "https://drive.google.com/file/d/17dO2pWXKQ3V3kWZIgLHXpLJ-ozKHKxu5/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1gTcOHHGW2bXKkhxAC38jdl6OikgHCT9g/view?usp=sharing"
        },
        # TAG 2
        {
            "day": 2,
            "topic": "Freunde fürs Leben (Übung) 1.2",
            "chapter": "1.2",
            "goal": "Freundschaften und wichtige Eigenschaften beschreiben.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Präteritum – Vergangene Erlebnisse erzählen",
            "video": "https://youtu.be/piJE4ucYFuc",
            "youtube_link": "https://youtu.be/piJE4ucYFuc",
            "grammarbook_link": "https://drive.google.com/file/d/1St8MpH616FiJmJjTYI9b6hEpNCQd5V0T/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1AgjhFYw07JYvsgVP1MBKYEMFBjeAwQ1e/view?usp=sharing"
        },
        # TAG 3
        {
            "day": 3,
            "topic": "Erfolgsgeschichten (Übung) 1.3",
            "chapter": "1.3",
            "goal": "Über Erfolge und persönliche Erlebnisse berichten.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Adjektivdeklination mit unbestimmten Artikeln",
            "video": "https://youtu.be/8k0Iaw_-o8c",
            "youtube_link": "https://youtu.be/8k0Iaw_-o8c",
            "grammarbook_link": "https://drive.google.com/file/d/1kUtriLOZfJXUxj2IVU2VHZZkghIWDWKv/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1qVANqTLg4FOU40_WfLZyVTu5KBluzYrh/view?usp=sharing"
        },
        # TAG 4
        {
            "day": 4,
            "topic": "Wohnung suchen (Übung) 2.4",
            "chapter": "2.4",
            "goal": "Über Wohnungssuche und Wohnformen sprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Wechselpräpositionen",
            "video": "https://youtu.be/kR8SmSY99c8",
            "youtube_link": "https://youtu.be/kR8SmSY99c8",
            "grammarbook_link": "https://drive.google.com/file/d/1NW5F0R5zj6nn2SqDjhpQlkGcfK-UBUqk/view?usp=drive_link",
            "workbook_link": "https://drive.google.com/file/d/12r_HE51QtpknXSSU0R75ur-EDFpTjzXU/view?usp=sharing"
        },
        # TAG 5
        {
            "day": 5,
            "topic": "Der Besichtigungstermin (Übung) 2.5",
            "chapter": "2.5",
            "goal": "Einen Besichtigungstermin beschreiben.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Modalverben, Konjunktiv II",
            "video": "https://youtu.be/2lUPAnzx4e4",
            "youtube_link": "https://youtu.be/2lUPAnzx4e4",
            "grammarbook_link": "https://drive.google.com/file/d/13SI6AiqC2BAWLZjPh-AsiyTEfvGyk8DR/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1-HaOiGQtP_JI7ujg4-h-u1GnCumabdx_/view?usp=sharing"
        },
        # TAG 6
        {
            "day": 6,
            "topic": "Leben in der Stadt oder auf dem Land? 2.6",
            "chapter": "2.6",
            "goal": "Stadtleben und Landleben vergleichen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Relativsätze",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1qUPAIGiwKNm4O9Z1VsFPprVVoNOZzCbF/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1xAUFfq2knYxfoGMTlXO_MA8F_RK5_i8o/view?usp=sharing"
        },
        # TAG 7
        {
            "day": 7,
            "topic": "Fast Food vs. Hausmannskost 3.7",
            "chapter": "3.7",
            "goal": "Fast Food und Hausmannskost vergleichen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Der Genitiv",
            "video": "https://youtu.be/y5wqJv8_GMI",
            "youtube_link": "https://youtu.be/y5wqJv8_GMI",
            "grammarbook_link": "https://drive.google.com/file/d/1DMyTdt1cxhDxYJZQPHe3pAqE30TNwThU/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1XXVhFMJdFI_j3pZXw3UkuHCoKqYR8dkj/view?usp=sharing"
        },
        # TAG 8
        {
            "day": 8,
            "topic": "Alles für die Gesundheit 3.8",
            "chapter": "3.8",
            "goal": "Tipps für Gesundheit geben und Arztbesuche besprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Moadalverben",
            "video": "https://youtu.be/_aFuOTSdMb8",
            "youtube_link": "https://youtu.be/_aFuOTSdMb8",
            "grammarbook_link": "https://drive.google.com/file/d/1s6TcUzjADzicOKRx3adxW4UdqEXQmz_L/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1PgsULeo11OhzpICZ77RSlVEuuyrSdxSe/view?usp=sharing"
        },
        # TAG 9
        {
            "day": 9,
            "topic": "Work-Life-Balance im modernen Arbeitsumfeld 3.9",
            "chapter": "3.9",
            "goal": "Über Work-Life-Balance und Stress sprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Reflexive Verben",
            "video": "https://youtu.be/3ozjxgOenaI",
            "youtube_link": "https://youtu.be/3ozjxgOenaI",
            "grammarbook_link": "https://drive.google.com/file/d/1Mp6i2pbaTd3r5fLZGqh6NLFZE6txCZpJ/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1giWw3qYhTmm3VO9and2ZuS7ARUFkq7vO/view?usp=sharing"
        },
        # TAG 10
        {
            "day": 10,
            "topic": "Digitale Auszeit und Selbstfürsorge 4.10",
            "chapter": "4.10",
            "goal": "Über digitale Auszeiten und Selbstfürsorge sprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "grammar_topic": "Vergleiche & Superlative",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1zuzkGBkX-NeL6v_lLkOf8dWmc2dJ1n71/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1Rh6SS45s3UCyX5mnU-RTby4K15a0Z_al/view?usp=sharing"
        },
        # TAG 11
        {
            "day": 11,
            "topic": "Teamspiele und Kooperative Aktivitäten 4.11",
            "chapter": "4.11",
            "goal": "Über Teamarbeit und kooperative Aktivitäten sprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/1kq9m4nHQVyj_clhr9GtadLfpSU0CuhnH/view?usp=sharing"
        },
        # TAG 12
        {
            "day": 12,
            "topic": "Abenteuer in der Natur 4.12",
            "chapter": "4.12",
            "goal": "Abenteuer und Erlebnisse in der Natur beschreiben.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1tR7dhUkR-am4c21HInXHP8XdY210MDII/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/14jYuVQ1WKDakOT_z4a4EzwJ0soqQrr8V/view?usp=sharing"
        },
        # TAG 13
        {
            "day": 13,
            "topic": "Eigene Filmkritik schreiben 4.13",
            "chapter": "4.13",
            "goal": "Eine Filmkritik schreiben und Filme bewerten.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "https://youtu.be/8rclmwsAYtc",
            "youtube_link": "https://youtu.be/8rclmwsAYtc",
            "grammarbook_link": "https://drive.google.com/file/d/11_i8x_tmppV5Vzc1jfYAkGAhJYelwMrr/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1dC4H3hyiX2gZ0R3jj_0CAjhl7iBa5oA7/view?usp=sharing"
        },
        # TAG 14
        {
            "day": 14,
            "topic": "Traditionelles vs. digitales Lernen 5.14",
            "chapter": "5.14",
            "goal": "Traditionelles und digitales Lernen vergleichen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1-E7DhaqHRwiFgZ3tWg-NWjctDW7rZScT/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1TMNv-jozqNaaJ_ejoV_5hDXkIbSdr3Nu/view?usp=sharing"
        },
        # TAG 15
        {
            "day": 15,
            "topic": "Medien und Arbeiten im Homeoffice 5.15",
            "chapter": "5.15",
            "goal": "Über Mediennutzung und Homeoffice sprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1a-UYqXhVb4q71o2_2A6z8tk1Fyb_6PA9/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1u82w53DQ2lml3ivUMHiK2I9kXDk_T1IH/view?usp=sharing"
        },
        # TAG 16
        {
            "day": 16,
            "topic": "Prüfungsangst und Stressbewältigung 5.16",
            "chapter": "5.16",
            "goal": "Prüfungsangst und Strategien zur Stressbewältigung besprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/11MN70gt1zEc0nSyeriUNDP4ZOdooYfYF/view?usp=sharing"
        },
        # TAG 17
        {
            "day": 17,
            "topic": "Wie lernt man am besten? 5.17",
            "chapter": "5.17",
            "goal": "Lerntipps geben und Lernstrategien vorstellen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/1U2qtjXfid8Aj5LOqP2Uqpbv18-utgZIh/view?usp=sharing"
        },
        # TAG 18
        {
            "day": 18,
            "topic": "Wege zum Wunschberuf 6.18",
            "chapter": "6.18",
            "goal": "Über Wege zum Wunschberuf sprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/13iU-2CldgD1-pP-kRx55Q7ld0KCU37vD/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1ynVwqtIMGSH1rbCfbPeYE2iRH5plkTC8/view?usp=sharing"
        },
        # TAG 19
        {
            "day": 19,
            "topic": "Das Vorstellungsgespräch 6.19",
            "chapter": "6.19",
            "goal": "Über Vorstellungsgespräche berichten und Tipps geben.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1IimP5JZHHvUYkDSuE7F-YI-Z4PeMYad2/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1fHjQGvObAE3TBmnstPhQBm5RUooP_NyJ/view?usp=sharing"
        },
        # TAG 20
        {
            "day": 20,
            "topic": "Wie wird man …? (Ausbildung und Qu) 6.20",
            "chapter": "6.20",
            "goal": "Über Ausbildung und Qualifikationen sprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/1kfFEDI3ufCCndSi-LhfMFYEdih58D5XQ/view?usp=sharing"
        },
        # TAG 21
        {
            "day": 21,
            "topic": "Lebensformen heute – Familie, Wohnge 7.21",
            "chapter": "7.21",
            "goal": "Lebensformen, Familie und Wohngemeinschaften beschreiben.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1-5hQoiAohD-lB-keyi7mTidjw8YJbvgT/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1y9B__4gEvvdgNzaD17SSWJO0TVRYxFBa/view?usp=sharing"
        },
        # TAG 22
        {
            "day": 22,
            "topic": "Was ist dir in einer Beziehung wichtig? 7.22",
            "chapter": "7.22",
            "goal": "Über Werte in Beziehungen sprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "https://drive.google.com/file/d/1x7Ycdg1DlCjukYoeoSTmnUL8WgkmdXAY/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/15H7jEA7zkl4c58rhybkKPjN1eqK7mPoM/view?usp=sharing"
        },
        # TAG 23
        {
            "day": 23,
            "topic": "Erstes Date – Typische Situationen 7.23",
            "chapter": "7.23",
            "goal": "Typische Situationen beim ersten Date beschreiben.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/1DZxrsgU-vZPGrQAqLuYP3Q3U6KCFy-Cy/view?usp=sharing"
        },
        # TAG 24
        {
            "day": 24,
            "topic": "Konsum und Nachhaltigkeit 8.24",
            "chapter": "8.24",
            "goal": "Nachhaltigen Konsum und Umweltschutz diskutieren.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/1x8IM6xcjR2hv3jbnnNudjyxLWPiT0-VL/view?usp=sharing"
        },
        # TAG 25
        {
            "day": 25,
            "topic": "Online einkaufen – Rechte und Risiken 8.25",
            "chapter": "8.25",
            "goal": "Rechte und Risiken beim Online-Shopping besprechen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/1If0R3cIT8KwjeXjouWlQ-VT03QGYOSZz/view?usp=sharing"
        },
        # TAG 26
        {
            "day": 26,
            "topic": "Reiseprobleme und Lösungen 9.26",
            "chapter": "9.26",
            "goal": "Reiseprobleme und Lösungen beschreiben.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/1BMwDDkfPJVEhL3wHNYqGMAvjOts9tv24/view?usp=sharing"
        },
        # TAG 27
        {
            "day": 27,
            "topic": "Umweltfreundlich im Alltag 10.27",
            "chapter": "10.27",
            "goal": "Umweltfreundliches Verhalten im Alltag beschreiben.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/15fjOKp_u75GfcbvRJVbR8UbHg-cgrgWL/view?usp=sharing"
        },
        # TAG 28
        {
            "day": 28,
            "topic": "Klimafreundlich leben 10.28",
            "chapter": "10.28",
            "goal": "Klimafreundliche Lebensweisen vorstellen.",
            "assignment": True,
            "instruction": "Schau das Video, wiederhole die Grammatik und mache die Aufgabe.",
            "video": "",
            "youtube_link": "",
            "grammarbook_link": "",
            "workbook_link": "https://drive.google.com/file/d/1iBeZHMDq_FnusY4kkRwRQvyOfm51-COU/view?usp=sharing"
        },

        # TAG 29 - ABSCHLUSS / GRATULATION
        {
            "day": 29,
            "topic": "Kurs abgeschlossen!",
            "chapter": None,
            "goal": "🎯 Ziel: Feiere deinen Erfolg und plane deine nächsten Schritte.",
            "instruction": """📝 Herzlichen Glückwunsch! Du hast den B1-Deutschkurs erfolgreich abgeschlossen. 
Du hast fleißig gearbeitet und große Fortschritte gemacht. Die Schule wird deine Ergebnisse bestätigen und dir dein Abschlusszertifikat per E-Mail zusenden.  

Nächste Schritte:  
- Du kannst dich jetzt auf die **B1-Prüfung** vorbereiten oder direkt mit dem **B2-Kurs** weitermachen.  
- Nutze weiterhin die Lern-Tools:  
  • **Prüfungsmodus** (mit alten Goethe-Prüfungsfragen – für Hörverstehen bitte YouTube verwenden)  
  • **Vokabeltrainer**  
  • **Schreibtrainer** mit typischen Prüfungsthemen  
  • **Chat • Grammar • Exams** für zusätzliche Übung  

 Hinweis: Dein Zugang zu deinem Tutor bleibt bis zum Ende deines Vertrags aktiv.  
 Wenn dir der Kurs gefallen hat, hinterlasse uns bitte eine [positive Bewertung auf Google](https://g.page/r/Cdogveq3Hy69EBE/review).  

Wir wünschen dir weiterhin viel Erfolg auf deinem Sprachlernweg! 
            """,
            "grammar_topic": None,
            "assignment": False,
            "lesen_hören": {
                "video": None,
                "youtube_link": None,
                "grammarbook_link": None,
                "workbook_link": None
            }
        },
    ]
    return _strip_topic_chapter(schedule)



def get_b2_schedule():
    schedule = [make_day0_tutorial_entry()]
    schedule.extend([
        {
            "day": 1,
            "topic": "Persönliche Identität und Selbstverständnis",
            "chapter": "1.1",
            "goal": "Drücken Sie Ihre persönliche Identität und Ihre Werte aus.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "https://youtu.be/a9LxkxNdnEg",
            "youtube_link": "https://youtu.be/a9LxkxNdnEg",
            "grammarbook_link": "https://drive.google.com/file/d/17pVc0VfLm32z4zmkaaa_cdshKJEQQxYa/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1D1eb-iwfl_WA2sXPOSPD_66NCiTB4o2w/view?usp=sharing",
            "grammar_topic": "Adjektivdeklination (Adjektivendungen nach bestimmten/unbestimmten Artikeln)"
        },
        {
            "day": 2,
            "topic": "Beziehungen und Kommunikation",
            "chapter": "1.2",
            "goal": "Diskutieren Sie über Beziehungstypen und Kommunikationsstrategien.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "https://youtu.be/gCzZnddwC_c",
            "youtube_link": "https://youtu.be/gCzZnddwC_c",
            "grammarbook_link": "https://drive.google.com/file/d/1Mlt-cK6YqPuJe9iCWfqT9DOG9oKhJBdK/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1XCLW0y-MMyIu_bNO3EkKIgp-8QLKgEek/view?usp=sharing",
            "grammar_topic": "Konjunktiv II (höfliche Bitten & hypothetische Situationen)"
        },
        {
            "day": 3,
            "topic": "Öffentliches vs. Privates Leben",
            "chapter": "1.3",
            "goal": "Vergleichen Sie das öffentliche und private Leben in Deutschland und Ihrem Land.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "https://drive.google.com/file/d/1R0sQc4uSWQNUxPa0_Gdz7PiQaiCyQrrL/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1VteR5sVx_uiKdhSVMBosMxiXe1lfnQnW/view?usp=sharing",
            "grammar_topic": "Passiv (Präsens und Vergangenheit)"
        },
        {
            "day": 4,
            "topic": "Beruf und Karriere",
            "chapter": "1.4",
            "goal": "Sprechen Sie über Berufe, Lebensläufe und Vorstellungsgespräche.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "https://drive.google.com/file/d/1_xVoBqbwCSCs0Xps2Rlx92Ho43Pcbreu/view?usp=sharing",
            "workbook_link": "https://drive.google.com/file/d/1tEKd5Umb-imLpPYrmFfNQyjf4oe2weBp/view?usp=sharing",
            "grammar_topic": "Konjunktiv I"
        },
        {
            "day": 5,
            "topic": "Bildung und Lernen",
            "chapter": "1.5",
            "goal": "Diskutieren Sie das Bildungssystem und lebenslanges Lernen.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Nominalisierung von Verben"
        },
        {
            "day": 6,
            "topic": "Migration und Integration",
            "chapter": "2.1",
            "goal": "Erforschen Sie Migration, Integration und kulturelle Identität.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Temporale Nebensätze (als, wenn, nachdem, während, bevor)"
        },
        {
            "day": 7,
            "topic": "Gesellschaftliche Vielfalt",
            "chapter": "2.2",
            "goal": "Untersuchen Sie Vielfalt und Inklusion in modernen Gesellschaften.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Relativsätze mit Präpositionen"
        },
        {
            "day": 8,
            "topic": "Politik und Engagement",
            "chapter": "2.3",
            "goal": "Lernen Sie politische Systeme und bürgerschaftliches Engagement kennen.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Finale und kausale Nebensätze (damit, um...zu, weil, da)"
        },
        {
            "day": 9,
            "topic": "Technologie und Digitalisierung",
            "chapter": "2.4",
            "goal": "Diskutieren Sie die digitale Transformation und deren Auswirkungen.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Infinitivkonstruktionen mit zu (ohne zu, anstatt zu, um zu, etc.)"
        },
        {
            "day": 10,
            "topic": "Umwelt und Nachhaltigkeit",
            "chapter": "2.5",
            "goal": "Sprechen Sie über Umweltschutz und Nachhaltigkeit.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Konjunktiv II Vergangenheit (hypothetische Vergangenheit)"
        },
        {
            "day": 11,
            "topic": "Gesundheit und Wohlbefinden",
            "chapter": "3.1",
            "goal": "Beschreiben Sie Gesundheit, Wohlbefinden und Lebensstil.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Reflexive Verben und Pronomen"
        },
        {
            "day": 12,
            "topic": "Konsum und Medien",
            "chapter": "3.2",
            "goal": "Analysieren Sie Medieneinfluss und Konsumgewohnheiten.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Modalverben im Passiv"
        },
        {
            "day": 13,
            "topic": "Reisen und Mobilität",
            "chapter": "3.3",
            "goal": "Planen Sie Reisen und diskutieren Sie Transportmöglichkeiten.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Präpositionen mit Genitiv"
        },
        {
            "day": 14,
            "topic": "Wohnen und Zusammenleben",
            "chapter": "3.4",
            "goal": "Vergleichen Sie verschiedene Wohnformen und Gemeinschaften.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Steigerung der Adjektive (Komparativ & Superlativ)"
        },
        {
            "day": 15,
            "topic": "Kunst und Kultur",
            "chapter": "3.5",
            "goal": "Entdecken Sie Kunst, Literatur und kulturelle Veranstaltungen.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Satzbau und Satzstellung"
        },
        {
            "day": 16,
            "topic": "Wissenschaft und Forschung",
            "chapter": "4.1",
            "goal": "Diskutieren Sie wissenschaftliche Entdeckungen und Forschung.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Partizipialkonstruktionen"
        },
        {
            "day": 17,
            "topic": "Feste und Traditionen",
            "chapter": "4.2",
            "goal": "Beschreiben Sie traditionelle Feste und Bräuche.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": ""
        },
        {
            "day": 18,
            "topic": "Freizeit und Hobbys",
            "chapter": "4.3",
            "goal": "Sprechen Sie über Freizeit und Hobbys.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Pronominaladverbien (darauf, worüber, etc.)"
        },
        {
            "day": 19,
            "topic": "Ernährung und Esskultur",
            "chapter": "4.4",
            "goal": "Diskutieren Sie über Essen, Ernährung und Essgewohnheiten.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Indirekte Rede"
        },
        {
            "day": 20,
            "topic": "Mode und Lebensstil",
            "chapter": "4.5",
            "goal": "Untersuchen Sie Mode- und Lebensstiltrends.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": ""
        },
        {
            "day": 21,
            "topic": "Werte und Normen",
            "chapter": "5.1",
            "goal": "Analysieren Sie Werte, Normen und deren Auswirkungen.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Negation: kein-, nicht, ohne, weder...noch"
        },
        {
            "day": 22,
            "topic": "Sprache und Kommunikation",
            "chapter": "5.2",
            "goal": "Diskutieren Sie Sprachenlernen und Kommunikationsstrategien.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Nominalstil vs. Verbalstil"
        },
        {
            "day": 23,
            "topic": "Innovation und Zukunft",
            "chapter": "5.3",
            "goal": "Spekulieren Sie über die Zukunft und Innovationen.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Futur I und II"
        },
        {
            "day": 24,
            "topic": "Gesellschaftliche Herausforderungen",
            "chapter": "5.4",
            "goal": "Diskutieren Sie gesellschaftliche Herausforderungen und mögliche Lösungen.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Subjekt- und Objektive Sätze"
        },
        {
            "day": 25,
            "topic": "Globalisierung und internationale Beziehungen",
            "chapter": "5.5",
            "goal": "Erforschen Sie Globalisierung und deren Auswirkungen.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": "Partizipialattribute"
        },
        {
            "day": 26,
            "topic": "Kreatives Schreiben & Projekte",
            "chapter": "6.1",
            "goal": "Entwickeln Sie kreative Schreibfähigkeiten.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": ""
        },
        {
            "day": 27,
            "topic": "Prüfungstraining & Wiederholung",
            "chapter": "6.2",
            "goal": "Wiederholen Sie B2-Themen und üben Sie Prüfungsformate.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": ""
        },
        {
            "day": 28,
            "topic": "Abschlusspräsentation & Feedback",
            "chapter": "6.3",
            "goal": "Fassen Sie die Kursthemen zusammen und reflektieren Sie Ihren Fortschritt.",
            "instruction": "Schauen Sie das Video, wiederholen Sie die Grammatik und bearbeiten Sie das Arbeitsbuch.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": "",
            "grammar_topic": ""
        }
    ])
    return _strip_topic_chapter(schedule)


# === C1 Schedule Template ===
def get_c1_schedule():
    schedule = [
        {
            "day": 1,
            "topic": "C1 Welcome & Orientation",
            "chapter": "0.0",
            "goal": "Get familiar with the C1 curriculum and expectations.",
            "instruction": "Read the C1 orientation, join the forum, and write a short self-intro.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": ""
        },
        {
            "day": 2,
            "topic": "C1 Diagnostic Writing",
            "chapter": "0.1",
            "goal": "Write a sample essay for initial assessment.",
            "instruction": "Write and upload a short essay on the assigned topic.",
            "video": "",
            "grammarbook_link": "",
            "workbook_link": ""
        }
        # You can add more C1 lessons here in the future
    ]
    return _strip_topic_chapter(schedule)

# --- Cache level schedules with TTL for periodic refresh ---
@st.cache_data(ttl=86400)
def _load_level_schedules_cached():
    return {
        "A1": get_a1_schedule(),
        "A2": get_a2_schedule(),
        "B1": get_b1_schedule(),
        "B2": get_b2_schedule(),
        "C1": get_c1_schedule(),
    }

def load_level_schedules():
    if "level_schedules" not in st.session_state:
        st.session_state["level_schedules"] = _load_level_schedules_cached()
    return st.session_state["level_schedules"]

# -------------------------


def get_level_schedules():
    if "load_level_schedules" in globals() and callable(load_level_schedules):
        return load_level_schedules()
    def _safe(fn):
        try:
            return fn()
        except Exception:
            return []
    return {
        "A1": _safe(get_a1_schedule),
        "A2": _safe(get_a2_schedule),
        "B1": _safe(get_b1_schedule),
        "B2": _safe(get_b2_schedule),
        "C1": _safe(get_c1_schedule),
    }
