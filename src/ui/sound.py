"""Utilities for playing short UI feedback sounds in Streamlit."""
from __future__ import annotations

from functools import wraps
from typing import Callable

import streamlit as st

try:
    from streamlit.delta_generator import DeltaGenerator
except Exception:  # pragma: no cover - Streamlit unavailable in some contexts
    DeltaGenerator = None  # type: ignore[assignment]

_FLAG_KEY = "__falowen_play_sound_flag"
_COUNTER_KEY = "__falowen_play_sound_counter"


def _mark_sound_flag(result: bool) -> bool:
    if result:
        st.session_state[_FLAG_KEY] = True
    return result


def _wrap_delta_method(name: str) -> None:
    if DeltaGenerator is None:
        return
    original: Callable | None = getattr(DeltaGenerator, name, None)
    if original is None or getattr(original, "__falowen_sound_wrapped__", False):
        return

    @wraps(original)
    def wrapper(self, *args, __orig: Callable = original, **kwargs):  # type: ignore[override]
        result = __orig(self, *args, **kwargs)
        return _mark_sound_flag(result)

    setattr(wrapper, "__falowen_sound_wrapped__", True)
    setattr(DeltaGenerator, name, wrapper)  # type: ignore[attr-defined]


for _method in ("button", "form_submit_button", "link_button"):
    _wrap_delta_method(_method)


def play_ui_sound(force: bool | None = None) -> None:
    """Play the UI sound if the flag was toggled during this run."""

    should_play = force if force is not None else bool(st.session_state.pop(_FLAG_KEY, False))
    if not should_play:
        return

    counter = int(st.session_state.get(_COUNTER_KEY, 0)) + 1
    st.session_state[_COUNTER_KEY] = counter

    st.markdown(
        f"""
        <script id="falowen-sound-{counter}">
        (function() {{
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) {{ return; }}
            window.__falowenAudioCtx = window.__falowenAudioCtx || new AudioCtx();
            const ctx = window.__falowenAudioCtx;
            if (ctx.state === "suspended") {{
                ctx.resume().catch(() => {{}});
            }}
            const now = ctx.currentTime;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = "sine";
            osc.frequency.setValueAtTime(880, now);
            gain.gain.setValueAtTime(0.0001, now);
            gain.gain.exponentialRampToValueAtTime(0.2, now + 0.01);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.22);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.24);
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["play_ui_sound"]
