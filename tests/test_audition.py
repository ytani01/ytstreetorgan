"""試聴用の MIDI（TODO-063）。

**実機で鳴る音だけ**を集めたもの。移調 → 重なりの統合 → 音階での
絞り込みを経ているので、元のファイルからは音が消える（持ち帰る MIDI
とは別物）。ここでは「消えるべきものが消えているか」を見る。
"""
import io
import tempfile
from pathlib import Path

import mido
import pytest

from ytstreetorgan.audition import playable_midi_bytes
from ytstreetorgan.conf import Conf
from ytstreetorgan.rollbook import RollBook
from ytstreetorgan.transpose import playable_notes

from .conftest import TEST_URL_PREFIX
from .webapp_base import SAMPLE_MIDI, WebAppTestCase

MODEL = '34notes'

URL = f'{TEST_URL_PREFIX}/audition/midi'


def note_ons(data: bytes) -> list[int]:
    """MIDI のバイト列から、鳴り始める音を順に取り出す。"""
    mid = mido.MidiFile(file=io.BytesIO(data))
    return [
        msg.note for track in mid.tracks for msg in track
        if msg.type == 'note_on' and msg.velocity > 0
    ]


def channels_of(data: bytes) -> set[int]:
    """音符のメッセージが使っているチャンネル。"""
    mid = mido.MidiFile(file=io.BytesIO(data))
    return {
        msg.channel for track in mid.tracks for msg in track
        if msg.type in ('note_on', 'note_off')
    }


def notes_sec(data: bytes) -> list[tuple[int, float, float]]:
    """音符を ``(MIDI ノート番号, 開始秒, 終了秒)`` の並びにする。"""
    result: list[tuple[int, float, float]] = []
    started: dict[int, float] = {}
    now = 0.0

    # mido の反復は delta を秒で返す（テンポを見てくれる）
    for msg in mido.MidiFile(file=io.BytesIO(data)):
        now += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            started[msg.note] = now
        elif msg.type == 'note_off' or (
            msg.type == 'note_on' and msg.velocity == 0
        ):
            if msg.note in started:
                result.append((msg.note, started.pop(msg.note), now))

    return result


def make_midi(path: Path, notes: list[tuple[int, int, int, int]]) -> Path:
    """``(MIDI ノート番号, チャンネル, 開始 tick, 終了 tick)`` から MIDI を作る。

    音ごとにトラックを分ける（同じ高さの重なりを作りやすくするため）。
    """
    mid = mido.MidiFile()
    for note, channel, start, end in notes:
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.Message(
            'note_on', note=note, channel=channel, velocity=100, time=start
        ))
        track.append(mido.Message(
            'note_off', note=note, channel=channel, velocity=0,
            time=end - start
        ))
    mid.save(path)
    return path


def test_off_scale_notes_are_dropped():
    """機種の音階に無い音は入らない（破線で描くだけの音）。"""
    conf = Conf(RollBook.DEF_CONF_FILE).get(MODEL)
    playable = playable_notes(conf)

    book = RollBook(MODEL)
    book.parse(SAMPLE_MIDI)

    # 元の曲に音階外の音が無いと、この検査は何も確かめていないことになる
    assert book.off_scale_note_count > 0

    data = playable_midi_bytes(SAMPLE_MIDI, MODEL)

    assert set(note_ons(data)) <= playable


def test_transpose_shifts_notes(tmp_path: Path):
    """移調が効く（移調してから音階で絞り込む）。

    60 / 62 / 64 は '34notes' の音階にあり、+2 した 62 / 64 / 66 も
    音階にある。どちらも消えないので、差は移調のぶんだけになる。
    """
    src = make_midi(tmp_path / 'scale.mid', [
        (60, 0, 0, 480), (62, 0, 480, 960), (64, 0, 960, 1440),
    ])

    assert note_ons(playable_midi_bytes(src, MODEL, 0)) == [60, 62, 64]
    assert note_ons(playable_midi_bytes(src, MODEL, 2)) == [62, 64, 66]


def test_note_count_matches_hole_note_count():
    """音符の数は、実線で描く穴（`hole_note_count`）と一致する。"""
    book = RollBook(MODEL)
    book.parse(SAMPLE_MIDI)

    data = playable_midi_bytes(SAMPLE_MIDI, MODEL)

    assert len(note_ons(data)) == book.hole_note_count


def test_overlapping_notes_are_merged(tmp_path: Path):
    """同じ高さの重なりは 1 つの長い音になる（TODO-038）。

    実機は 1 音に 1 本のパイプしか無いので、これは再現であって不具合
    ではない。0.00〜0.50 秒と 0.25〜0.75 秒が 0.00〜0.75 秒になる。
    """
    src = make_midi(tmp_path / 'overlap.mid', [
        (60, 0, 0, 480), (60, 1, 240, 720),
    ])

    data = playable_midi_bytes(src, MODEL)
    notes = notes_sec(data)

    assert len(notes) == 1
    note, start, end = notes[0]
    assert note == 60
    assert start == pytest.approx(0.0, abs=0.02)
    assert end == pytest.approx(0.75, abs=0.02)


def test_channel_is_always_zero(tmp_path: Path):
    """チャンネルは全部 0 に揃える。

    ブラウザ側の再生に使う Magenta は channel 9 をドラムとして扱うので、
    揃えないと穴の音がキックドラムで鳴る。
    """
    src = make_midi(tmp_path / 'ch.mid', [
        (60, 9, 0, 480), (62, 5, 480, 960),
    ])

    assert channels_of(playable_midi_bytes(src, MODEL)) == {0}


def test_nothing_is_stored(tmp_path: Path):
    """作った MIDI もその途中のものも残さない。"""
    src = make_midi(tmp_path / 'keep.mid', [(60, 0, 0, 480)])
    before = sorted(p.name for p in tmp_path.iterdir())

    playable_midi_bytes(src, MODEL)

    assert sorted(p.name for p in tmp_path.iterdir()) == before
    # 一時ディレクトリ経由で書いているので、そちらも消えていること
    assert not list(Path(tempfile.gettempdir()).glob('storgan-audition-*'))


def test_unknown_model_is_value_error():
    with pytest.raises(ValueError):
        playable_midi_bytes(SAMPLE_MIDI, 'no-such-model')


class TestAuditionMidi(WebAppTestCase):
    """`/audition/midi/<name>?t=<半音数>&model=<機種名>`（TODO-063）。"""

    PORT = 10089

    def setup_files(self):
        self.put_midi('sample.mid')

    def test_returns_midi(self):
        response = self.fetch(f'{URL}/sample.mid?t=0&model={MODEL}')

        assert response.code == 200
        assert response.headers['Content-Type'] == 'audio/midi'
        # SMF の先頭 4 バイト
        assert response.body[:4] == b'MThd'

    def test_no_content_disposition(self):
        """試聴のためのものなので、持ち帰らせない。"""
        response = self.fetch(f'{URL}/sample.mid?t=0&model={MODEL}')

        assert 'Content-Disposition' not in response.headers

    def test_nothing_is_stored(self):
        before = self.names('midi')

        self.fetch(f'{URL}/sample.mid?t=3&model={MODEL}')

        assert self.names('midi') == before
        assert self.names('svg') == []

    def test_bad_transpose_is_400(self):
        assert self.fetch(f'{URL}/sample.mid?t=abc&model={MODEL}').code == 400
        assert self.fetch(f'{URL}/sample.mid?t=1.5&model={MODEL}').code == 400
        assert self.fetch(f'{URL}/sample.mid?model={MODEL}').code == 400

    def test_unknown_model_is_400(self):
        assert self.fetch(f'{URL}/sample.mid?t=0&model=nope').code == 400
        assert self.fetch(f'{URL}/sample.mid?t=0').code == 400

    def test_bad_name_is_400(self):
        # 素の '..' はクライアント側で畳まれて別のハンドラに届くので、
        # このハンドラに '..' を渡すには符号化しておく
        assert self.fetch(
            f'{URL}/%2e%2e%2fx.mid?t=0&model={MODEL}'
        ).code == 400
        assert self.fetch(f'{URL}/sub%2fx.mid?t=0&model={MODEL}').code == 400

    def test_missing_file_is_404(self):
        assert self.fetch(f'{URL}/nope.mid?t=0&model={MODEL}').code == 404

    def test_unreadable_midi_is_400(self):
        (self.webroot / 'midi' / 'broken.mid').write_bytes(b'not midi')

        assert self.fetch(f'{URL}/broken.mid?t=0&model={MODEL}').code == 400
