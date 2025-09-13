from pathlib import Path

def test_coursebook_discussion_links_present():
    src = Path('a1sprechen.py').read_text(encoding='utf-8')
    assert 'Class Board' in src
    assert 'Class Notes & Q&A' in src
    assert "go_board_{info['chapter']}" in src
    assert "go_qna_{info['chapter']}" in src
