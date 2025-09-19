from types import SimpleNamespace

from src.falowen import chat_core
from src.falowen import custom_chat


def _load_increment_fn():
    st = SimpleNamespace(session_state={})
    custom_chat.st = st  # type: ignore[attr-defined]
    chat_core.st = st  # type: ignore[attr-defined]

    def dummy_summary(msgs):
        dummy_summary.called_with = msgs
        return 'SUMMARY'

    custom_chat.generate_summary = dummy_summary  # type: ignore[assignment]
    return (
        custom_chat.increment_turn_count_and_maybe_close,
        dummy_summary,
        st,
        chat_core.reset_falowen_chat_flow,
    )


def test_increment_and_emit_summary_after_six():
    inc, dummy, st, _ = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 5
    ss['falowen_messages'] = [
        {'role': 'user', 'content': 'Hallo'},
        {'role': 'assistant', 'content': 'Hi'},
        {'role': 'user', 'content': 'Tschüss'},
    ]
    ended = inc(False)
    assert ended is True
    assert ss['falowen_turn_count'] == 6
    assert ss['falowen_chat_closed'] is False
    assert ss['falowen_messages'][-1]['content'] == 'SUMMARY'
    assert ss['falowen_summary_emitted'] is True
    assert dummy.called_with == ['Hallo', 'Tschüss']


def test_increment_when_below_limit():
    inc, dummy, st, _ = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 2
    ss['falowen_messages'] = [{'role': 'user', 'content': 'Hallo'}]
    ended = inc(False)
    assert ended is False
    assert ss['falowen_turn_count'] == 3
    assert ss['falowen_messages'] == [{'role': 'user', 'content': 'Hallo'}]
    assert ss['falowen_chat_closed'] is False
    assert ss['falowen_summary_emitted'] is False
    assert not hasattr(dummy, 'called_with')


def test_no_increment_in_exam_mode():
    inc, dummy, st, _ = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 4
    ss['falowen_messages'] = []
    ss['falowen_chat_closed'] = False
    ss['falowen_summary_emitted'] = True
    ended = inc(True)
    assert ended is False
    assert ss['falowen_turn_count'] == 4
    assert ss['falowen_messages'] == []
    assert ss['falowen_chat_closed'] is False
    assert 'falowen_summary_emitted' not in ss
    assert not hasattr(dummy, 'called_with')


def test_new_chat_reset_clears_summary_state():
    inc, dummy, st, reset_chat = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 6
    ss['falowen_messages'] = [{'role': 'user', 'content': 'Hallo'}]
    ss['custom_topic_intro_done'] = True
    ss['falowen_chat_closed'] = False
    ss['falowen_summary_emitted'] = True

    reset_chat()

    assert ss['falowen_turn_count'] == 0
    assert ss['falowen_messages'] == []
    assert ss['custom_topic_intro_done'] is False
    assert ss['falowen_chat_closed'] is False
    assert 'falowen_summary_emitted' not in ss


def test_prevents_duplicate_summary_after_emission():
    inc, dummy, st, _ = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 6
    ss['falowen_messages'] = [
        {'role': 'user', 'content': 'Hallo'},
        {'role': 'assistant', 'content': 'Hi'},
        {'role': 'assistant', 'content': 'SUMMARY'},
    ]
    ss['falowen_chat_closed'] = False
    ss['falowen_summary_emitted'] = True

    ended = inc(False)

    assert ended is False
    assert ss['falowen_turn_count'] == 7
    assert ss['falowen_messages'][-1]['content'] == 'SUMMARY'
    assert not hasattr(dummy, 'called_with')


def test_summary_only_once_chat_remains_open():
    inc, dummy, st, _ = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 5
    ss['falowen_messages'] = [
        {'role': 'user', 'content': 'Hallo'},
        {'role': 'assistant', 'content': 'Hi'},
        {'role': 'user', 'content': 'Tschüss'},
    ]

    first = inc(False)
    assert first is True
    assert ss['falowen_summary_emitted'] is True
    assert ss['falowen_chat_closed'] is False

    second = inc(False)
    assert second is False
    assert ss['falowen_turn_count'] == 7
    assert ss['falowen_chat_closed'] is False
    assert ss['falowen_messages'].count({'role': 'assistant', 'content': 'SUMMARY'}) == 1
    assert dummy.called_with == ['Hallo', 'Tschüss']
