"""Prompt bank utilities for brain-map style scaffolds and AI coaching prompts."""
from __future__ import annotations

import importlib.util
import json
from textwrap import dedent
from typing import Dict, List, Sequence

_yaml_spec = importlib.util.find_spec("yaml")
if _yaml_spec:
    import yaml  # type: ignore
else:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore

BRAIN_MAP_SCAFFOLDS: List[Dict[str, object]] = [
    {
        "theme": "Alltag & Termine",
        "situation": "Einen Arzttermin kurz nach der Arbeit vereinbaren",
        "bullet_outline": [
            "Beschreiben Sie in einem Satz Ihr Hauptsymptom.",
            "Bitten Sie um einen Termin nach 17:00 Uhr und schlagen Sie einen Tag vor.",
            "Fragen Sie, ob Sie Unterlagen oder Medikamente mitbringen sollen.",
        ],
        "target_functions": [
            "Terminvereinbarung", "Zeit aushandeln", "Höflich um Hinweise bitten"
        ],
    },
    {
        "theme": "Wohnen & Nachbarschaft",
        "situation": "Lärmproblem im Mehrfamilienhaus klären",
        "bullet_outline": [
            "Beschreiben Sie höflich, wann und wie oft der Lärm auftritt.",
            "Schlagen Sie eine Lösung oder ruhige Zeiten vor.",
            "Bitten Sie um Rückmeldung und bedanken Sie sich.",
        ],
        "target_functions": [
            "Beschwerden formulieren", "Vorschläge machen", "Rückmeldung einholen"
        ],
    },
    {
        "theme": "Arbeit & Projekte",
        "situation": "Eine Kollegin um Unterstützung bei einer Präsentation bitten",
        "bullet_outline": [
            "Nennen Sie das Thema und das Datum der Präsentation.",
            "Fragen Sie konkret nach Hilfe (z. B. Folien prüfen, Feedback geben).",
            "Erklären Sie kurz, warum ihre Perspektive wichtig ist.",
        ],
        "target_functions": [
            "Um Hilfe bitten", "Aufgaben beschreiben", "Begründungen geben"
        ],
    },
    {
        "theme": "Reisen & Orientierung",
        "situation": "Eine Zugverbindung mit Umstieg planen",
        "bullet_outline": [
            "Sagen Sie Start- und Zielbahnhof sowie das gewünschte Datum.",
            "Fragen Sie nach der besten Umstiegsoption und Pufferzeiten.",
            "Klären Sie Tickettyp, Sitzplatzwunsch und eventuelle Rabatte.",
        ],
        "target_functions": [
            "Informationen erfragen", "Optionen vergleichen", "Kaufentscheidungen treffen"
        ],
    },
    {
        "theme": "Studium & Kurse",
        "situation": "Einen Kurswechsel mit der Studienberatung besprechen",
        "bullet_outline": [
            "Nennen Sie den aktuellen Kurs und den gewünschten Kurs.",
            "Erklären Sie kurz, warum der Wechsel notwendig oder hilfreich ist.",
            "Fragen Sie nach freien Plätzen und nächsten Schritten.",
        ],
        "target_functions": [
            "Argumentieren", "Nach Verfügbarkeit fragen", "Verbindliche Schritte klären"
        ],
    },
]

WRITING_TASK_TEMPLATES: List[Dict[str, object]] = [
    {
        "title": "Service-Beschwerde per E-Mail",
        "genre": "Formelle E-Mail (Beschwerde)",
        "target_length": "140–170 Wörter",
        "communicative_goal": "Problem präzise schildern und eine konkrete Lösung einfordern",
        "key_connectors": ["zunächst", "außerdem", "dennoch", "abschließend"],
    },
    {
        "title": "Projekt-Update an Stakeholder",
        "genre": "Halbformeller Statusbericht",
        "target_length": "170–200 Wörter",
        "communicative_goal": "Fortschritt darstellen, Risiken benennen und nächste Schritte vorschlagen",
        "key_connectors": ["aktuell", "zugleich", "allerdings", "daher", "abschließend"],
    },
    {
        "title": "Meinungsbeitrag zu Stadtentwicklung",
        "genre": "Kommentar / Meinungstext",
        "target_length": "180–210 Wörter",
        "communicative_goal": "Position klar vertreten, Gegenargumente aufgreifen und Fazit ziehen",
        "key_connectors": ["einerseits", "andererseits", "zudem", "denn", "infolgedessen"],
    },
    {
        "title": "Bitte um akademische Empfehlung",
        "genre": "Formeller Bewerbungsbrief",
        "target_length": "160–190 Wörter",
        "communicative_goal": "Hintergrund schildern, Qualifikationen hervorheben und Empfehlung erbitten",
        "key_connectors": ["zunächst", "ferner", "insbesondere", "daher", "mit freundlichen Grüßen"],
    },
    {
        "title": "Antwort auf Kundenkritik",
        "genre": "Formelle Antwort / Schadensbegrenzung",
        "target_length": "150–180 Wörter",
        "communicative_goal": "Kritik anerkennen, Verantwortung übernehmen und Wiedergutmachung anbieten",
        "key_connectors": ["wir bedauern", "gleichzeitig", "umgehend", "damit", "abschließend"],
    },
]

DEFAULT_RUBRIC: Dict[str, str] = {
    "Aufgabenbewältigung": "Erfüllt der Text alle Stichpunkte der Brain-Map-Situation?",
    "Kohärenz & Organisation": "Logischer Aufbau mit klaren Übergängen und Absätzen?",
    "Lexik": "Passender Wortschatz, Kollokationen und Register für die Situation?",
    "Grammatik & Struktur": "Sichere Satzstrukturen, Verbzweitstellung und Nebensätze?",
    "Fluss & Diskursmarker": "Nutzt Konnektoren (z. B. außerdem, jedoch, danach) für flüssiges Lesen?",
}

PATTERN_BANKS: Dict[str, Dict[str, object]] = {
    "weil_clause": {
        "structure": "weil + Nebensatz (Verb am Ende)",
        "cefr": "A2",
        "examples": [
            {
                "input": "Ich bleibe zu Hause. Ich bin krank.",
                "output": "Ich bleibe zu Hause, weil ich krank bin.",
            },
            {
                "input": "Er fährt mit dem Rad. Er möchte Geld sparen.",
                "output": "Er fährt mit dem Rad, weil er Geld sparen möchte.",
            },
            {
                "input": "Wir können nicht kommen. Wir arbeiten heute Abend.",
                "output": "Wir können nicht kommen, weil wir heute Abend arbeiten.",
            },
            {
                "input": "Sie ruft später an. Sie ist gerade im Meeting.",
                "output": "Sie ruft später an, weil sie gerade im Meeting ist.",
            },
        ],
        "upgrade_tip": "Setze das finites Verb konsequent ans Satzende und variiere Tempus/Modalverben.",
    },
    "zu_infinitive": {
        "structure": "um/ohne/anstatt ... zu + Infinitiv",
        "cefr": "B1",
        "examples": [
            {
                "input": "Er lernt viel. Er möchte die Prüfung bestehen.",
                "output": "Er lernt viel, um die Prüfung zu bestehen.",
            },
            {
                "input": "Sie ging früh. Sie wollte den Zug nicht verpassen.",
                "output": "Sie ging früh, um den Zug nicht zu verpassen.",
            },
            {
                "input": "Er hat nichts gesagt. Er wollte niemanden verletzen.",
                "output": "Er hat nichts gesagt, um niemanden zu verletzen.",
            },
            {
                "input": "Sie las die Anleitung nicht. Sie baute das Regal falsch auf.",
                "output": "Sie baute das Regal falsch auf, ohne die Anleitung zu lesen.",
            },
            {
                "input": "Er schrieb die E-Mail nicht. Er rief den Kunden sofort an.",
                "output": "Er rief den Kunden sofort an, anstatt die E-Mail zu schreiben.",
            },
        ],
        "upgrade_tip": "Nutze klare Ziel-/Kontrastmarkierungen (um, ohne, anstatt) und reduziere Doppelungen.",
    },
    "passiv_werden": {
        "structure": "Vorgangspassiv mit werden + Partizip II",
        "cefr": "B1",
        "examples": [
            {
                "input": "Die Firma renoviert das Büro.",
                "output": "Das Büro wird renoviert.",
            },
            {
                "input": "Jemand hat den Bericht geschrieben.",
                "output": "Der Bericht wurde geschrieben.",
            },
            {
                "input": "Man bringt das Essen gleich.",
                "output": "Das Essen wird gleich gebracht.",
            },
            {
                "input": "Die Handwerker reparieren die Heizung.",
                "output": "Die Heizung wird repariert.",
            },
            {
                "input": "Jemand hat die Tür geschlossen.",
                "output": "Die Tür wurde geschlossen.",
            },
        ],
        "upgrade_tip": "Achte auf Zeitform (wird/wurde) und füge bei Bedarf ein von- oder durch-Agent ein.",
    },
}


def brain_map_prompts_as_json(scaffolds: Sequence[Dict[str, object]] | None = None) -> str:
    """Return the brain-map prompt bank as pretty-printed JSON."""

    data = list(scaffolds) if scaffolds is not None else BRAIN_MAP_SCAFFOLDS
    return json.dumps(data, ensure_ascii=False, indent=2)


def brain_map_prompts_as_yaml(scaffolds: Sequence[Dict[str, object]] | None = None) -> str:
    """Return the brain-map prompt bank as YAML if available, else JSON fallback."""

    data = list(scaffolds) if scaffolds is not None else BRAIN_MAP_SCAFFOLDS
    if yaml is None:
        return brain_map_prompts_as_json(data)
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def build_plan_prompt(scaffold: Dict[str, object]) -> str:
    """Build a prompt that elicits a concise plan before writing."""

    outline = "\n- ".join([""] + list(scaffold.get("bullet_outline", [])))
    return dedent(
        f"""
        You are a German writing coach. Read the brain-map scaffold and propose a
        brief plan (max 4 sentences) the learner will follow before drafting.

        Theme: {scaffold.get('theme')}
        Situation: {scaffold.get('situation')}
        Bullet outline:{outline}
        Target functions: {', '.join(scaffold.get('target_functions', []))}

        Output:
        - 1–2 guiding questions the learner should answer.
        - A concise action plan with ordering and time-boxed steps.
        - One tip to keep vocabulary and grammar aligned with the CEFR level.
        """
    ).strip()


def build_interlocutor_prompt(scaffold: Dict[str, object]) -> str:
    """Build a prompt that simulates an interlocutor with focused follow-ups."""

    return dedent(
        f"""
        Act as a succinct German interlocutor for the scenario below. Ask 3–4
        follow-up questions total, one at a time, staying within the theme and
        target functions. Keep language at the learner's CEFR level and avoid
        long explanations.

        Theme: {scaffold.get('theme')}
        Situation: {scaffold.get('situation')}
        Target functions: {', '.join(scaffold.get('target_functions', []))}

        Each turn:
        - Ask exactly one question that advances the bullet outline.
        - Offer one micro-prompt if the learner hesitates.
        - Track which bullet points are already covered.
        """
    ).strip()


def build_feedback_prompt(scaffold: Dict[str, object]) -> str:
    """Build a rubric-driven feedback prompt with CEFR scoring and reflection."""

    rubric_lines = "\n".join([f"- {k}: {v}" for k, v in DEFAULT_RUBRIC.items()])
    return dedent(
        f"""
        You are an examiner providing rubric-based feedback for the writing task.
        Use the brain-map scaffold to judge completeness, then return:
        1) A CEFR-aligned score (A1–C2) plus a 0–100 numeric score.
        2) A brief justification referencing the bullet outline and target functions.
        3) A structured rubric summary using the categories below.
        4) Reflection: suggest 2–3 concrete upgrades — one lexical, one syntactic,
           and one with discourse markers — plus a mini-drill where the learner
           rewrites a key sentence in two varied ways.

        Theme: {scaffold.get('theme')}
        Situation: {scaffold.get('situation')}
        Bullet outline: {', '.join(scaffold.get('bullet_outline', []))}
        Target functions: {', '.join(scaffold.get('target_functions', []))}

        Rubric:
        {rubric_lines}

        Output format:
        - <score>CEFR level – numeric/100</score>
        - <justification>2–3 sentences grounded in the scaffold</justification>
        - <rubric_notes>bulleted notes per category</rubric_notes>
        - <reflection>
            • Upgrade (lexical)
            • Upgrade (syntax)
            • Upgrade (discourse marker)
            • Mini-drill: repeat one key sentence with two variations
          </reflection>
        """
        ).strip()


def build_pattern_drill_prompt(structure_key: str, learner_level: str | None = None) -> str:
    """Build a multi-step drill prompt for grammar pattern practice."""

    bank = PATTERN_BANKS.get(structure_key)
    if bank is None:
        raise KeyError(f"Unknown pattern bank: {structure_key}")

    pairs = bank.get("examples", [])
    formatted_pairs = "\n".join(
        [f"- Input: {ex['input']} → Output: {ex['output']}" for ex in pairs]
    )
    cefr = learner_level or bank.get("cefr", "")
    upgrade_tip = bank.get("upgrade_tip", "")

    return dedent(
        f"""
        You are a precise German tutor. Use the pattern bank to run a complete mini-workshop.

        Target structure: {bank.get('structure')}
        CEFR focus: {cefr}
        Pattern bank (input → output pairs):
        {formatted_pairs}

        Actions (keep instructions compact and level-appropriate):
        a) Recognition: ask for 2 quick checks to spot where the pattern fits.
        b) Transformations: give 5–10 prompts that require transforming inputs using the pattern.
        c) Production: create 3 prompts asking for free sentences that still require the pattern.
        d) After a learner reply, return concise corrections plus one upgraded sample answer per item.

        Tip: {upgrade_tip}
        """
    ).strip()


def build_review_prompt(
    task_template: Dict[str, object], rubric: Dict[str, str] | None = None
) -> str:
    """Build a rich review prompt with rubric scores and practice drills."""

    rubric_source = rubric or DEFAULT_RUBRIC
    rubric_lines = "\n".join([f"- {k}: {v}" for k, v in rubric_source.items()])
    connectors = ", ".join(task_template.get("key_connectors", []))

    return dedent(
        f"""
        You are a concise but encouraging German writing examiner. Evaluate the
        learner's submission for the task below and respond with numbered,
        clearly separated sections.

        Task template:
        - Title: {task_template.get('title')}
        - Genre: {task_template.get('genre')}
        - Target length: {task_template.get('target_length')}
        - Communicative goal: {task_template.get('communicative_goal')}
        - Key connectors to privilege: {connectors}

        Rubric focus:
        {rubric_lines}

        Output strictly in this order:
        1) Holistic comment (2–3 sentences) on how well the text fulfills the
           communicative goal and genre conventions.
        2) Per-criterion scores (0–5) with one short rationale each, aligned to
           the rubric above.
        3) Inline error list: bullet each issue with the exact snippet and a
           corrected version (grammar, lexicon, cohesion).
        4) Three rewrites of the weakest sentences with upgraded connectors or
           syntax; keep them concise and level-appropriate.
        5) Five-item micro-drill: mix of gap-fill or transformation items that
           recycle the learner's errors and the required connectors.
        6) Next-step task: adjust difficulty (e.g., tighter register, more
           hedging, denser argumentation, or stricter word limit) and restate
           the modified assignment in 1–2 sentences.
        """
    ).strip()
