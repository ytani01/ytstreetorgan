import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from ytmidilib import NoteInfo as RealNoteInfo

from ytstreetorgan.rollbook import (
    HOLE_COLOR,
    HoleInfo,
    RollBook,
    merge_overlapping_notes,
    note2scale,
    svg_square,
)


def test_note2scale():
    notes = [
        {'name': 'C', 'offset': 0},
        {'name': 'D', 'offset': 2},
        {'name': 'E', 'offset': 4},
    ]
    assert note2scale(60, 60, notes) == 0
    assert note2scale(62, 60, notes) == 1
    assert note2scale(65, 60, notes) == -1

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
        'base_note': 60,
        'notes': [
            {'name': 'C', 'offset': 0},
            {'name': 'D', 'offset': 2},
            {'name': 'E', 'offset': 4},
        ],
        'mm_per_sec': 10,
        'pitch': 5,
        'margin': 2,
        'hole_height': 3,
        'book_height': 100
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
        'base_note': 60,
        'notes': [
            {'name': 'C', 'offset': 0},
            {'name': 'D', 'offset': 2},
            {'name': 'E', 'offset': 4},
        ],
        'mm_per_sec': 10,
        'pitch': 5,
        'margin': 2,
        'hole_height': 3
    }
    hi = HoleInfo(mock_note, conf)
    s = str(hi)
    assert 'note:060' in s


def test_rollbook_parse_real_midi():
    # Verify that parse works with a real MIDI file (fixture)
    midi_file = Path('webroot/midi/d-kaeru.mid')
    if midi_file.exists():
        rb = RollBook()
        svg = rb.parse(midi_file)
        assert '<svg ' in svg
        assert '</svg>' in svg
        # There should be some notes parsed
        assert len(rb._holes) > 0
        assert rb._width > 0


def test_rollbook_dimension_properties():
    """Web のビューアは寸法をこのプロパティ経由で受け取る。

    width / height は SVG にも出るので、値が食い違わないこと。
    穴の数と mm_per_sec は SVG から取り出せない。
    """
    midi_file = Path('webroot/midi/d-kaeru.mid')
    if not midi_file.exists():
        return

    rb = RollBook()

    # parse() する前は全長が決まらない
    assert rb.width == 0.0
    assert rb.height > 0
    assert rb.note_count == 0
    assert rb.hole_count == 0

    svg = rb.parse(midi_file)

    assert rb.width > 0
    assert rb.mm_per_sec > 0
    assert f'width="{rb.width:.2f}mm" height="{rb.height:.2f}mm"' in svg


def test_unknown_model_is_refused():
    """知らない機種名は断る。

    `Conf.get()` が `{}` を返し、`HoleInfo` が足りない項目を 0 で読むので、
    かつては「高さ 0 の空のブック」が何事もなく生成されていた。
    """
    with pytest.raises(ValueError, match='no-such-model'):
        RollBook('no-such-model')


def test_incomplete_config_is_refused(tmp_path):
    """項目の足りない設定も断る（黙って 0 で描かない）。"""
    conf = json.loads(
        (Path('conf') / 'storgan-conf.json').read_text(encoding='utf-8')
    )
    broken = next(d for d in conf if d['model'] == '34notes')
    del broken['pitch']

    conf_file = tmp_path / 'storgan-conf.json'
    conf_file.write_text(json.dumps([broken]), encoding='utf-8')

    with pytest.raises(ValueError, match='pitch'):
        RollBook('34notes', str(conf_file))


def test_parse_twice_gives_the_same_book():
    """同じインスタンスで 2 回 parse しても結果が変わらないこと。

    かつては `_holes` を初期化せずに追加していたので、2 回目は穴が二重に
    なり、`_width` も `max()` で伸びたままだった。
    """
    midi_file = Path('webroot/midi/d-kaeru.mid')
    if not midi_file.exists():
        return

    rb = RollBook('34notes')
    first = rb.parse(midi_file)
    counts = (rb.width, rb.note_count, rb.hole_count, rb.off_scale_count)

    second = rb.parse(midi_file)

    assert (rb.width, rb.note_count, rb.hole_count, rb.off_scale_count) == counts
    assert second == first


def test_hole_counts_are_split_into_solid_and_dashed():
    """穴の数は「音符の数」と「分割後の数」を、実線と破線で分けて数える。

    合計と、実際に描かれる `<path>` の数が合うこと。
    """
    midi_file = Path('webroot/midi/d-kaeru.mid')
    if not midi_file.exists():
        return

    rb = RollBook('34notes')
    svg = rb.parse(midi_file)

    # 音符は実線と破線に分かれる
    assert rb.hole_note_count + rb.off_scale_note_count == rb.note_count
    assert rb.hole_note_count > 0
    assert rb.off_scale_note_count > 0

    # 分割されるぶん、音符より多くなる（減ることはない）
    assert rb.hole_count >= rb.hole_note_count
    assert rb.off_scale_count >= rb.off_scale_note_count
    assert rb.hole_count > rb.hole_note_count   # この曲では実際に分割される

    # 描かれる path と一致する（外枠の 1 本を除く）
    drawn = len(re.findall(r'<path ', svg)) - 1
    assert rb.hole_count + rb.off_scale_count == drawn


def test_hole_count_counts_only_the_solid_ones():
    """穴の数は実線だけ。破線は音階に無い音なので穴を開けない。"""
    midi_file = Path('webroot/midi/d-kaeru.mid')
    if not midi_file.exists():
        return

    rb = RollBook('34notes')
    rb.parse(midi_file)

    solid = [h for h in rb._holes if h.scale >= 0]
    assert rb.hole_note_count == len(solid)
    assert rb.hole_count == sum(len(h.segments) for h in solid)


def test_hole_count_grows_when_holes_are_divided_more():
    """`bridge_threshold` が小さいほど、分割されて穴が増える。

    '20notes' と '20notes a' は音階の定義が同じで、違うのは
    `bridge_threshold`（50.0 と 2.7）だけ。**音符の数は変わらないのに
    穴の数だけ増える**ので、SVG から逆算できないことがこれで分かる。
    """
    midi_file = Path('webroot/midi/d-kaeru.mid')
    if not midi_file.exists():
        return

    coarse = RollBook('20notes')      # bridge_threshold = 50.0
    coarse.parse(midi_file)
    fine = RollBook('20notes a')      # bridge_threshold = 2.7
    fine.parse(midi_file)

    # 音符の数は同じ
    assert coarse.note_count == fine.note_count
    assert coarse.hole_note_count == fine.hole_note_count
    # 分割後は大きく違う
    assert fine.hole_count > coarse.hole_count * 2


def test_merge_overlapping_notes_merges_overlap():
    """TODO-038: 同じ MIDI ノート番号どうしの重なりを 1 つにまとめる。"""
    a = RealNoteInfo(abs_time=1.0, channel=0, note=60, velocity=50, end_time=3.0)
    b = RealNoteInfo(abs_time=2.0, channel=1, note=60, velocity=80, end_time=4.0)

    merged = merge_overlapping_notes([a, b])

    assert len(merged) == 1
    assert merged[0].abs_time == 1.0
    assert merged[0].end_time == 4.0
    assert merged[0].velocity == 80   # 大きいほうを採る
    assert merged[0].channel == 0     # 先に鳴り始めたほうを採る


def test_merge_overlapping_notes_merges_containment():
    """内包（短い音が長い音の中にすっぽり入る）でも end_time が縮まない。"""
    a = RealNoteInfo(abs_time=1.0, channel=0, note=60, velocity=50, end_time=5.0)
    b = RealNoteInfo(abs_time=2.0, channel=1, note=60, velocity=80, end_time=3.0)

    merged = merge_overlapping_notes([a, b])

    assert len(merged) == 1
    assert merged[0].abs_time == 1.0
    assert merged[0].end_time == 5.0


def test_merge_overlapping_notes_merges_touching():
    """前の終わり＝次の始まりも、繋がっている 1 つの穴としてまとめる。"""
    a = RealNoteInfo(abs_time=1.0, channel=0, note=60, velocity=50, end_time=2.0)
    b = RealNoteInfo(abs_time=2.0, channel=1, note=60, velocity=50, end_time=3.0)

    merged = merge_overlapping_notes([a, b])

    assert len(merged) == 1
    assert merged[0].abs_time == 1.0
    assert merged[0].end_time == 3.0


def test_merge_overlapping_notes_keeps_different_notes_apart():
    """違う MIDI ノート番号（違うトラック）はまとめない。"""
    a = RealNoteInfo(abs_time=1.0, channel=0, note=60, velocity=50, end_time=3.0)
    b = RealNoteInfo(abs_time=1.0, channel=1, note=61, velocity=50, end_time=3.0)

    merged = merge_overlapping_notes([a, b])

    assert len(merged) == 2


def test_merge_overlapping_notes_keeps_non_overlapping_apart():
    """重なっても接してもいなければまとめない。"""
    a = RealNoteInfo(abs_time=1.0, channel=0, note=60, velocity=50, end_time=2.0)
    b = RealNoteInfo(abs_time=5.0, channel=0, note=60, velocity=50, end_time=6.0)

    merged = merge_overlapping_notes([a, b])

    assert len(merged) == 2


def test_merge_overlapping_notes_sorts_by_abs_time():
    """入力の並び順に関わらず、結果は abs_time の昇順になる。"""
    a = RealNoteInfo(abs_time=5.0, channel=0, note=60, velocity=50, end_time=6.0)
    b = RealNoteInfo(abs_time=1.0, channel=0, note=60, velocity=50, end_time=2.0)

    merged = merge_overlapping_notes([a, b])

    assert [ni.abs_time for ni in merged] == [1.0, 5.0]


@patch('ytstreetorgan.rollbook.Parser')
def test_overlapping_same_note_does_not_starve_bridges(mock_parser):
    """TODO-038: 統合前は、重なった相手の穴がブリッジを食い、紙が分離した。

    A（0.0〜3.0秒）に B（1.0〜2.0秒）が内包される、同じ音階の音。
    統合しないと A を分割したブリッジの一部が B の穴と重なって消える。
    """
    mock_instance = mock_parser.return_value

    a = RealNoteInfo(abs_time=0.0, channel=0, note=60, velocity=50, end_time=3.0)
    b = RealNoteInfo(abs_time=1.0, channel=1, note=60, velocity=80, end_time=2.0)

    mock_instance.parse.return_value = {
        'channel_set': {0, 1},
        'note_info': [a, b],
    }

    rb = RollBook()
    rb._conf = {
        'base_note': 60,
        'notes': [{'name': 'C', 'offset': 0}],
        'mm_per_sec': 100,   # 300mm の全長になる
        'pitch': 5,
        'margin': 2,
        'hole_height': 3,
        'book_height': 100,
        'bridge_threshold': 50,
        'bridge_width': 1,
    }

    rb.parse('dummy.mid')

    assert rb.note_count == 1
    assert rb.merged_count == 1
    assert len(rb._holes) == 1

    segments = rb._holes[0].segments
    assert len(segments) > 1   # 実際に分割されている

    # ブリッジ（セグメント間の隙間）が重ならず、紙が繋がったままであること
    for (_, end1), (start2, _) in zip(segments, segments[1:], strict=False):
        assert end1 <= start2


def test_css_selects_holes_by_the_same_color():
    """ビューアの CSS は、実線の穴を**色の文字列**で選んで塗っている。

    CSS からは定数を import できないので、`HOLE_COLOR` を変えると
    セレクタが黙ってすり抜け、画面で塗られなくなるだけになる。
    ずれたらここで気づけるようにしておく。
    """
    css = (Path('webroot') / 'static' / 'css' / 'my.css').read_text(
        encoding='utf-8'
    )

    assert f'stroke:{HOLE_COLOR}' in css, (
        f'my.css が {HOLE_COLOR} を選んでいない。'
        'rollbook.HOLE_COLOR を変えたら my.css も直すこと'
    )
