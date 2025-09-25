from src.config import get_cookie_manager


def test_get_cookie_manager_importable():
    assert callable(get_cookie_manager)
