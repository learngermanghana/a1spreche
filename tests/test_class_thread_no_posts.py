from src.discussion_board import go_class_thread


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
    def stream(self):
        for item in self.storage.get(self.path, []):
            yield DummySnap(item)

class DummyDocument:
    def __init__(self, storage, path):
        self.storage = storage
        self.path = path
    def collection(self, name):
        return DummyCollection(self.storage, self.path + (name,))
    def document(self, name):
        return DummyDocument(self.storage, self.path + (name,))
    def set(self, data):
        parent = self.path[:-1]
        self.storage.setdefault(parent, []).append(data)

class DummyDB:
    def __init__(self):
        self.storage = {}
    def collection(self, name):
        return DummyCollection(self.storage, (name,))

class DummyStreamlit:
    def __init__(self):
        self.session_state = {}
        self.query_params = {}
        self.warnings = []

    def warning(self, message):
        self.warnings.append(message)



def setup_env(posts=None):
    db = DummyDB()
    if posts:
        base = db.collection("class_board").document("A1").collection("classes").document("ClassA").collection("posts")
        for pid, data in posts.items():
            base.document(pid).set(data)
    st = DummyStreamlit()
    st.session_state.update(
        {
            "student_level": "A1",
            "student_row": {
                "ClassName": "ClassA",
                "Email": "classa@example.com",
            },
        }
    )
    go_class_thread.__globals__["st"] = st
    fn = go_class_thread
    return fn, st, db


def test_go_class_thread_clears_search_when_no_posts():
    fn, st, db = setup_env()
    fn("9", db=db)
    assert st.session_state.get("q_search") == ""
    assert "q_search_warning" in st.session_state
    assert st.session_state.get("q_search_count") == 0
    assert st.session_state.get("coursebook_subtab") == "🧑‍🏫 Classroom"
    assert st.session_state.get("classroom_page") == "Class Notes & Q&A"


def test_go_class_thread_keeps_search_when_posts_exist():
    posts = {
        "p1": {"lesson": "Day 1: Topic", "topic": "9", "content": ""},
        "p2": {"lesson": "Day 2: Other", "topic": "8", "content": ""},
    }
    fn, st, db = setup_env(posts)
    fn("9", db=db)
    assert st.session_state.get("q_search") == "9"
    assert "q_search_warning" not in st.session_state
    assert st.session_state.get("q_search_count") == 1
    assert st.session_state.get("coursebook_subtab") == "🧑‍🏫 Classroom"
    assert st.session_state.get("classroom_page") == "Class Notes & Q&A"


def test_go_class_thread_warns_when_db_missing():
    fn, st, db = setup_env()
    original_get_db = fn.__globals__["get_db"]
    fn.__globals__["get_db"] = lambda: None
    try:
        fn("9", db=None)
    finally:
        fn.__globals__["get_db"] = original_get_db

    assert st.session_state.get("class_discussion_warning") is True
    assert st.warnings[-1].startswith("Class discussion database is currently unavailable")
