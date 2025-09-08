import ast
import time
from datetime import datetime, timezone


def load_send_comment(stub_st):
    with open('a1sprechen.py', 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    func_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'send_comment':
            func_node = node
            break
    mod = ast.Module(body=[func_node], type_ignores=[])
    glb = {
        'st': stub_st,
        'save_draft_to_db': lambda *a, **k: None,
        '_notify_slack': lambda *a, **k: None,
        '_dt': datetime,
        '_timezone': timezone,
        'uuid4': lambda: 'abcd1234',
        'time': time,
        'refresh_with_toast': lambda *a, **k: None,
    }
    exec(compile(mod, 'a1sprechen.py', 'exec'), glb)
    return glb['send_comment']


class DummyStreamlit:
    class StreamlitAPIException(Exception):
        pass

    def __init__(self):
        self.locked = set()
        self.session_state = self.SessionState(self)

    class SessionState(dict):
        def __init__(self, outer):
            super().__init__()
            self._outer = outer

        def __setitem__(self, key, value):
            if key in self._outer.locked:
                raise DummyStreamlit.StreamlitAPIException('locked')
            super().__setitem__(key, value)

    def text_area(self, label, value="", key=None, placeholder="", on_change=None, args=None, height=None):
        self.session_state[key] = value
        self.locked.add(key)
        return value

    def success(self, msg):
        pass


class DummyDoc:
    def collection(self, name):
        return self

    def document(self, name):
        return self

    def set(self, data):
        self.data = data


class DummyBoardBase:
    def __init__(self):
        self.doc = DummyDoc()

    def document(self, q_id):
        return self.doc


def render_comment_box(st, q_id, student_code):
    draft_key = f"classroom_comment_draft_{q_id}"
    clear_key = f"__clear_comment_draft_{q_id}"
    if st.session_state.pop(clear_key, False):
        st.session_state[draft_key] = ""
    current_text = st.session_state.get(draft_key, "")
    st.text_area(
        f"Comment on Q{q_id}",
        value=current_text,
        key=draft_key,
        placeholder="Write your comment…",
    )


def test_comment_submission_clears_box():
    st = DummyStreamlit()
    send_comment = load_send_comment(st)
    board = DummyBoardBase()
    q_id = 'q1'
    draft_key = f'classroom_comment_draft_{q_id}'
    st.session_state[draft_key] = 'hi'
    render_comment_box(st, q_id, 's1')

    try:
        send_comment(
            q_id,
            'code',
            'name',
            'class',
            board,
            draft_key,
            'lv',
            'lt',
            'sf',
            'sa',
        )
    except DummyStreamlit.StreamlitAPIException:
        assert False, 'StreamlitAPIException should not be raised'

    st.locked.clear()
    render_comment_box(st, q_id, 's1')
    assert st.session_state[draft_key] == ''
