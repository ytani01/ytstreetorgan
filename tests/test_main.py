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
        with open(out_file, 'w') as f:
            f.write('<svg></svg>')
        return '<svg></svg>'

    mock_instance.parse_to_file.side_effect = fake_parse_to_file

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
