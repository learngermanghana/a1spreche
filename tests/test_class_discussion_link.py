import ast
from pathlib import Path


def test_lesson_includes_class_discussion_button():
    src = Path("a1sprechen.py").read_text(encoding="utf-8")
    assert "CLASS_DISCUSSION_LABEL" in src
    assert "CLASS_DISCUSSION_ANCHOR" in src
    tree = ast.parse(src)
    found = False

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node):
            nonlocal found
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "button"
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "CLASS_DISCUSSION_LABEL"
            ):
                on_click = next((kw.value for kw in node.keywords if kw.arg == "on_click"), None)
                args_kw = next((kw.value for kw in node.keywords if kw.arg == "args"), None)
                if (
                    isinstance(on_click, ast.Name)
                    and on_click.id == "_go_class_thread"
                    and isinstance(args_kw, ast.Tuple)
                    and len(args_kw.elts) == 1
                ):
                    arg = args_kw.elts[0]
                    if isinstance(arg, ast.Name) and arg.id == "chapter":
                        found = True
            self.generic_visit(node)

    Visitor().visit(tree)
    assert found, "Class discussion button missing or has wrong arguments"
