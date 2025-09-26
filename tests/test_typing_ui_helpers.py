import ast
import math
from typing import Any, Dict, List


class TimeStub:
    def __init__(self, start: float = 1000.0):
        self._now = start

    def time(self) -> float:
        return self._now

    def advance(self, delta: float) -> None:
        self._now += delta


class StreamlitStub:
    def __init__(self):
        self.session_state: Dict[str, Any] = {}


def load_typing_helpers(stub_st, indicator_func, time_stub):
    with open("a1sprechen.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename="a1sprechen.py")

    wanted_funcs = {
        "_safe_str",
        "_typing_meta_key",
        "_update_typing_state",
        "_clear_typing_state",
        "_format_typing_banner",
    }
    wanted_assigns = {"_TYPING_TRACKER_PREFIX", "_TYPING_PING_INTERVAL"}
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id in wanted_assigns
                for target in node.targets
            ):
                selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in wanted_funcs:
            selected.append(node)

    module = ast.Module(body=selected, type_ignores=[])
    glb: Dict[str, Any] = {
        "st": stub_st,
        "time": time_stub,
        "set_typing_indicator": indicator_func,
        "math": math,
        "Any": Any,
        "Dict": Dict,
        "List": List,
    }
    exec(compile(module, "a1sprechen.py", "exec"), glb)
    return glb


def test_update_typing_state_is_throttled():
    indicator_calls: List[Dict[str, Any]] = []

    def indicator(*args, **kwargs):
        indicator_calls.append({"is_typing": kwargs.get("is_typing")})
        return True

    st = StreamlitStub()
    time_stub = TimeStub()
    helpers = load_typing_helpers(st, indicator, time_stub)
    update = helpers["_update_typing_state"]
    clear = helpers["_clear_typing_state"]
    meta_key = helpers["_typing_meta_key"]("draft1")

    update(
        level="A1",
        class_code="C1",
        qid="q1",
        draft_key="draft1",
        student_code="stu",
        student_name="Student",
        text="Hallo",
    )
    assert indicator_calls and indicator_calls[0]["is_typing"] is True
    assert st.session_state[meta_key]["is_typing"] is True

    update(
        level="A1",
        class_code="C1",
        qid="q1",
        draft_key="draft1",
        student_code="stu",
        student_name="Student",
        text="Hallo",
    )
    assert len(indicator_calls) == 1

    time_stub.advance(5.0)
    update(
        level="A1",
        class_code="C1",
        qid="q1",
        draft_key="draft1",
        student_code="stu",
        student_name="Student",
        text="Hallo",
    )
    assert len(indicator_calls) == 2
    assert indicator_calls[-1]["is_typing"] is True

    update(
        level="A1",
        class_code="C1",
        qid="q1",
        draft_key="draft1",
        student_code="stu",
        student_name="Student",
        text="",
    )
    assert indicator_calls[-1]["is_typing"] is False
    assert st.session_state[meta_key]["is_typing"] is False

    clear(
        level="A1",
        class_code="C1",
        qid="q1",
        draft_key="draft1",
        student_code="stu",
        student_name="Student",
    )
    assert indicator_calls[-1]["is_typing"] is False
    assert meta_key not in st.session_state


def test_format_typing_banner_humanises_names():
    st = StreamlitStub()
    time_stub = TimeStub()
    indicators: List[Dict[str, Any]] = []
    helpers = load_typing_helpers(st, lambda **kwargs: indicators.append(kwargs), time_stub)
    format_banner = helpers["_format_typing_banner"]

    banner_single = format_banner(
        [{"student_code": "abc", "student_name": "Alice"}],
        current_code="xyz",
    )
    assert banner_single == "Alice is typing…"

    banner_multi = format_banner(
        [
            {"student_code": "self", "student_name": "Self"},
            {"student_code": "b", "student_name": "Bob"},
            {"student_code": "c", "student_name": ""},
        ],
        current_code="self",
    )
    assert banner_multi == "Bob and c are typing…"


def test_update_typing_state_supports_edit_draft_keys():
    indicator_calls: List[Dict[str, Any]] = []

    def indicator(*args, **kwargs):
        indicator_calls.append(dict(kwargs))
        return True

    st = StreamlitStub()
    time_stub = TimeStub()
    helpers = load_typing_helpers(st, indicator, time_stub)
    update = helpers["_update_typing_state"]
    clear = helpers["_clear_typing_state"]
    meta_key_post = helpers["_typing_meta_key"]("q_edit_text_post42")
    meta_key_comment = helpers["_typing_meta_key"]("c_edit_text_post42_c99")

    update(
        level="A1",
        class_code="C1",
        qid="post42",
        draft_key="q_edit_text_post42",
        student_code="stu",
        student_name="Student",
        text="Hallo",
    )
    assert indicator_calls[-1]["is_typing"] is True
    assert st.session_state[meta_key_post]["is_typing"] is True

    update(
        level="A1",
        class_code="C1",
        qid="post42",
        draft_key="c_edit_text_post42_c99",
        student_code="stu",
        student_name="Student",
        text="Antwort",
    )
    assert indicator_calls[-1]["is_typing"] is True
    assert st.session_state[meta_key_comment]["is_typing"] is True

    update(
        level="A1",
        class_code="C1",
        qid="post42",
        draft_key="q_edit_text_post42",
        student_code="stu",
        student_name="Student",
        text="",
    )
    assert indicator_calls[-1]["is_typing"] is False
    assert st.session_state[meta_key_post]["is_typing"] is False

    clear(
        level="A1",
        class_code="C1",
        qid="post42",
        draft_key="c_edit_text_post42_c99",
        student_code="stu",
        student_name="Student",
    )
    assert indicator_calls[-1]["is_typing"] is False
    assert meta_key_comment not in st.session_state
