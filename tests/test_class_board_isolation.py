import ast
from datetime import datetime, timezone
from typing import Optional


def load_post_message(dummy_db):
    with open('a1sprechen.py', 'r', encoding='utf-8') as f:
        src = f.read()
    mod = ast.parse(src)
    funcs = [node for node in mod.body if isinstance(node, ast.FunctionDef) and node.name == 'post_message']
    module_ast = ast.Module(body=funcs, type_ignores=[])
    code = compile(module_ast, 'a1sprechen.py', 'exec')
    glb = {'db': dummy_db, '_dt': datetime, '_timezone': timezone, 'Optional': Optional}
    exec(code, glb)
    return glb['post_message']


class DummySnap:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class DummyCollection:
    def __init__(self, storage, path):
        self.storage = storage
        self.path = path

    def document(self, name):
        return DummyDocument(self.storage, self.path + (name,))

    def collection(self, name):
        return DummyCollection(self.storage, self.path + (name,))

    def add(self, data):
        self.storage.setdefault(self.path, []).append(data)

    def stream(self):
        for item in self.storage.get(self.path, []):
            yield DummySnap(item)

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self


class DummyDocument:
    def __init__(self, storage, path):
        self.storage = storage
        self.path = path

    def collection(self, name):
        return DummyCollection(self.storage, self.path + (name,))

    def set(self, data):
        self.storage.setdefault(self.path, []).append(data)


class DummyDB:
    def __init__(self):
        self.storage = {}

    def collection(self, name):
        return DummyCollection(self.storage, (name,))


def test_posts_isolated_by_class():
    db = DummyDB()
    post_message = load_post_message(db)

    post_message('A1', 'ClassA', 'c1', 'Alice', 'Hello')
    post_message('A1', 'ClassB', 'c2', 'Bob', 'Hi')

    coll_a = db.collection('class_board').document('A1').collection('classes').document('ClassA').collection('posts')
    coll_b = db.collection('class_board').document('A1').collection('classes').document('ClassB').collection('posts')

    posts_a = [s.to_dict() for s in coll_a.stream()]
    posts_b = [s.to_dict() for s in coll_b.stream()]

    assert len(posts_a) == 1 and posts_a[0]['student_name'] == 'Alice'
    assert len(posts_b) == 1 and posts_b[0]['student_name'] == 'Bob'
