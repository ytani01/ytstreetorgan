#
# (c) 2026 Yoichi Tanibayashi
#
"""ブラウザでの試聴用の MIDI（TODO-063）。

**「この機種で実際に鳴る音」だけを鳴らす。** 移調・重なりの統合
（`merge_overlapping_notes()`。TODO-038）・音階での絞り込み
（`note2scale()` が -1 を返す音を除く）を経たもので、ロールブックの
実線の穴と 1 対 1 に対応する。

**持ち帰る MIDI（`transpose.py`）とは別物。** あちらは元のファイルを
移調するだけで、テンポもトラック構成も音階に無い音も残す「素材」。
こちらは実機の再現なので音が消える。同じ名前で中身の違う MIDI が
2 種類出回らないように、経路（エンドポイント）も分けてある。

依存は一方向に保つこと::

    conf.py → transpose.py → rollbook.py → audition.py → handler1.py
"""
import io
from pathlib import Path

from loguru import logger
from ytmidilib import NoteInfo, write

from .rollbook import RollBook

# 鳴らすチャンネル。**必ず 0 に揃える。** ブラウザ側の再生に使う Magenta
# は channel 9 をドラムとして扱い、合成ドラムの音で鳴らすため、元の MIDI の
# チャンネルをそのまま残すと「穴が開く音がキックドラムで鳴る」ことになる。
PLAY_CHANNEL = 0


def playable_midi_bytes(
    src: Path, model: str, semitones: int = 0,
    conf_file: str = RollBook.DEF_CONF_FILE,
) -> bytes:
    """実機で鳴る音だけを集めた MIDI のバイト列を返す（TODO-063）。

    **絞り込みの手順は組み立て直さない。** `RollBook.load()` をそのまま
    通し、その結果（`playable_note_info`）を書き出すだけにしてある。
    音階に入るかどうかは移調したあとに決まるので、順序を持ち直すと
    黙って食い違う（TODO-043 と同じ失敗）。

    **ディスクには残さない**（`transpose_midi_bytes()` と同じ）。
    `ytmidilib.write()` が `io.BytesIO` を受けるので、それをそのまま返す。

    Args:
        src (Path): 元の MIDI ファイル。
        model (str): 機種名。
        semitones (int): 移調する半音数（負なら下げる）。
        conf_file (str): 設定ファイルのパス（既定は探索に任せる）。

    Returns:
        bytes: 鳴る音だけの MIDI（SMF）。音符が 1 つも無ければ、
            音の入っていない MIDI になる。

    Raises:
        ValueError: 機種が設定に無い、設定の項目が足りないとき
            （`RollBook` が投げるものをそのまま通す）。
    """
    book = RollBook(model, conf_file, semitones)
    book.load(src)

    # チャンネルだけ 0 に差し替えた写しを作る（元の音符は変えない）
    note_info = [
        NoteInfo(
            abs_time=ni.abs_time,
            channel=PLAY_CHANNEL,
            note=ni.note,
            velocity=ni.velocity,
            end_time=ni.end_time,
        )
        for ni in book.playable_note_info
    ]

    buf = io.BytesIO()
    write(buf, note_info)
    data = buf.getvalue()

    logger.debug(
        'src={}, model={}, semitones={}, notes={}, len(data)={}',
        src, model, semitones, len(note_info), len(data)
    )
    return data
