from unittest.mock import MagicMock, patch

from ytstreetorgan.rollbook import HoleInfo, RollBook, note2scale, svg_square


def test_note2scale():
    assert note2scale(60, 60, [0, 2, 4]) == 0
    assert note2scale(62, 60, [0, 2, 4]) == 1
    assert note2scale(65, 60, [0, 2, 4]) == -1

def test_svg_square():
    svg = svg_square(10, 20, 30, 40, '#123456')
    assert 'stroke:#123456' in svg
    assert 'd="M -10.00,-20.00 h -30.00 v -40.00 h 30.00 Z"' in svg

@patch('ytstreetorgan.rollbook.Parser')
def test_rollbook_parse(mock_parser):
    mock_instance = mock_parser.return_value

    # Mock the return value of Parser.parse
    mock_note1 = MagicMock()
    mock_note1.abs_time = 1.0
    mock_note1.length.return_value = 2.0
    mock_note1.note = 60

    mock_note2 = MagicMock()
    mock_note2.abs_time = 2.0
    mock_note2.length.return_value = 1.0
    mock_note2.note = 999  # Invalid note to test scale < 0

    mock_instance.parse.return_value = {
        'channel_set': {1},
        'note_info': [mock_note1, mock_note2]
    }

    rb = RollBook()
    # Mock conf slightly if needed, but defaults might work
    rb._conf = {
        'base note': 60,
        'note offset': [0, 2, 4],
        '1sec': 10,
        'pitch': 5,
        'margin': 2,
        'hole height': 3,
        'book height': 100
    }

    svg = rb.parse('dummy.mid')
    assert '<svg ' in svg
    assert 'viewBox=' in svg
    assert '#FF0000' in svg  # Hole color
    assert '#000000' in svg  # Scale < 0 fallback color

def test_holeinfo_str():
    mock_note = MagicMock()
    mock_note.abs_time = 1.0
    mock_note.length.return_value = 2.0
    mock_note.note = 60

    conf = {
        'base note': 60,
        'note offset': [0, 2, 4],
        '1sec': 10,
        'pitch': 5,
        'margin': 2,
        'hole height': 3
    }
    hi = HoleInfo(mock_note, conf)
    s = str(hi)
    assert 'note:060' in s

import os


def test_rollbook_parse_real_midi():
    # Verify that parse works with a real MIDI file (fixture)
    midi_file = 'webroot/midi/d-kaeru.mid'
    if os.path.exists(midi_file):
        rb = RollBook()
        svg = rb.parse(midi_file)
        assert '<svg ' in svg
        assert '</svg>' in svg
        # There should be some notes parsed
        assert len(rb._holes) > 0
        assert rb._width > 0
