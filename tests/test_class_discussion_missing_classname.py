import ast
from pathlib import Path


def test_class_discussion_skips_without_classname():
    src = Path("a1sprechen.py").read_text(encoding="utf-8")
    lines = src.splitlines()
    target = next(
        i + 1 for i, line in enumerate(lines) if "Class discussion count & link" in line
    )
    tree = ast.parse(src)

    class Finder(ast.NodeVisitor):
        def __init__(self, start_line):
            self.start_line = start_line
            self.node = None

        def visit_If(self, node):
            if node.lineno > self.start_line and self.node is None:
                self.node = node
            self.generic_visit(node)

    finder = Finder(target)
    finder.visit(tree)
    node = finder.node
    assert node is not None, "Class discussion condition not found"

    # First branch should require class_name and chapter
    assert isinstance(node.test, ast.BoolOp)
    assert isinstance(node.test.op, ast.And)
    names = {v.id for v in node.test.values if isinstance(v, ast.Name)}
    assert {"class_name", "chapter"} <= names

    # Ensure button exists in first branch
    has_button = any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "button"
        for n in ast.walk(ast.Module(body=node.body, type_ignores=[]))
    )
    assert has_button, "Discussion button missing from main branch"

    # Elif branch handles missing class_name
    assert node.orelse
    elif_node = node.orelse[0]
    assert isinstance(elif_node, ast.If)
    assert isinstance(elif_node.test, ast.UnaryOp) and isinstance(elif_node.test.op, ast.Not)
    assert isinstance(elif_node.test.operand, ast.Name) and elif_node.test.operand.id == "class_name"

    # Ensure no button but info message containing guidance
    info_msgs = [
        arg.value
        for n in ast.walk(ast.Module(body=elif_node.body, type_ignores=[]))
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "info"
        for arg in n.args
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
    ]
    assert info_msgs, "Missing info message when class_name absent"
    assert any("contact support" in msg for msg in info_msgs)
    assert not any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "button"
        for n in ast.walk(ast.Module(body=elif_node.body, type_ignores=[]))
    ), "Button should not appear when class name is missing"
