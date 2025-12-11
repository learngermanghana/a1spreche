"""Lightweight proficiency profiling and next-task planning utilities."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Dict, Iterable, List, Mapping, MutableMapping, Sequence

PROFICIENCY_TAGS: Mapping[str, str] = {
    "cohesion": "Logic, paragraphing, and how well ideas connect.",
    "register": "Appropriateness of tone, formality, and audience fit.",
    "accuracy": "Grammar and form accuracy at the learner's target level.",
    "range": "Variety of structures, connectors, and lexical choices.",
    "fluency": "Ease of expression, pacing, and flow without hesitation cues.",
}

REMEDIATION_TAGS: Mapping[str, str] = {
    "cohesion": "Model transitions and paragraph planning; add linking devices.",
    "register": "Check formality, pronouns, and greetings against audience needs.",
    "accuracy": "Target tense/word order drills; rebuild sentences with fewer errors.",
    "range": "Stretch to new connectors and clause types; avoid repeating safe forms.",
    "fluency": "Practice timed responses and chunking; reduce fillers.",
}


@dataclass
class TaskRecord:
    """Snapshot of a single practice task."""

    task_id: str
    score: float | None = None
    errors: List[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ProfileStore:
    """Minimal in-memory store for profiling task outcomes."""

    def __init__(self, *, history_limit: int = 20) -> None:
        self.history_limit = max(1, history_limit)
        self._profiles: Dict[str, Dict[str, object]] = {}

    def _profile(self, student_code: str) -> Dict[str, object]:
        code = student_code or "unknown"
        profile = self._profiles.setdefault(
            code,
            {
                "error_counts": Counter(),
                "history": deque(maxlen=self.history_limit),
            },
        )
        # Ensure deque retains configured limit even when restored from a plain list
        if not isinstance(profile.get("history"), deque):
            profile["history"] = deque(profile.get("history", []), maxlen=self.history_limit)
        return profile

    def tag_errors(self, raw_errors: Iterable[str]) -> List[str]:
        """Return recognised proficiency tags for the provided error labels."""

        tags: List[str] = []
        for err in raw_errors:
            key = str(err).strip().casefold()
            if key in PROFICIENCY_TAGS:
                tags.append(key)
        return tags

    def record_task_completion(
        self,
        *,
        student_code: str,
        task_id: str,
        score: float | None = None,
        errors: Iterable[str] = (),
    ) -> TaskRecord:
        """Normalise errors, append a task record, and update tag counts."""

        profile = self._profile(student_code)
        tagged_errors = self.tag_errors(errors)

        history: Deque[TaskRecord] = profile["history"]  # type: ignore[assignment]
        record = TaskRecord(task_id=task_id, score=score, errors=tagged_errors)
        history.append(record)

        error_counts: Counter = profile["error_counts"]  # type: ignore[assignment]
        error_counts.update(tagged_errors)

        return record

    def snapshot(self, student_code: str) -> Dict[str, object]:
        """Return a read-only snapshot of the student's profile."""

        profile = self._profile(student_code)
        history: Deque[TaskRecord] = profile["history"]  # type: ignore[assignment]
        return {
            "error_counts": profile["error_counts"].copy(),
            "history": list(history),
        }

    def top_gaps(self, student_code: str, *, limit: int = 3) -> List[tuple[str, int]]:
        """Return the most frequent tags sorted by need."""

        counts: Counter = self._profile(student_code)["error_counts"]  # type: ignore[assignment]
        return counts.most_common(limit)

    def recent_tasks(self, student_code: str, *, limit: int = 3) -> List[TaskRecord]:
        """Return the most recent task records (newest last)."""

        history: Deque[TaskRecord] = self._profile(student_code)["history"]  # type: ignore[assignment]
        recent = list(history)[-limit:]
        return recent


def build_planner_prompt(
    *,
    student_code: str,
    available_tasks: Sequence[Mapping[str, object]],
    profile_store: ProfileStore,
    recent_limit: int = 3,
) -> str:
    """Construct a planner prompt emphasising profile gaps and fresh results."""

    profile = profile_store.snapshot(student_code)
    gaps = profile_store.top_gaps(student_code, limit=len(PROFICIENCY_TAGS))
    recent_tasks = profile_store.recent_tasks(student_code, limit=recent_limit)

    task_lines = []
    for task in available_tasks:
        task_id = str(task.get("id") or task.get("task_id") or "")
        focus = ", ".join(
            tag for tag in task.get("focus_tags", []) if str(tag).casefold() in PROFICIENCY_TAGS
        )
        label = str(task.get("label") or task_id)
        task_lines.append(f"- {label} (id={task_id}; focus: {focus or 'general'})")

    gap_lines = []
    for tag, count in gaps:
        if tag in REMEDIATION_TAGS:
            gap_lines.append(
                f"- {tag.title()}: {count} recent flags. Remedy: {REMEDIATION_TAGS[tag]}"
            )

    recent_lines = []
    for record in recent_tasks:
        recent_lines.append(
            f"- {record.task_id}: score={record.score if record.score is not None else 'n/a'}; "
            f"errors={', '.join(record.errors) if record.errors else 'none'}"
        )

    prompt_sections = [
        "You are an AI planner choosing the next practice task.",
        f"Student code: {student_code or 'unknown'}.",
        "Available tasks (choose one):",
        "\n".join(task_lines) if task_lines else "- No tasks provided",
        "Profile gaps to target (highest need first):",
        "\n".join(gap_lines) if gap_lines else "- No errors recorded yet",
        "Recent performance (most recent last):",
        "\n".join(recent_lines) if recent_lines else "- No recent tasks",
        "Planning rules:",
        "- Prioritise tasks that address the highest-need tags above.",
        "- Avoid repeating the same task id as the most recent entry unless no alternatives exist.",
        "- When gaps are empty, rotate through different focus areas to build range.",
        "Respond with the chosen task id and a one-line rationale.",
    ]

    return "\n".join(prompt_sections)


__all__ = [
    "PROFICIENCY_TAGS",
    "REMEDIATION_TAGS",
    "ProfileStore",
    "TaskRecord",
    "build_planner_prompt",
]
