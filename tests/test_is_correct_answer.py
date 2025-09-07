import ast


def _load_is_correct_answer():
    with open("a1sprechen.py", "r", encoding="utf-8") as f:
        src = f.read()
    mod = ast.parse(src)
    funcs = [
        node for node in mod.body
        if isinstance(node, ast.FunctionDef) and node.name == "is_correct_answer"
    ]
    module_ast = ast.Module(body=funcs, type_ignores=[])
    code = compile(module_ast, "a1sprechen.py", "exec")
    glb = {}
    exec(code, glb)
    return glb["is_correct_answer"]


def test_is_correct_answer_handles_case_and_spaces():
    fn = _load_is_correct_answer()
    assert fn(" Hallo ", "hallo")
    assert fn("HALLO", "hallo")
    assert not fn("Tschüss", "hallo")


def test_is_correct_answer_articles_and_similarity():
    fn = _load_is_correct_answer()
    assert fn("the intersection", "intersection")
    assert not fn("roundabout", "intersection")
