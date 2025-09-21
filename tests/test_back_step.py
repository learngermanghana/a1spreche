from types import SimpleNamespace
from unittest.mock import MagicMock

from src.draft_management import _draft_state_keys
from src.falowen import chat_core
from src.utils import toasts


def _load_back_step():
    st = SimpleNamespace(session_state={}, toast=MagicMock())
    chat_core.st = st  # type: ignore[attr-defined]
    toasts.st = st
    return chat_core.back_step, st


def test_back_step_clears_chat_state():
    back_step, st = _load_back_step()
    ss = st.session_state
    ss.update({
        'falowen_stage': 3,
        'falowen_mode': 'mode',
        'falowen_level': 'A1',
        'falowen_teil': 'T1',
        'falowen_messages': ['hi'],
        'falowen_loaded_key': 'lk',
        'falowen_conv_key': 'conv',
        'falowen_chat_draft_key': 'chat_draft_123',
        'custom_topic_intro_done': True,
        'falowen_turn_count': 5,
        'falowen_chat_closed': True,
        '__refresh': 0,
    })
    draft_key = ss['falowen_chat_draft_key']
    ss[draft_key] = 'draft text'
    for extra in _draft_state_keys(draft_key):
        ss[extra] = 'meta'

    back_step()

    assert ss['falowen_stage'] == 1
    assert ss['_falowen_loaded'] is False
    assert ss['__refresh'] == 1
    assert ss['need_rerun'] is True
    assert ss['falowen_level'] == 'A1'
    st.toast.assert_not_called()

    for key in [
        'falowen_mode', 'falowen_teil',
        'falowen_messages',
        'falowen_loaded_key', 'falowen_conv_key',
        'falowen_chat_draft_key', 'custom_topic_intro_done',
        'falowen_turn_count', 'falowen_chat_closed',
        draft_key, *_draft_state_keys(draft_key)
    ]:
        assert key not in ss
