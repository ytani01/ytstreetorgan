"""移調した MIDI のダウンロード（TODO-042）。

元のファイルを移調するだけで、ロールブックの音符（統合・絞り込み済み）は
使わない。**その場で作って返し、`webroot/midi/` には残さない。**
"""
import io
import zipfile
from pathlib import Path

import mido
import pytest

from ytstreetorgan.transpose import (
    transpose_midi_bytes,
    transposed_midi_name,
    transposed_midi_zip_bytes,
    transposed_zip_name,
)

from .conftest import TEST_URL_PREFIX
from .webapp_base import SAMPLE_MIDI, WebAppTestCase

URL = f'{TEST_URL_PREFIX}/download/midi-transpose'
ZIP_URL = f'{TEST_URL_PREFIX}/download/midi-transpose-zip'


def notes_of(data: bytes) -> list[int]:
    """MIDI のバイト列から、`note_on` / `note_off` の音を順に取り出す。"""
    mid = mido.MidiFile(file=io.BytesIO(data))
    return [
        msg.note for track in mid.tracks for msg in track
        if msg.type in ('note_on', 'note_off')
    ]


def tempos_of(data: bytes) -> list[int]:
    """テンポ（`set_tempo`）の値を順に取り出す。"""
    mid = mido.MidiFile(file=io.BytesIO(data))
    return [
        msg.tempo for track in mid.tracks for msg in track
        if msg.type == 'set_tempo'
    ]


class TestTransposeMidiBytes:
    """`transpose_midi_bytes()` そのもの（HTTP を通さない）。"""

    def test_notes_are_shifted(self):
        src = notes_of(SAMPLE_MIDI.read_bytes())
        out = notes_of(transpose_midi_bytes(SAMPLE_MIDI, 3))

        assert out == [n + 3 for n in src]

    def test_zero_keeps_notes(self):
        assert notes_of(transpose_midi_bytes(SAMPLE_MIDI, 0)) == notes_of(
            SAMPLE_MIDI.read_bytes()
        )

    def test_note_is_the_only_change(self):
        """テンポ・トラック数・分解能は変わらない。"""
        src = mido.MidiFile(SAMPLE_MIDI)
        out = mido.MidiFile(file=io.BytesIO(transpose_midi_bytes(
            SAMPLE_MIDI, -5
        )))

        assert len(out.tracks) == len(src.tracks)
        assert out.ticks_per_beat == src.ticks_per_beat
        assert out.type == src.type
        assert tempos_of(transpose_midi_bytes(SAMPLE_MIDI, -5)) == tempos_of(
            SAMPLE_MIDI.read_bytes()
        )

    def test_out_of_range_is_clipped(self, tmp_path: Path):
        """0 .. 127 をはみ出す音は丸める（`ValueError` にしない）。

        候補は元の音域から作っているので実際に外れることはまず無いが、
        そのために持ち帰れなくなるほうが困る。
        """
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.Message('note_on', note=120, velocity=64, time=0))
        track.append(mido.Message('note_off', note=120, velocity=0, time=480))
        track.append(mido.Message('note_on', note=3, velocity=64, time=0))
        track.append(mido.Message('note_off', note=3, velocity=0, time=480))
        src = tmp_path / 'edge.mid'
        mid.save(src)

        assert notes_of(transpose_midi_bytes(src, 10)) == [127, 127, 13, 13]
        assert notes_of(transpose_midi_bytes(src, -10)) == [110, 110, 0, 0]


@pytest.mark.parametrize(('name', 'semitones', 'expected'), [
    ('sample.mid', 3, 'sample.t+3.mid'),
    ('sample.mid', -5, 'sample.t-5.mid'),
    # ±0 の行にもボタンを出す（元のキーのまま MIDI だけ欲しい場合がある）
    ('sample.mid', 0, 'sample.t+0.mid'),
    ('a.b.midi', 1, 'a.b.t+1.mid'),
])
def test_transposed_midi_name(name, semitones, expected):
    assert transposed_midi_name(name, semitones) == expected


def zip_names(data: bytes) -> list[str]:
    """ZIP の中のファイル名を、入っている順に取り出す。"""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.namelist()


class TestTransposedMidiZipBytes:
    """`transposed_midi_zip_bytes()` そのもの（HTTP を通さない）。"""

    def test_names_and_order(self):
        data = transposed_midi_zip_bytes(SAMPLE_MIDI, [-5, 0, 3])

        assert zip_names(data) == [
            'sample.t-5.mid', 'sample.t+0.mid', 'sample.t+3.mid'
        ]

    def test_each_entry_is_transposed(self):
        """中身は 1 件ずつ持ち帰ったときと同じもの。"""
        data = transposed_midi_zip_bytes(SAMPLE_MIDI, [4])

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            body = zf.read('sample.t+4.mid')

        assert notes_of(body) == [
            n + 4 for n in notes_of(SAMPLE_MIDI.read_bytes())
        ]


def test_transposed_zip_name():
    assert transposed_zip_name('sample.mid') == 'sample.transposed.zip'
    assert transposed_zip_name('a.b.midi') == 'a.b.transposed.zip'


class TestDownloadTransposedMidiZip(WebAppTestCase):
    """`/download/midi-transpose-zip/<name>?t=-5,-2,0,3`（TODO-050）。"""

    PORT = 10087

    def setup_files(self):
        self.put_midi('sample.mid')

    def test_zip_has_every_candidate(self):
        response = self.fetch(f'{ZIP_URL}/sample.mid?t=-5,-2,0,3')

        assert response.code == 200
        assert response.headers['Content-Type'] == 'application/zip'
        assert zip_names(response.body) == [
            'sample.t-5.mid', 'sample.t-2.mid', 'sample.t+0.mid', 'sample.t+3.mid'
        ]

    def test_filename(self):
        response = self.fetch(f'{ZIP_URL}/sample.mid?t=0')

        assert 'filename="sample.transposed.zip"' in response.headers[
            'Content-Disposition'
        ]

    def test_duplicates_are_removed(self):
        """同じ名前の要素が 2 つ入った ZIP を作らない。"""
        response = self.fetch(f'{ZIP_URL}/sample.mid?t=3,3,0,3')

        assert zip_names(response.body) == ['sample.t+3.mid', 'sample.t+0.mid']

    def test_nothing_is_stored(self):
        before = self.names('midi')

        self.fetch(f'{ZIP_URL}/sample.mid?t=-5,0,3')

        assert self.names('midi') == before
        assert self.names('svg') == []

    def test_missing_file_is_404(self):
        assert self.fetch(f'{ZIP_URL}/nope.mid?t=1').code == 404

    def test_bad_name_is_400(self):
        assert self.fetch(f'{ZIP_URL}/%2e%2e%2fx.mid?t=1').code == 400

    def test_bad_transpose_is_400(self):
        assert self.fetch(f'{ZIP_URL}/sample.mid?t=abc').code == 400
        assert self.fetch(f'{ZIP_URL}/sample.mid?t=1,,2').code == 400
        assert self.fetch(f'{ZIP_URL}/sample.mid?t=').code == 400
        assert self.fetch(f'{ZIP_URL}/sample.mid').code == 400

    def test_too_many_is_400(self):
        """1 リクエストで何百回も移調させられないようにしてある。"""
        many = ','.join(str(n) for n in range(40))

        assert self.fetch(f'{ZIP_URL}/sample.mid?t={many}').code == 400


class TestDownloadTransposedMidi(WebAppTestCase):
    """`/download/midi-transpose/<name>?t=<半音数>`。"""

    PORT = 10086

    def setup_files(self):
        self.put_midi('sample.mid')
        self.put_midi('テスト曲.mid')

    def test_download_shifts_notes(self):
        response = self.fetch(f'{URL}/sample.mid?t=4')

        assert response.code == 200
        assert notes_of(response.body) == [
            n + 4 for n in notes_of(SAMPLE_MIDI.read_bytes())
        ]

    def test_filename_has_semitones(self):
        response = self.fetch(f'{URL}/sample.mid?t=-2')

        assert response.code == 200
        assert 'filename="sample.t-2.mid"' in response.headers[
            'Content-Disposition'
        ]

    def test_nothing_is_stored(self):
        """作った MIDI は置き場に残さない（TODO-042）。"""
        before = self.names('midi')

        self.fetch(f'{URL}/sample.mid?t=4')

        assert self.names('midi') == before
        assert self.names('svg') == []

    def test_missing_file_is_404(self):
        assert self.fetch(f'{URL}/nope.mid?t=1').code == 404

    def test_bad_name_is_400(self):
        # 素の '..' はクライアント側で畳まれて別のハンドラに届くので、
        # このハンドラに '..' を渡すには符号化しておく
        assert self.fetch(f'{URL}/%2e%2e%2fx.mid?t=1').code == 400
        assert self.fetch(f'{URL}/sub%2fx.mid?t=1').code == 400

    def test_bad_transpose_is_400(self):
        assert self.fetch(f'{URL}/sample.mid?t=abc').code == 400
        assert self.fetch(f'{URL}/sample.mid?t=1.5').code == 400
        assert self.fetch(f'{URL}/sample.mid').code == 400

    def test_unreadable_midi_is_400(self):
        (self.webroot / 'midi' / 'broken.mid').write_bytes(b'not midi')

        assert self.fetch(f'{URL}/broken.mid?t=1').code == 400
