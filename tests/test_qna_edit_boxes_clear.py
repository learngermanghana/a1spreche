def render_question_editor(st, q_id):
    clear_flag = f"__clear_q_edit_{q_id}"
    if st.session_state.pop(clear_flag, False):
        for _k in [
            f"q_edit_text_{q_id}",
            f"q_edit_topic_{q_id}",
            f"q_edit_link_{q_id}",
            f"q_edit_text_input_{q_id}",
            f"q_edit_topic_input_{q_id}",
            f"q_edit_link_input_{q_id}",
        ]:
            st.session_state.pop(_k, None)
    if st.session_state.get(f"q_editing_{q_id}", False):
        st.text_input(
            "Edit topic (optional)",
            key=f"q_edit_topic_input_{q_id}",
            value=st.session_state.get(f"q_edit_topic_{q_id}", ""),
        )
        st.text_input(
            "Edit link (optional)",
            key=f"q_edit_link_input_{q_id}",
            value=st.session_state.get(f"q_edit_link_{q_id}", ""),
        )
        st.text_area(
            "Edit post",
            key=f"q_edit_text_input_{q_id}",
            value=st.session_state.get(f"q_edit_text_{q_id}", ""),
        )

def render_comment_editor(st, q_id, cid):
    clear_flag = f"__clear_c_edit_{q_id}_{cid}"
    if st.session_state.pop(clear_flag, False):
        for _k in [
            f"c_edit_text_{q_id}_{cid}",
            f"c_edit_text_input_{q_id}_{cid}",
        ]:
            st.session_state.pop(_k, None)
    if st.session_state.get(f"c_editing_{q_id}_{cid}", False):
        st.text_area(
            "Edit comment",
            key=f"c_edit_text_input_{q_id}_{cid}",
            value=st.session_state.get(f"c_edit_text_{q_id}_{cid}", ""),
        )


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
                raise DummyStreamlit.StreamlitAPIException("locked")
            super().__setitem__(key, value)

    def text_input(self, label, value="", key=None):
        self.session_state[key] = value
        self.locked.add(key)
        return value

    def text_area(self, label, value="", key=None, **kwargs):
        self.session_state[key] = value
        self.locked.add(key)
        return value


def test_question_edit_box_clears():
    st = DummyStreamlit()
    q_id = "q1"
    st.session_state[f"q_editing_{q_id}"] = True
    st.session_state[f"q_edit_text_{q_id}"] = "old"
    st.session_state[f"q_edit_topic_{q_id}"] = "t"
    st.session_state[f"q_edit_link_{q_id}"] = "l"
    render_question_editor(st, q_id)
    st.session_state[f"q_editing_{q_id}"] = False
    st.session_state[f"__clear_q_edit_{q_id}"] = True
    st.locked.clear()
    try:
        render_question_editor(st, q_id)
    except DummyStreamlit.StreamlitAPIException as err:
        raise AssertionError("StreamlitAPIException should not be raised") from err
    keys = [
        f"q_edit_text_{q_id}",
        f"q_edit_topic_{q_id}",
        f"q_edit_link_{q_id}",
        f"q_edit_text_input_{q_id}",
        f"q_edit_topic_input_{q_id}",
        f"q_edit_link_input_{q_id}",
    ]
    assert all(k not in st.session_state for k in keys)


def test_comment_edit_box_clears():
    st = DummyStreamlit()
    q_id, cid = "q1", "c1"
    st.session_state[f"c_editing_{q_id}_{cid}"] = True
    st.session_state[f"c_edit_text_{q_id}_{cid}"] = "old"
    render_comment_editor(st, q_id, cid)
    st.session_state[f"c_editing_{q_id}_{cid}"] = False
    st.session_state[f"__clear_c_edit_{q_id}_{cid}"] = True
    st.locked.clear()
    try:
        render_comment_editor(st, q_id, cid)
    except DummyStreamlit.StreamlitAPIException as err:
        raise AssertionError("StreamlitAPIException should not be raised") from err
    keys = [
        f"c_edit_text_{q_id}_{cid}",
        f"c_edit_text_input_{q_id}_{cid}",
    ]
    assert all(k not in st.session_state for k in keys)
