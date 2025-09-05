from pathlib import Path

def test_no_cedi_symbol_present():
    text = Path('a1sprechen.py').read_text()
    assert '₵' not in text
