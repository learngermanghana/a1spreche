import ast
import math
from pathlib import Path
from typing import Any, Dict, Iterable, MutableMapping, Tuple


def _load_topic_coach_initialiser():
    source = Path("a1sprechen.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="a1sprechen.py")
    targets = {
        "_safe_str",
        "_topic_coach_state_key",
        "_initialise_topic_coach_session_state",
    }
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in targets]
    module = ast.Module(body=funcs, type_ignores=[])
    namespace = {
        "Any": Any,
        "Dict": Dict,
        "Iterable": Iterable,
        "MutableMapping": MutableMapping,
        "Tuple": Tuple,
        "math": math,
    }
    exec(compile(module, "a1sprechen.py", "exec"), namespace)
    return (
        namespace["_initialise_topic_coach_session_state"],
        namespace["_topic_coach_state_key"],
    )


def test_topic_coach_state_isolated_between_students():
    initialise_state, make_key = _load_topic_coach_initialiser()
    session_state = {}

    first_messages = [{"role": "assistant", "content": "Hallo"}]
    chat_key1, qcount_key1, finalized_key1 = initialise_state(
        session_state,
        student_code="stu1",
        level="A1",
        messages=first_messages,
        qcount=3,
        finalized=True,
    )

    assert chat_key1 == make_key("cchat_data_chat", "stu1", "A1")
    assert session_state[chat_key1] == first_messages
    assert session_state[qcount_key1] == 3
    assert session_state[finalized_key1] is True
    assert session_state["_cchat_active_identity"] == ("stu1", "A1")
    assert "cchat_data_chat" not in session_state

    chat_key2, qcount_key2, finalized_key2 = initialise_state(
        session_state,
        student_code="stu2",
        level="A1",
        messages=[],
        qcount=0,
        finalized=False,
    )

    assert chat_key2 == make_key("cchat_data_chat", "stu2", "A1")
    assert session_state[chat_key2] == []
    assert session_state[qcount_key2] == 0
    assert session_state[finalized_key2] is False
    assert session_state["_cchat_active_identity"] == ("stu2", "A1")
    assert session_state[chat_key1] == first_messages
    assert session_state[qcount_key1] == 3
