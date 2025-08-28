"""UI helpers for displaying student statistics."""

from __future__ import annotations

import streamlit as st

from .stats import get_vocab_stats, get_schreiben_stats


def render_vocab_stats(student_code: str):
    """Render the vocabulary practice statistics expander.

    Returns the statistics dictionary so callers can reuse it without
    performing another Firestore lookup.
    """

    stats = get_vocab_stats(student_code)
    with st.expander("📝 Your Vocab Stats", expanded=False):
        st.markdown(f"- **Sessions:** {stats['total_sessions']}")
        st.markdown(f"- **Last Practiced:** {stats['last_practiced']}")
        st.markdown(f"- **Unique Words:** {len(stats['completed_words'])}")
        if st.checkbox("Show Last 5 Sessions"):
            for a in stats["history"][-5:][::-1]:
                st.markdown(
                    f"- {a['timestamp']} | {a['correct']}/{a['total']} | {a['level']}<br>"
                    f"<span style='font-size:0.9em;'>Words: {', '.join(a['practiced_words'])}</span>",
                    unsafe_allow_html=True,
                )
    return stats


def render_schreiben_stats(student_code: str):
    """Show writing statistics and return them for further use."""

    stats = get_schreiben_stats(student_code)
    if stats:
        total = stats.get("total", 0)
        passed = stats.get("passed", 0)
        pass_rate = stats.get("pass_rate", 0)

        if total <= 2:
            writer_title = "🟡 Beginner Writer"
            milestone = "Write 3 letters to become a Rising Writer!"
        elif total <= 5 or pass_rate < 60:
            writer_title = "🟡 Rising Writer"
            milestone = "Achieve 60% pass rate and 6 letters to become a Confident Writer!"
        elif total <= 7 or (60 <= pass_rate < 80):
            writer_title = "🔵 Confident Writer"
            milestone = "Reach 8 attempts and 80% pass rate to become an Advanced Writer!"
        elif total >= 8 and pass_rate >= 80 and not (total >= 10 and pass_rate >= 95):
            writer_title = "🟢 Advanced Writer"
            milestone = "Reach 10 attempts and 95% pass rate to become a Master Writer!"
        elif total >= 10 and pass_rate >= 95:
            writer_title = "🏅 Master Writer!"
            milestone = "You've reached the highest milestone! Keep maintaining your skills 🎉"
        else:
            writer_title = "✏️ Active Writer"
            milestone = "Keep going to unlock your next milestone!"

        st.markdown(
            f"""
            <div style="background:#fff8e1;padding:18px 12px 14px 12px;border-radius:12px;margin-bottom:12px;
                        box-shadow:0 1px 6px #00000010;">
                <span style="font-weight:bold;font-size:1.25rem;color:#d63384;">{writer_title}</span><br>
                <span style="font-weight:bold;font-size:1.09rem;color:#444;">📊 Your Writing Stats</span><br>
                <span style="color:#202020;font-size:1.05rem;"><b>Total Attempts:</b> {total}</span><br>
                <span style="color:#202020;font-size:1.05rem;"><b>Passed:</b> {passed}</span><br>
                <span style="color:#202020;font-size:1.05rem;"><b>Pass Rate:</b> {pass_rate:.1f}%</span><br>
                <span style="color:#e65100;font-weight:bold;font-size:1.03rem;">{milestone}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("No writing stats found yet. Write your first letter to see progress!")
    return stats


__all__ = ["render_vocab_stats", "render_schreiben_stats"]
