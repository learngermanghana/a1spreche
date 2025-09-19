import ast
from types import SimpleNamespace

from src.draft_management import _draft_state_keys
from src.utils import toasts


def _load_back_step():
    with open("a1sprechen.py", "r", encoding="utf-8") as f:
        src = f.read()
    mod = ast.parse(src)
    funcs = [
        node for node in mod.body if isinstance(node, ast.FunctionDef) and node.name == "back_step"
    ]
    module_ast = ast.Module(body=funcs, type_ignores=[])
    code = compile(module_ast, "a1sprechen.py", "exec")
    st = SimpleNamespace(session_state={}, toast=lambda *a, **k: None)
    toasts.st = st
    glb = {
        "st": st,
        "_draft_state_keys": _draft_state_keys,
        "refresh_with_toast": toasts.refresh_with_toast,
    }
    exec(code, glb)
    return glb["back_step"], st


def test_back_step_clears_chat_state():
    back_step, st = _load_back_step()
    ss = st.session_state
    ss.update({
        'falowen_stage': 4,
        'falowen_mode': 'mode',
        'falowen_level': 'A1',
        'falowen_teil': 'T1',
        'falowen_exam_topic': 'topic',
        'falowen_exam_keyword': 'key',
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

    for key in [
        'falowen_mode', 'falowen_level', 'falowen_teil',
        'falowen_exam_topic', 'falowen_exam_keyword',
        'falowen_messages',
        'falowen_loaded_key', 'falowen_conv_key',
        'falowen_chat_draft_key', 'custom_topic_intro_done',
        'falowen_turn_count', 'falowen_chat_closed',
        draft_key, *_draft_state_keys(draft_key)
    ]:
        assert key not in ss
