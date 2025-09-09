import ast
import types


class DummyStreamlit:
    def __init__(self):
        self.session_state = {}
        self.errors = []

    def error(self, msg):
        self.errors.append(msg)


def load_apply_profile_ai_correction(stub_st, stub_client, api_key="test"):
    with open("a1sprechen.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    func_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "apply_profile_ai_correction":
            func_node = node
            break
    mod = ast.Module(body=[func_node], type_ignores=[])
    glb = {"st": stub_st, "client": stub_client, "OPENAI_API_KEY": api_key}
    exec(compile(mod, "a1sprechen.py", "exec"), glb)
    return glb["apply_profile_ai_correction"]


class DummyClient:
    def __init__(self, reply="Corrected"):
        self.called = False
        self.reply = reply
        self.chat = types.SimpleNamespace(completions=self)

    def create(self, **kwargs):
        self.called = True
        return types.SimpleNamespace(
            choices=[
                types.SimpleNamespace(
                    message=types.SimpleNamespace(content=self.reply),
                    finish_reason="stop",
                )
            ]
        )


def test_profile_ai_button_updates_bio():
    st = DummyStreamlit()
    client = DummyClient("Improved bio")
    fn = load_apply_profile_ai_correction(st, client)
    st.session_state["profile_about"] = "bad bio"

    fn("profile_about")

    assert client.called is True
    assert st.session_state["profile_about"] == "Improved bio"
