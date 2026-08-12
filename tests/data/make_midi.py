"""テスト用の MIDI を合成する（TODO-081）。

同じディレクトリの `.mid` はこのスクリプトが作ったもので、**リポジトリで
追跡している**。実曲の MIDI は出所がはっきりしないので置かない。何を
試している MIDI なのかは、ここを読めば分かる。

    uv run python tests/data/make_midi.py

SMF に日時は入らないので、作り直しても同じ中身になる（`git status` は
きれいなまま）。**音を変えたら、下に書いた性質が保たれているか確かめる
こと**（テストの期待値がこれに依っている）。

- `sample.mid` — 中身のある MIDI が要るとき全般。C 長調の半音上
  （C# 長調）なので、**-1 半音で `'20notes a'` の音階に収まる**。
  `'34notes'` では D#4 だけが音階に無い（破線が出る）
- `long-notes.mid` — 長い音を含む。`'20notes'`（`bridge_threshold` 50.0）と
  `'20notes a'`（2.7）で**分割後の穴の数が大きく変わる**。同じ高さの
  重なりもあるので、統合（`merged_count`）も通る
- `in-scale.mid` — 全部の音が `'20notes a'` の音階にある（±0 で 100%）。
  **どう移調しても改善しない**場合を作る
"""
from pathlib import Path

import mido

TPQ = 480        # 4 分音符あたりの tick
SEC = TPQ * 2    # 既定のテンポ（120 BPM）では 4 分音符 = 0.5 秒

DATA_DIR = Path(__file__).resolve().parent

# C 長調（この 8 音を、そのまま・半音上げて使う）
C_MAJOR = [60, 62, 64, 65, 67, 69, 71, 72]


def notes_in_a_row(
    notes: list[int], start: int = 0, length: int = SEC // 2
) -> list[tuple[int, int, int]]:
    """同じ長さの音を順に並べる。"""
    return [
        (note, start + i * length, length) for i, note in enumerate(notes)
    ]


def write_midi(path: Path, notes: list[tuple[int, int, int]]) -> Path:
    """`(MIDI ノート番号, 開始 tick, 長さ tick)` の並びから MIDI を作る。"""
    events = []
    for note, start, length in notes:
        events.append((start, 'note_on', note, 100))
        events.append((start + length, 'note_off', note, 0))
    # 同じ tick では note_off を先に置く（重なりを意図せず作らない）
    events.sort(key=lambda e: (e[0], e[1] == 'note_on'))

    mid = mido.MidiFile(ticks_per_beat=TPQ)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    now = 0
    for when, kind, note, velocity in events:
        track.append(mido.Message(
            kind, note=note, velocity=velocity, time=when - now
        ))
        now = when

    mid.save(path)
    return path


# C# 長調。'20notes a' の音階（C 長調 + F#）には 8 音中 3 音しか無く、
# -1 半音で全部が収まる。'34notes' には D#4(63) だけが無い
SAMPLE = notes_in_a_row([note + 1 for note in C_MAJOR])

# 長い音（分割される）→ 同じ高さの重なり（統合される）→ 短い音の繰り返し。
# 63 = D#4 は '34notes' の音階に無いので、破線のほうも分割される。
# **ブックの全長も要る**（ブラウザのビューアのテストが、高さを合わせた
# 状態で横にはみ出していることを前提にしている）
LONG_NOTES = [
    (60, 0 * SEC, 4 * SEC),
    (64, 4 * SEC, 3 * SEC),
    (67, 7 * SEC, 2 * SEC),
    (63, 9 * SEC, 3 * SEC),
    (65, 12 * SEC, 2 * SEC),
    (65, 13 * SEC, 2 * SEC),   # 1 つ前と重なる（1 音にまとめられる）
    *[
        note
        for i in range(8)
        for note in notes_in_a_row(C_MAJOR, start=(15 + i * 4) * SEC)
    ],
]

IN_SCALE = notes_in_a_row(C_MAJOR)


if __name__ == '__main__':
    write_midi(DATA_DIR / 'sample.mid', SAMPLE)
    write_midi(DATA_DIR / 'long-notes.mid', LONG_NOTES)
    write_midi(DATA_DIR / 'in-scale.mid', IN_SCALE)
