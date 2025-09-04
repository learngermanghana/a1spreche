import ast
from types import SimpleNamespace


def _load_increment_fn():
    with open('a1sprechen.py', 'r', encoding='utf-8') as f:
        src = f.read()
    mod = ast.parse(src)
    wanted = []
    for node in mod.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == 'FINAL_FEEDBACK_MESSAGE':
                    wanted.append(node)
        if isinstance(node, ast.FunctionDef) and node.name == 'increment_turn_count_and_maybe_close':
            wanted.append(node)
    module_ast = ast.Module(body=wanted, type_ignores=[])
    code = compile(module_ast, 'a1sprechen.py', 'exec')
    st = SimpleNamespace(session_state={})
    glb = {'st': st}
    exec(code, glb)
    return glb['increment_turn_count_and_maybe_close'], glb['FINAL_FEEDBACK_MESSAGE'], st


def test_increment_and_finalize_after_six():
    inc, final_msg, st = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 5
    ss['falowen_messages'] = []
    ended = inc(False)
    assert ended is True
    assert ss['falowen_turn_count'] == 6
    assert ss['falowen_messages'][-1]['content'] == final_msg


def test_increment_when_below_limit():
    inc, final_msg, st = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 2
    ss['falowen_messages'] = []
    ended = inc(False)
    assert ended is False
    assert ss['falowen_turn_count'] == 3
    assert ss['falowen_messages'] == []


def test_no_increment_in_exam_mode():
    inc, final_msg, st = _load_increment_fn()
    ss = st.session_state
    ss['falowen_turn_count'] = 4
    ss['falowen_messages'] = []
    ended = inc(True)
    assert ended is False
    assert ss['falowen_turn_count'] == 4
    assert ss['falowen_messages'] == []
