from auth_helpers import (
    create_cookie_manager,
    bootstrap_cookies,
    restore_session_from_cookies,
    handle_login_success,
)

cm = create_cookie_manager()   # or your real CookieManager
cm = bootstrap_cookies(cm)

logged_in = restore_session_from_cookies(cm)

if not logged_in:
    # show login form
    code = st.text_input("Student code")
    if st.button("Login"):
        # TODO: validate code...
        handle_login_success(cm, code)
        st.experimental_rerun()
else:
    # show the actual Falowen app
    st.write("Welcome,", st.session_state["student_code"])
