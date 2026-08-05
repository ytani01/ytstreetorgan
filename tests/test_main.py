from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ytstreetorgan.__main__ import cli
from ytstreetorgan.apps import MidiApp, RollBookApp


@pytest.fixture
def runner():
    return CliRunner()

def test_cli_help(runner):
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Usage: cli" in result.output

@patch('ytstreetorgan.__main__.WebServer')
def test_webapp_command(mock_webserver, runner):
    mock_instance = mock_webserver.return_value
    result = runner.invoke(cli, ['webapp', '--port', '8080'])
    assert result.exit_code == 0
    mock_webserver.assert_called_once()
    mock_instance.main.assert_called_once()

@patch('ytstreetorgan.__main__.RollBookApp')
def test_rollbook_command(mock_rollbookapp, runner, tmp_path):
    mock_instance = mock_rollbookapp.return_value
    midi_file = tmp_path / "test.mid"
    midi_file.write_bytes(b"")
    result = runner.invoke(cli, ['rollbook', str(midi_file)])
    assert result.exit_code == 0
    mock_rollbookapp.assert_called_once()
    mock_instance.main.assert_called_once()
    mock_instance.end.assert_called_once()

@patch('ytstreetorgan.__main__.MidiApp')
def test_parse_command(mock_midiapp, runner, tmp_path):
    mock_instance = mock_midiapp.return_value
    midi_file = tmp_path / "test.mid"
    midi_file.write_bytes(b"")
    result = runner.invoke(cli, ['parse', str(midi_file)])
    assert result.exit_code == 0
    mock_midiapp.assert_called_once()
    mock_instance.main.assert_called_once()
    mock_instance.end.assert_called_once()

@patch('ytstreetorgan.__main__.MidiApp')
def test_play_command(mock_midiapp, runner, tmp_path):
    mock_instance = mock_midiapp.return_value
    midi_file = tmp_path / "test.mid"
    midi_file.write_bytes(b"")
    result = runner.invoke(cli, ['play', str(midi_file)])
    assert result.exit_code == 0
    mock_midiapp.assert_called_once()
    mock_instance.main.assert_called_once()
    mock_instance.end.assert_called_once()

@patch('ytstreetorgan.apps.RollBook')
def test_rollbook_app_class(mock_rollbook, tmp_path):
    midi_file = str(tmp_path / "test.mid")
    app = RollBookApp(midi_file, "conf.json", "test_model")
    app._out_file = str(tmp_path / "out.svg")

    mock_instance = mock_rollbook.return_value

    # parse_to_file writes the file, so simulate it
    def fake_parse_to_file(midi_file, out_file, channel=None):
        if channel is None:
            channel = []
        Path(out_file).write_text('<svg></svg>')
        return '<svg></svg>'

    mock_instance.parse_to_file.side_effect = fake_parse_to_file

    # main() は生成後に移調の候補を表にして出す（TODO-039）ので、
    # そこで読む値も持たせる（MagicMock のままだと書式指定で落ちる）
    mock_instance.transpose = 0
    mock_instance.hole_note_count = 1
    mock_instance.note_count = 1
    mock_instance.candidates = []

    app.main()
    app.end()

    assert (tmp_path / "out.svg").exists()

@patch('ytstreetorgan.apps.Parser')
@patch('ytstreetorgan.apps.Player')
def test_midi_app_class(mock_player, mock_parser, tmp_path):
    midi_file = str(tmp_path / "test.mid")
    app = MidiApp(midi_file, channel=[1])

    mock_parser_instance = mock_parser.return_value
    mock_parser_instance.parse.return_value = {
        'note_info': ['note1'],
        'channel_set': {1}
    }

    app.main()
    app.end()

    mock_parser_instance.parse.assert_called_once()
    mock_player.return_value.play.assert_called_once()


@patch('ytstreetorgan.apps.Parser')
@patch('ytstreetorgan.apps.Player')
def test_midi_app_converts_for_model(mock_player, mock_parser, tmp_path):
    """`-m` 指定時は、機種の音階に無い音を再生前に取り除く。"""
    from ytmidilib import NoteInfo

    midi_file = str(tmp_path / "test.mid")
    app = MidiApp(midi_file, model_name='34notes')

    # base_note=41, offset=0 -> 41 は音階にある。40 は無い
    on_scale = NoteInfo(abs_time=0.0, channel=0, note=41,
                        velocity=100, end_time=1.0)
    off_scale = NoteInfo(abs_time=0.0, channel=0, note=40,
                         velocity=100, end_time=1.0)

    mock_parser_instance = mock_parser.return_value
    mock_parser_instance.parse.return_value = {
        'note_info': [on_scale, off_scale],
        'channel_set': {0}
    }

    app.main()
    app.end()

    played = mock_player.return_value.play.call_args[0][0]
    assert played['note_info'] == [on_scale]


def test_midi_app_unknown_model_raises(tmp_path):
    midi_file = str(tmp_path / "test.mid")
    with pytest.raises(ValueError):
        MidiApp(midi_file, model_name='no-such-model')


@patch('ytstreetorgan.apps.Parser')
@patch('ytstreetorgan.apps.Player')
def test_midi_app_merges_overlapping_same_note(mock_player, mock_parser, tmp_path):
    """`-m` 指定時は、同じ音の重なりも 1 つにまとめてから再生する（TODO-038）。

    実機は 1 つの音に 1 本のパイプしか無く、複数パートが同じ高さを
    同時に鳴らしても鳴るのは 1 本だけになるため。
    """
    from ytmidilib import NoteInfo

    midi_file = str(tmp_path / "test.mid")
    app = MidiApp(midi_file, model_name='34notes')

    # base_note=41, offset=0 -> 41 は音階にある。2 つのパートが重ねて鳴らす
    a = NoteInfo(abs_time=0.0, channel=0, note=41, velocity=60, end_time=1.5)
    b = NoteInfo(abs_time=0.5, channel=1, note=41, velocity=100, end_time=1.0)

    mock_parser_instance = mock_parser.return_value
    mock_parser_instance.parse.return_value = {
        'note_info': [a, b],
        'channel_set': {0, 1}
    }

    app.main()
    app.end()

    played = mock_player.return_value.play.call_args[0][0]
    assert len(played['note_info']) == 1
    merged = played['note_info'][0]
    assert merged.abs_time == 0.0
    assert merged.end_time == 1.5
    assert merged.velocity == 100
