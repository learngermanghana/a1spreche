"""Helpers for spaced-repetition style vocabulary scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from src.stats import update_vocab_schedule

DEFAULT_EASE = 2.5
MIN_EASE = 1.3
EASE_INCREMENT = 0.1
EASE_PENALTY = 0.2


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def _default_state() -> Dict[str, object]:
    return {
        "ease": DEFAULT_EASE,
        "interval": 0,
        "repetitions": 0,
        "last_review": None,
        "next_due": None,
        "last_result": None,
    }


def _normalise_state(raw: Optional[Dict[str, object]]) -> Dict[str, object]:
    state = _default_state()
    if not raw:
        return state
    for key in state:
        if key in raw:
            state[key] = raw[key]
    return state


def _compute_next_state(
    state: Dict[str, object],
    *,
    correct: bool,
    now: datetime,
) -> Dict[str, object]:
    ease = float(state.get("ease", DEFAULT_EASE) or DEFAULT_EASE)
    interval = int(state.get("interval", 0) or 0)
    repetitions = int(state.get("repetitions", 0) or 0)

    if correct:
        repetitions += 1
        ease = max(MIN_EASE, ease + EASE_INCREMENT)
        if interval == 0:
            interval = 1
        elif interval == 1:
            interval = 3
        else:
            interval = max(1, int(round(interval * ease)))
    else:
        repetitions = 0
        ease = max(MIN_EASE, ease - EASE_PENALTY)
        interval = 1

    next_due = now + timedelta(days=interval)

    return {
        "ease": round(ease, 3),
        "interval": int(interval),
        "repetitions": int(repetitions),
        "last_review": _format_datetime(now),
        "next_due": _format_datetime(next_due),
        "last_result": "correct" if correct else "incorrect",
    }


@dataclass
class DueItem:
    pair: Tuple[str, str]
    due_at: datetime


class VocabScheduleManager:
    """Manage spaced-repetition scheduling for vocab practice."""

    def __init__(
        self,
        student_code: str,
        schedule: Optional[Dict[str, Dict[str, object]]] = None,
        *,
        now: Optional[datetime] = None,
    ) -> None:
        self.student_code = student_code
        self.now = (now or _utc_now()).astimezone(timezone.utc)
        raw = schedule or {}
        self.schedule: Dict[str, Dict[str, object]] = {
            str(word): _normalise_state(payload)
            for word, payload in raw.items()
            if str(word).strip()
        }

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------
    @property
    def known_words(self) -> Sequence[str]:
        return tuple(sorted(self.schedule.keys()))

    def due_items(self, items: Iterable[Tuple[str, str]]) -> List[DueItem]:
        results: List[DueItem] = []
        for pair in items:
            word = str(pair[0])
            state = self.schedule.get(word)
            if not state:
                continue
            due_at = _parse_datetime(state.get("next_due"))
            if due_at and due_at <= self.now:
                results.append(DueItem(pair=pair, due_at=due_at))
        results.sort(key=lambda item: item.due_at)
        return results

    def next_due_after_now(self) -> Optional[str]:
        upcoming: List[datetime] = []
        for state in self.schedule.values():
            due_at = _parse_datetime(state.get("next_due"))
            if due_at and due_at > self.now:
                upcoming.append(due_at)
        if not upcoming:
            return None
        upcoming.sort()
        return _format_datetime(upcoming[0])

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    def record_session(
        self,
        practiced_words: Iterable[str],
        incorrect_words: Iterable[str],
    ) -> Dict[str, Dict[str, object]]:
        updates: Dict[str, Dict[str, object]] = {}
        incorrect_set = {str(word) for word in incorrect_words}
        for word in practiced_words:
            key = str(word)
            if not key:
                continue
            state = self.schedule.get(key, _default_state())
            updated = _compute_next_state(
                state,
                correct=key not in incorrect_set,
                now=self.now,
            )
            updates[key] = updated
            self.schedule[key] = updated
        return updates

    def snooze_cards(
        self,
        words: Sequence[str],
        *,
        days: int = 1,
    ) -> Dict[str, Dict[str, object]]:
        if days < 1:
            days = 1
        updates: Dict[str, Dict[str, object]] = {}
        delta = timedelta(days=days)
        for raw_word in words:
            word = str(raw_word)
            if not word:
                continue
            state = self.schedule.get(word, _default_state()).copy()
            base_due = _parse_datetime(state.get("next_due")) or self.now
            new_due = base_due + delta
            state.setdefault("ease", DEFAULT_EASE)
            state.setdefault("interval", max(int(state.get("interval", 1) or 1), 1))
            state.setdefault("repetitions", int(state.get("repetitions", 0) or 0))
            state["next_due"] = _format_datetime(new_due)
            updates[word] = state
            self.schedule[word] = state
        return updates

    def reset_cards(self, words: Sequence[str]) -> Dict[str, Optional[Dict[str, object]]]:
        updates: Dict[str, Optional[Dict[str, object]]] = {}
        for raw_word in words:
            word = str(raw_word)
            if not word:
                continue
            updates[word] = None
            self.schedule.pop(word, None)
        return updates

    def persist_updates(
        self, updates: Dict[str, Optional[Dict[str, object]]]
    ) -> None:
        if not updates:
            return
        update_vocab_schedule(self.student_code, updates)


__all__ = [
    "DEFAULT_EASE",
    "MIN_EASE",
    "VocabScheduleManager",
    "DueItem",
]
