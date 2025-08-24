from src.firestore_utils import _extract_level_and_lesson


def test_extract_level_and_lesson_with_prefix():
    level, lesson = _extract_level_and_lesson("draft_B2_day5_ch3")
    assert level == "B2"
    assert lesson == "B2_day5_ch3"


def test_extract_level_and_lesson_without_prefix():
    level, lesson = _extract_level_and_lesson("C1_day2_ch1")
    assert level == "C1"
    assert lesson == "C1_day2_ch1"
