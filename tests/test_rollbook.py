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
    key_label,
    merge_overlapping_notes,
    model_note_range,
    note2scale,
    playable_notes,
    svg_square,
    transpose_candidates,
    transpose_notes,
    transpose_notices,
)

# 移調のテスト用。C から 1 オクターブの、白鍵だけの機種
DIATONIC_CONF = {
    'base_note': 60,
    'notes': [
        {'name': 'C', 'offset': 0},
        {'name': 'D', 'offset': 2},
        {'name': 'E', 'offset': 4},
        {'name': 'F', 'offset': 5},
        {'name': 'G', 'offset': 7},
        {'name': 'A', 'offset': 9},
        {'name': 'B', 'offset': 11},
    ],
}


# 12 音すべてを 2 オクターブぶん鳴らせる機種。曲がこの音域に収まっていれば
# **どの調でも 100% 鳴る**ので、「移調しても改善しない」場合を作れる
CHROMATIC_CONF = {
    'base_note': 60,
    'notes': [{'name': str(i), 'offset': i} for i in range(24)],
}


def _note(note, start=0.0, end=1.0, channel=0, velocity=100):
    return RealNoteInfo(abs_time=start, channel=channel, note=note,
                        velocity=velocity, end_time=end)


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


def test_playable_notes_and_range():
    """機種が鳴らせる MIDI ノート番号の集合と、その最低・最高。"""
    assert playable_notes(DIATONIC_CONF) == {60, 62, 64, 65, 67, 69, 71}
    assert model_note_range(DIATONIC_CONF) == (60, 71)


def test_model_note_range_without_tracks():
    """トラックが 1 つも無ければ、最低も最高も base_note。"""
    assert model_note_range({'base_note': 55, 'notes': []}) == (55, 55)


def test_key_label_folds_into_minus5_to_plus6():
    """調の動きは -5〜+6 で表す（+7 は -5 と同じ調で、下げるほうが近い）。"""
    assert key_label(0) == 0
    assert key_label(12) == 0     # オクターブは調を変えない
    assert key_label(-12) == 0
    assert key_label(3) == 3
    assert key_label(7) == -5     # 上に 7 = 下に 5
    assert key_label(6) == 6      # ちょうど半分は + のまま
    assert key_label(-18) == 6


def test_transpose_notes_shifts_every_note():
    """全 MIDI ノート番号に同じ数を足す。他の項目は変えない。"""
    src = [_note(60, 0.0, 1.0), _note(64, 1.0, 2.5, channel=3)]

    out = transpose_notes(src, -12)

    assert [ni.note for ni in out] == [48, 52]
    assert [ni.abs_time for ni in out] == [0.0, 1.0]
    assert [ni.end_time for ni in out] == [1.0, 2.5]
    assert out[1].channel == 3
    # 元のリストは変えない
    assert [ni.note for ni in src] == [60, 64]


def test_transpose_notes_zero_copies():
    """0 半音でも写しを返す（呼ぶ側が破壊しても元が残る）。"""
    src = [_note(60)]
    out = transpose_notes(src, 0)

    assert out is not src
    assert out[0].note == 60


def test_transpose_candidates_are_one_per_key():
    """候補は調ごとに 1 つずつ。同じ調が 2 行出てはいけない。"""
    ni = [_note(n) for n in (72, 74, 76)]

    cands = transpose_candidates(ni, DIATONIC_CONF)

    keys = [c['key'] for c in cands]
    assert len(keys) == len(set(keys)), '同じ調が重複している'
    assert all(-5 <= k <= 6 for k in keys)
    # transpose は key と octave から復元できる
    for c in cands:
        assert c['transpose'] == c['key'] + c['octave'] * 12


def test_transpose_candidates_are_sorted_by_note_count():
    """鳴らせる音符の多い順に並ぶ。"""
    ni = [_note(n) for n in (73, 75, 78)]   # 黒鍵ばかり

    cands = transpose_candidates(ni, DIATONIC_CONF)

    counts = [c['notes'] for c in cands]
    assert counts == sorted(counts, reverse=True)


def test_transpose_candidates_finds_the_octave_shift():
    """音域から外れているだけなら、調を変えずにオクターブで収まる。"""
    # C-D-E の 2 オクターブ上。調は合っているが音域外
    ni = [_note(n) for n in (84, 86, 88)]

    cands = transpose_candidates(ni, DIATONIC_CONF)

    best = cands[0]
    assert best['note_pct'] == 100.0
    assert best['key'] == 0, '調を変えずに済むはず'
    assert best['transpose'] == -24
    assert (best['lo'], best['hi']) == (60, 64)


def test_transpose_candidates_empty_for_no_notes():
    assert transpose_candidates([], DIATONIC_CONF) == []


def test_transpose_candidates_range_is_not_a_fixed_width():
    """探索範囲は曲と機種の音域から決める。

    **固定幅（±24 など）にすると、遠く離れた曲で端に張り付く。**
    ここでは 4 オクターブ以上高い曲を置いて、それでも見つかることを見る。
    """
    ni = [_note(n) for n in (120, 122, 124)]   # 5 オクターブ上

    best = transpose_candidates(ni, DIATONIC_CONF)[0]

    assert best['note_pct'] == 100.0
    assert best['transpose'] == -60


def test_transpose_notices_reports_no_improvement():
    """どう移調しても変わらない曲は、はっきりそう言う。

    12 音すべて鳴らせる機種に、その音域へ収まる曲を渡すと、どの調でも
    100% 鳴る（＝選ぶ意味が無い）。
    """
    ni = [_note(n) for n in (65, 66, 67)]

    cands = transpose_candidates(ni, CHROMATIC_CONF)
    assert all(c['note_pct'] == 100.0 for c in cands), '前提が崩れている'

    notices = transpose_notices(cands)

    assert len(notices) == 1
    assert '改善しません' in notices[0]


def test_transpose_notices_reports_metric_disagreement():
    """音符の数の 1 位と、音の長さの 1 位が違うときは両方を示す。

    短い音 2 つが鳴る案と、長い音が鳴る案を作って食い違わせる。
    """
    ni = [
        _note(60, 0.0, 0.1),     # 短い
        _note(62, 1.0, 1.1),     # 短い
        _note(61, 2.0, 12.0),    # 長い（調を動かさないと鳴らない）
    ]

    cands = transpose_candidates(ni, DIATONIC_CONF)
    best = cands[0]
    best_sec = max(cands, key=lambda c: c['sec_pct'])
    assert best['transpose'] != best_sec['transpose'], '前提が崩れている'

    notices = transpose_notices(cands)

    assert any('音の長さでは' in n for n in notices)


def test_transpose_notices_empty_for_no_candidates():
    assert transpose_notices([]) == []


def test_rollbook_applies_the_transpose():
    """`transpose` を渡すと、その半音数だけずれた穴になる。"""
    midi_file = Path('webroot/midi/holy.mid')
    if not midi_file.exists():
        return

    plain = RollBook('20notes a')
    plain.parse(midi_file)

    shifted = RollBook('20notes a', transpose=-24)
    svg = shifted.parse(midi_file)

    assert shifted.transpose == -24
    assert shifted.hole_note_count > plain.hole_note_count
    assert 'data-storgan-transpose="-24"' in svg


def test_rollbook_auto_picks_the_best_candidate():
    """`'auto'` は候補の 1 位を採り、`transpose` に実際の値が入る。"""
    midi_file = Path('webroot/midi/holy.mid')
    if not midi_file.exists():
        return

    rb = RollBook('20notes a', transpose='auto')
    rb.parse(midi_file)

    assert rb.transpose == rb.candidates[0]['transpose']
    assert rb.transpose == -24   # 調そのままで 2 オクターブ下


def test_rollbook_makes_candidates_even_without_transposing():
    """移調しなくても候補は作る。**選び直せるように見せるのが目的。**"""
    midi_file = Path('webroot/midi/holy.mid')
    if not midi_file.exists():
        return

    rb = RollBook('20notes a')
    rb.parse(midi_file)

    assert rb.transpose == 0
    # 調ごとの 12 行 + いまの ±0（この曲では候補に挙がらない）
    assert len(rb.candidates) == 13


def test_rollbook_candidates_always_include_zero_and_current():
    """表に ±0 といまの値が必ずあること。

    `transpose_candidates()` は調ごとに「いちばん音域に収まるオクターブ」
    しか返さないので、`±0` は並ばないことが多い。**無いと、一度移調したら
    元に戻せない。**
    """
    midi_file = Path('webroot/midi/holy.mid')
    if not midi_file.exists():
        return

    for t in (0, -24, -3):
        rb = RollBook('20notes a', transpose=t)
        rb.parse(midi_file)

        got = [c['transpose'] for c in rb.candidates]
        assert t in got, f'いまの値 {t} が表に無い'
        assert 0 in got, f'±0 が表に無い（t={t} から戻れない）'
        # 同じ移調量が二重に並ばない
        assert len(got) == len(set(got)), t
        # 足した行も並び順（音符の多い順）を守る
        counts = [c['notes'] for c in rb.candidates]
        assert counts == sorted(counts, reverse=True), t


def test_rollbook_refuses_a_bad_transpose():
    """整数にも 'auto' にもならない値は、作る前に断る。"""
    with pytest.raises(ValueError, match='整数'):
        RollBook('20notes a', transpose='なんとなく')


def test_rollbook_accepts_a_numeric_string():
    """Web のフォームは文字列で送ってくるので、数字の文字列も通す。"""
    rb = RollBook('20notes a', transpose='-12')
    assert rb.transpose == -12


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
