import ast
from pathlib import Path


def test_submit_payload_includes_student_email():
    src = Path("a1sprechen.py").read_text(encoding="utf-8")
    tree = ast.parse(src, filename="a1sprechen.py")

    found_payload = False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "payload" not in targets:
            continue
        if not isinstance(node.value, ast.Dict):
            continue

        keys = []
        for key in node.value.keys:
            if isinstance(key, ast.Constant):
                keys.append(key.value)

        # Identify the submit payload by looking for unique keys
        submit_keys = {"student_code", "student_name", "lesson_key", "receipt"}
        if submit_keys.issubset(set(keys)):
            found_payload = "student_email" in keys
            break

    assert found_payload, "Submit payload must include the student_email field"
