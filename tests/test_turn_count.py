import ast
from types import SimpleNamespace


def _load_increment_fn():
    with open('a1sprechen.py', 'r', encoding='utf-8') as f:
        src = f.read()
    mod = ast.parse(src)
    wanted = []
    target_names = {
        'increment_turn_count_and_maybe_close',
        'reset_falowen_chat_flow',
    }
    for node in mod.body:
        if isinstance(node, ast.FunctionDef) and node.name in target_names:
            wanted.append(node)
    module_ast = ast.Module(body=wanted, type_ignores=[])
    code = compile(module_ast, 'a1sprechen.py', 'exec')
    st = SimpleNamespace(session_state={})

    def dummy_summary(msgs):
        dummy_summary.called_with = msgs
        return 'SUMMARY'

    glb = {'st': st, 'generate_summary': dummy_summary}
    exec(code, glb)
    return (
        glb['increment_turn_count_and_maybe_close'],
        dummy_summary,
        st,
        glb['reset_falowen_chat_flow'],
    )


def test_increment_and_finalize_after_six():
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
    assert ss['falowen_messages'][-1]['content'] == 'SUMMARY'
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
    assert not hasattr(dummy, 'called_with')


def test_no_increment_in_exam_mode():
    inc, dummy, st, _ = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 4
    ss['falowen_messages'] = []
    ended = inc(True)
    assert ended is False
    assert ss['falowen_turn_count'] == 4
    assert ss['falowen_messages'] == []
    assert not hasattr(dummy, 'called_with')


def test_new_chat_reset_unlocks_after_limit():
    inc, dummy, st, reset_chat = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 6
    ss['falowen_messages'] = [{'role': 'user', 'content': 'Hallo'}]
    ss['custom_topic_intro_done'] = True

    chat_locked = (not False) and ss.get('falowen_turn_count', 0) >= 6
    assert chat_locked is True

    reset_chat()

    assert ss['falowen_turn_count'] == 0
    assert ss['falowen_messages'] == []
    assert ss['custom_topic_intro_done'] is False
    chat_locked = (not False) and ss.get('falowen_turn_count', 0) >= 6
    assert chat_locked is False
