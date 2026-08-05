#
# (c) 2026 Yoichi Tanibayashi
#
import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import TypedDict
from xml.sax.saxutils import quoteattr

from loguru import logger
from ytmidilib import NoteInfo, Parser

from .conf import Conf, ModelConf, NoteConf, validate_config

DEF_LINE_WIDTH = 0.2

# 線の色と、諸元を埋める属性の接頭辞。
# **`storage.book_from_svg()` がこの色で穴と破線を見分け、この接頭辞で
# 諸元を読む。** どちらも「描いたものを読み直す」ための約束なので、
# 定義はここ 1 か所に置き、storage 側はこれを import して使う。
#
# [!! 注意 !!] **色を変えるなら `webroot/static/css/my.css` も直すこと。**
# ビューアは `path[style*="stroke:#FF0000"]` という**文字列の一致**で
# 実線の穴を選んで塗っている（CSS からは import できない）。片方だけ
# 変えると黙ってすり抜け、画面で塗られなくなるだけになるので、
# `test_css_selects_holes_by_the_same_color` がずれを見張っている。
BOOK_COLOR = '#0000FF'       # ブックの外枠
HOLE_COLOR = '#FF0000'       # 実線（実際に開ける穴）
OFF_SCALE_COLOR = '#000000'  # 破線（オルガンの音階に無い音）
OFF_SCALE_DASH = '3 1'       # 破線の刻み

# 他のツールが付けた属性と紛れないように storgan- で始める
META_PREFIX = 'data-storgan-'


def note2scale(midi_note: int, base_note: int, notes: list[NoteConf]) -> int:
    """MIDIノート番号からスケール番号（インデックス）を取得する。

    Args:
        midi_note (int): 対象のMIDIノート番号。
        base_note (int): 基準となるベースノート番号。
        notes (list[NoteConf]): トラックの定義（``'offset'`` だけを見る）。

    Returns:
        int: 対応するスケール番号（インデックス）。該当するものがない場合は -1。
    """
    scale = -1

    for s, note in enumerate(notes):
        if base_note + note['offset'] == midi_note:
            scale = s
            break

    return scale


def playable_notes(conf: ModelConf) -> set[int]:
    """機種が鳴らせる MIDI ノート番号の集合。

    `note2scale()` はトラック番号（穴の列）が要るときに使う。こちらは
    「鳴らせるかどうか」だけを何万回も調べる用（移調の候補を作るとき）。
    """
    base_note = conf.get('base_note', 0)
    return {base_note + n['offset'] for n in conf.get('notes', [])}


def model_note_range(conf: ModelConf) -> tuple[int, int]:
    """機種が鳴らせる MIDI ノート番号の最低・最高。

    Returns:
        tuple[int, int]: ``(最低, 最高)``。トラックが 1 つも無ければ
            どちらも ``base_note``。
    """
    base_note = conf.get('base_note', 0)
    notes = conf.get('notes', [])
    if not notes:
        return (base_note, base_note)

    offsets = [n['offset'] for n in notes]
    return (base_note + min(offsets), base_note + max(offsets))


def transpose_notes(
    note_info: list[NoteInfo], semitones: int
) -> list[NoteInfo]:
    """全 MIDI ノート番号に ``semitones`` を足した写しを返す（移調）。

    曲を丸ごと上下させる。機種の設定を読まないので、`RollBook` からも
    `MidiApp`（`play`）からも同じように使える。

    Args:
        note_info (list[NoteInfo]): 対象の音符。
        semitones (int): 足す半音数。0 なら写すだけ。

    Returns:
        list[NoteInfo]: 移調後の音符（元のリストは変えない）。
    """
    if semitones == 0:
        return list(note_info)

    return [
        NoteInfo(
            abs_time=ni.abs_time,
            channel=ni.channel,
            note=ni.note + semitones,
            velocity=ni.velocity,
            end_time=ni.end_time,
        )
        for ni in note_info
    ]


def key_label(semitones: int) -> int:
    """移調量を「調の動き」に直す（-5〜+6 の半音数）。

    +7 は -5 と同じ調なので、動きの小さいほうで表す。0 は調が変わらない。
    """
    key = semitones % 12
    return key - 12 if key > 6 else key


class TransposeCandidate(TypedDict):
    """移調の候補 1 つ。**調ごとに 1 つだけ**作る。

    Attributes:
        key: 調の動き（-5〜+6 の半音数）。0 なら**キーが変わらない**。
        octave: どのオクターブに置くか。
        transpose: 合計の半音数（＝実際に足す数）。``key + octave * 12``。
        notes: 鳴らせる音符の数。
        note_pct: 鳴らせる音符の数の割合 [%]。**並び順はこれ**。
        sec_pct: 鳴らせる音符の長さ（秒）の合計の割合 [%]。
            画面では「音の長さ」と呼ぶ（ブック全体の「演奏時間」とは別物）。
        lo: 移調後の最低 MIDI ノート番号。
        hi: 移調後の最高 MIDI ノート番号。
    """

    key: int
    octave: int
    transpose: int
    notes: int
    note_pct: float
    sec_pct: float
    lo: int
    hi: int


class _NoteTally:
    """MIDI ノート番号ごとの「何個あるか・合計で何秒鳴るか」。

    移調量を総当たりするとき、音符 1 つずつ数え直すと重い
    （曲 2000 音 × 移調 100 通り）。ここへ畳んでおくと、1 つの移調量
    あたり高々 128 回で済む。
    """

    def __init__(self, note_info: list[NoteInfo]) -> None:
        self.count_of: dict[int, int] = {}
        self.sec_of: dict[int, float] = {}
        for ni in note_info:
            self.count_of[ni.note] = self.count_of.get(ni.note, 0) + 1
            self.sec_of[ni.note] = (
                self.sec_of.get(ni.note, 0.0) + (ni.end_time - ni.abs_time)
            )

        self.total_notes = len(note_info)
        self.total_sec = sum(self.sec_of.values())
        self.note_min = min(self.count_of) if self.count_of else 0
        self.note_max = max(self.count_of) if self.count_of else 0

    def score(self, t: int, playable: set[int]) -> TransposeCandidate:
        """移調量 `t` 1 つぶんの成績。"""
        notes = 0
        sec = 0.0
        for n, c in self.count_of.items():
            if n + t in playable:
                notes += c
                sec += self.sec_of[n]

        key = key_label(t)
        return {
            'key': key,
            'octave': (t - key) // 12,
            'transpose': t,
            'notes': notes,
            'note_pct': notes / self.total_notes * 100,
            'sec_pct': (sec / self.total_sec * 100) if self.total_sec else 0.0,
            'lo': self.note_min + t,
            'hi': self.note_max + t,
        }


def transpose_score(
    note_info: list[NoteInfo], conf: ModelConf, semitones: int
) -> TransposeCandidate | None:
    """移調量 1 つぶんの成績を出す（音符が無ければ None）。

    候補に挙がらない移調量（``±0`` や手で指定した値）を、候補と同じ形で
    表に並べるために使う。**候補だけを出すと ±0 に戻れなくなる。**
    """
    if not note_info:
        return None

    return _NoteTally(note_info).score(semitones, playable_notes(conf))


def transpose_candidates(
    note_info: list[NoteInfo], conf: ModelConf
) -> list[TransposeCandidate]:
    """移調の候補を、鳴らせる音符の多い順に返す（TODO-039）。

    移調量を総当たりして、**調ごとに 1 つずつ残す**。

    1. 移調量 `t` の範囲を決める。1 音でも鳴りうるぶんだけ見れば足りる::

           t = (機種の最低 - 曲の最高) 〜 (機種の最高 - 曲の最低)

       **固定幅にしないこと。** 曲が機種より 2 オクターブ以上高いと
       最適値が範囲の端に張り付き、その先を見ていないことに気づけない。
    2. `t` を `t % 12` でグループ分けする（12 個）。同じグループの `t` は
       **調が同じで、違いはオクターブだけ**。
    3. 各グループから、鳴らせる音符が最多の `t` を 1 つ選ぶ。同点なら
       `|t|` が小さいほう。これで「その調で、いちばん音域に収まる
       オクターブ」が選ばれる。
    4. 音符の多い順に並べて返す。

    Returns:
        list[TransposeCandidate]: 最大 12 個。音符が 0 個の曲なら空。
    """
    if not note_info:
        return []

    playable = playable_notes(conf)
    lo, hi = model_note_range(conf)
    tally = _NoteTally(note_info)

    best_of_key: dict[int, TransposeCandidate] = {}

    for t in range(lo - tally.note_max, hi - tally.note_min + 1):
        cand = tally.score(t, playable)
        key = cand['key']

        cur = best_of_key.get(key)
        # 同じ調なら、音符が多いほう → 同点なら移調量が小さいほう
        if cur is None or (
            (cand['notes'], -abs(t))
            > (cur['notes'], -abs(cur['transpose']))
        ):
            best_of_key[key] = cand

    # 数が同じなら**調を変えない案を上に**する。キーを変えずに済むなら
    # そのほうが良いのに、僅差で下に沈むと気づかれない。次いで移調量が小さい順。
    return sorted(
        best_of_key.values(),
        key=lambda c: (-c['notes'], c['key'] != 0, abs(c['transpose']))
    )


def add_transpose_rows(
    candidates: list[TransposeCandidate],
    note_info: list[NoteInfo], conf: ModelConf, wanted: Sequence[int],
) -> list[TransposeCandidate]:
    """候補に無い移調量の行を足して、並べ直したものを返す。

    `transpose_candidates()` は調ごとに「いちばん音域に収まるオクターブ」
    しか返さないので、**`±0` や手で指定した値は並ばないことが多い**。
    それだと表から ±0 に戻せず、「移調しないと何 % なのか」も分からない。

    Args:
        candidates (list[TransposeCandidate]): `transpose_candidates()` の結果。
        note_info (list[NoteInfo]): 成績を測る対象（移調する**前**）。
        conf (ModelConf): 機種の設定。
        wanted (Sequence[int]): 必ず行にしたい移調量。既にあるものは飛ばす。

    Returns:
        list[TransposeCandidate]: 鳴らせる音符の多い順。元のリストは変えない。
    """
    if not candidates:
        return list(candidates)

    rows = list(candidates)
    for t in wanted:
        if any(c['transpose'] == t for c in rows):
            continue
        row = transpose_score(note_info, conf, t)
        if row is not None:
            rows.append(row)

    rows.sort(key=lambda c: (-c['notes'], c['key'] != 0, abs(c['transpose'])))
    return rows


def transpose_notices(candidates: list[TransposeCandidate]) -> list[str]:
    """候補について、利用者に言っておくべきことを返す（TODO-039）。

    **最適解は 1 つに定まらないことのほうが多い。** 一覧を出すだけでは
    気づけない状況だけを言葉にする。

    - 全部同じ → 移調しても改善しない（黙って ±0 を返すと壊れて見える）
    - 音符の数の 1 位と、音の長さの 1 位が違う → 両方を示す
    - 調を変えない案が 1 位でないが上位にある → それで済むと知らせる

    Returns:
        list[str]: 画面に出す文（日本語）。何も無ければ空。
    """
    if not candidates:
        return []

    notices: list[str] = []
    best = candidates[0]

    if all(c['notes'] == best['notes'] for c in candidates):
        notices.append(
            'どの調にしても鳴らせる音符の数は変わりません'
            f'（{best["note_pct"]:.0f}%）。移調しても改善しません。'
        )
        return notices

    best_sec = max(
        candidates, key=lambda c: (c['sec_pct'], -abs(c['transpose']))
    )
    if best_sec['transpose'] != best['transpose']:
        notices.append(
            f'音符の数では 調{best["key"]:+d}'
            f'（{best["note_pct"]:.0f}%）ですが、'
            f'音の長さでは 調{best_sec["key"]:+d}'
            f'（{best_sec["sec_pct"]:.0f}%）が上です。'
        )

    if best['key'] != 0:
        same_key = next((c for c in candidates if c['key'] == 0), None)
        # 1 位に迫るなら、キーを変えずに済むことを知らせる
        if same_key and best['note_pct'] - same_key['note_pct'] <= 5.0:
            notices.append(
                '調を変えずに（オクターブだけで）'
                f'{same_key["note_pct"]:.0f}% 鳴らせます。'
            )

    return notices


def merge_overlapping_notes(note_info: list[NoteInfo]) -> list[NoteInfo]:
    """同じ MIDI ノート番号どうしの、時間が重なる／接している音をまとめる。

    実機は 1 つの音に 1 本のパイプしか無く、同じ高さの音を複数のパートが
    同時に鳴らしても鳴るのは 1 本だけになる。まとめておかないと、
    ロールブックでは同じトラックに穴が重なって描かれるうえ、
    `divide_length_by_max_len()` によるブリッジ分割が、重なった相手の
    穴に食われて紙が分離することがある（TODO-038）。

    **トラック単位ではなく MIDI ノート番号単位でまとめる。** オルガンの
    音階に無い音（`note2scale()` が -1 を返す音）は `HoleInfo.y` が
    `scale = -1` の 1 行に集まるが、それは別の高さの音どうしが同じ行を
    共有しているだけで、ここで統合してよい重なりではない。ノート番号単位
    なら機種の設定を読まずに済むので、`MidiApp`（`play -m`）からも使える。

    Args:
        note_info (list[NoteInfo]): 対象の音符（並び順は問わない）。

    Returns:
        list[NoteInfo]: `abs_time` の昇順に並んだ、統合後の音符。
            統合した音の `velocity` は大きいほう、`channel` は先に
            鳴り始めたほうを採る。
    """
    by_note: dict[int, list[NoteInfo]] = {}
    for ni in note_info:
        by_note.setdefault(ni.note, []).append(ni)

    merged: list[NoteInfo] = []
    for group in by_note.values():
        group.sort(key=lambda ni: ni.abs_time)

        cur = group[0]
        for nxt in group[1:]:
            # 音符の end_time は Parser.parse() が必ず埋めている
            assert cur.end_time is not None and nxt.end_time is not None
            if nxt.abs_time <= cur.end_time:
                # 重なっている（内包も含む）か、接している
                cur = NoteInfo(
                    abs_time=cur.abs_time,
                    channel=cur.channel,
                    note=cur.note,
                    velocity=max(cur.velocity, nxt.velocity),
                    end_time=max(cur.end_time, nxt.end_time),
                )
            else:
                merged.append(cur)
                cur = nxt
        merged.append(cur)

    merged.sort(key=lambda ni: ni.abs_time)
    return merged


def svg_square(
    x: float, y: float, w: float, h: float,
    color: str, line_width: float = DEF_LINE_WIDTH,
    stroke_dasharray: str = 'none',
    hairline: bool = True
) -> str:
    """矩形描画用のSVGパス文字列を生成する。

    Args:
        x (float): X座標（mm単位）。
        y (float): Y座標（mm単位）。
        w (float): 幅（mm単位）。
        h (float): 高さ（mm単位）。
        color (str): 線色（例: '#FF0000'）。
        line_width (float, optional): 線の太さ（mm単位）。デフォルトは DEF_LINE_WIDTH。
        stroke_dasharray (str, optional): 破線のスタイル（例: 'none', '3 1'）。
            デフォルトは 'none'。
        hairline (bool, optional): ヘアライン指定。デフォルト 'True'

    Returns:
        str: 生成されたSVGパス要素の文字列。
    """
    logger.debug('w={}', w)

    style_str:str = 'fill:none;'
    style_str += f'stroke:{color};'
    style_str += f'stroke-width:{line_width};'
    style_str += f'stroke-dasharray:{stroke_dasharray};'
    if hairline:
        style_str += 'vector-effect:non-scaling-stroke;'
        style_str += '-inkscape-stroke:hairline;'

    d_str:str = f'M {-x:.2f},{-y:.2f} h {-w:.2f} v {-h:.2f} h {w:.2f} Z'

    svg:str = f'<path style="{style_str}" d="{d_str}" />\n'

    return svg


def divide_length_by_max_len(
    total_len: float, unit_len_max: float | None, gap: float | None = 1.0
) -> list[tuple[float, float]]:
    """長さ total_len を 最大 unit_len_max間隔 で分割。間隔は gap。
    最少の分割数 n で分割する。

    Args:
        total_len (float): 全長[mm]
        unit_len_max (float|None): 1要素あたりの最大長さ[mm]
        gap (float|None): 要素間の間隔[mm], default = 1.0mm

    Returns:
        list[tuple[float, float]]: 各要素の (開始, 終了)。分割しない場合は 1 個。

    Note:
        分割数 n と 1 要素あたりの長さも計算しているが、**返さない**
        （誰も読んでいなかった）。
    """
    logger.debug(
        'total_len={}, unit_len_max={}, gap={}',
        total_len, unit_len_max, gap
    )

    NO_DIVISION: list[tuple[float, float]] = [(0.0, total_len)]

    if total_len <= 0:
        logger.error('{} <=0', total_len)
        return NO_DIVISION
    if unit_len_max is None or unit_len_max <= 0:
        logger.error('{} <= 0', unit_len_max)
        return NO_DIVISION
    if gap is None or gap <= 0.0:
        return NO_DIVISION

    # x(n) <= b を満たす最小の正の整数 n
    n = math.ceil((total_len + gap) / (gap + unit_len_max))

    # 1要素あたりの長さを算出
    total_gap = (n - 1) * gap
    unit_len = (total_len - total_gap) / n

    # 各要素の座標範囲を計算
    segments = []
    current_pos = 0.0
    for _ in range(n):
        end_pos = current_pos + unit_len
        segments.append((round(current_pos, 4), round(end_pos, 4)))
        current_pos = end_pos + gap

        logger.debug("n={}, unit_len={}, segment={}", n, round(unit_len, 4), segments)

    return segments


class HoleInfo:
    """音符ごとの穴の情報。
    ホールの長さが bridge_threshold より長い場合は、分割する

    Attributes:
        note_info (NoteInfo): MIDIノート情報。
        conf (ModelConf): モデル設定情報。
        start_sec (float): ノートの開始時間（秒）。
        sec (float): ノートの長さ（秒）。
        scale (int): 対応するスケール番号（該当しない場合は -1）。
        x (float): X座標（mm単位）。
        y (float): Y座標（mm単位）。
        w (float): 穴の幅（mm単位）。
        h (float): 穴の高さ（mm単位）。
    """

    def __init__(self, note_info: NoteInfo, conf: ModelConf) -> None:
        """HoleInfoのインスタンスを初期化する。

        Args:
            note_info (NoteInfo): MIDIノート情報。
            conf (ModelConf): モデル設定情報。
        """
        # 項目が揃っていることは RollBook.__init__ が確かめている。
        # ここの既定値は、単体で使われたときの保険にすぎない
        self.note_info = note_info
        self.conf = conf

        self.start_sec = self.note_info.abs_time
        self.sec = self.note_info.length()

        base_note = self.conf.get('base_note', 0)
        notes = self.conf.get('notes', [])
        note_val = self.note_info.note if self.note_info.note is not None else -1
        self.scale = note2scale(note_val, base_note, notes)

        mm_per_sec = self.conf.get('mm_per_sec', 0.0)
        pitch = self.conf.get('pitch', 0.0)
        margin = self.conf.get('margin', 0.0)

        self.x = self.start_sec * mm_per_sec
        self.y = self.scale * pitch + margin
        self.w = self.sec * mm_per_sec
        self.h = self.conf.get('hole_height', 0.0)

        self.bridge_width = self.conf.get('bridge_width')
        self.bridge_threshold = self.conf.get('bridge_threshold')

        # 長い穴はブリッジ（紙のつなぎ）を挟んで分割する。
        # ここで一度だけ求めて svg() と hole_count が同じものを見る。
        self.segments = divide_length_by_max_len(
            self.w, self.bridge_threshold, self.bridge_width
        )

    def __str__(self) -> str:
        """オブジェクトの文字列表現を取得する。

        Returns:
            str: ノート情報や座標データを含むフォーマット済み文字列。
        """
        str_data = (
            f'note:{self.note_info.note:03d}'
            f' start_sec:{self.start_sec:07.2f}'
            f' sec:{self.sec:05.2f}'
        )
        str_data += f' scale:{self.scale:02d}'
        str_data += f' ({self.x:.2f}, {self.y:.2f})-({self.w:.2f}, {self.h:.2f})'
        return str_data

    def svg(self, color: str = HOLE_COLOR,
            stroke_dasharray: str = 'none') -> str:
        """穴描画用のSVGパス文字列を生成する。

        Args:
            color (str, optional): 線色。デフォルトは HOLE_COLOR（実線）。
                音階に無い音は OFF_SCALE_COLOR で呼ばれる。
            stroke_dasharray (str, optional): 破線のスタイル。デフォルトは 'none'。

        Returns:
            str: 生成されたSVGパス要素の文字列。
        """
        svg = ''
        for (x1, x2) in self.segments:
            logger.debug("({}, {})", x1, x2)

            svg += svg_square(
                self.x + x1, self.y, x2 - x1, self.h, color,
                stroke_dasharray=stroke_dasharray
            )

        logger.debug('svg={}', svg)
        return svg


class RollBook:
    """ロールブック（楽譜データ）全体の生成およびファイル出力を行うクラス。

    Attributes:
        DEF_MODEL_NAME (str): デフォルトのモデル名 ('34notes')。
        DEF_CONF_FILE (str): デフォルトの設定ファイルパス。
    """

    DEF_MODEL_NAME = '34notes'
    DEF_CONF_FILE = ''

    def __init__(
        self, model: str = DEF_MODEL_NAME, conf_file: str = DEF_CONF_FILE,
        transpose: int | str = 0,
    ) -> None:
        """RollBookインスタンスを初期化する。

        Args:
            model (str, optional): モデル名。
                デフォルトは DEF_MODEL_NAME。
            conf_file (str, optional): 設定ファイルのパス。
                デフォルトは DEF_CONF_FILE。
            transpose (int | str, optional): 移調する半音数（TODO-039）。
                ``'auto'`` を渡すと `parse()` が候補の 1 位を選ぶ。
                **実際に使われた値は `transpose` プロパティで読む。**

        Raises:
            ValueError: 機種が設定に無い、設定の項目が足りない、または
                `transpose` が整数にも ``'auto'`` にもならないとき。

        Note:
            **ここで弾かないと、静かに壊れた図が出る。** `Conf.get()` は
            知らない機種名に `{}` を返し、`HoleInfo` は足りない項目を
            既定値 0 で読むので、機種名を打ち間違えるだけで「高さ 0 の
            空のブック」が何事もなかったように生成されていた。
        """
        logger.info('model={}', model)

        self._model = model
        self._conf_file = conf_file
        logger.debug('model={},conf_file={}', self._model, self._conf_file)

        self._conf: ModelConf = Conf(self._conf_file).get(self._model)
        logger.debug('conf={}', json.dumps(self._conf))

        if not self._conf:
            raise ValueError(f"機種 '{model}' は設定にありません")

        valid, msg = validate_config(self._conf)
        if not valid:
            raise ValueError(f"機種 '{model}' の設定が不正です: {msg}")

        # 'auto' は parse() が候補から決める。それまでは要求のまま持つ
        self._transpose_req = self._check_transpose(transpose)
        self._transpose = 0 if self._transpose_req == 'auto' else int(
            self._transpose_req
        )
        self._candidates: list[TransposeCandidate] = []

        self._width = 0.0
        self._height = float(self._conf.get('book_height', 0.0))
        self._holes: list[HoleInfo] = []
        self._raw_note_count = 0
        self._svg = ''

        self._midi_parser = Parser()

    @staticmethod
    def _check_transpose(transpose: int | str) -> int | str:
        """`transpose` 引数を検証して、整数か ``'auto'`` に正規化する。

        **外から来る値。** CLI の `-t` と Web のフォームがそのまま渡すので、
        整数にならない文字列がありうる。ここで弾かないと、あとで静かに
        0 として扱われる。

        Raises:
            ValueError: 整数にも ``'auto'`` にもならないとき
                （メッセージはそのまま画面に出る）。
        """
        if isinstance(transpose, str):
            if transpose.strip().lower() == 'auto':
                return 'auto'
            try:
                return int(transpose)
            except ValueError as e:
                raise ValueError(
                    f"移調量 '{transpose}' は整数か 'auto' で指定してください"
                ) from e

        return int(transpose)

    # ブックの寸法。SVG 文字列を作らないと分からない値なので、
    # Web のビューアが初期倍率とスクロール位置を決めるのに使う。
    @property
    def width(self) -> float:
        """ブックの全長 [mm]。``parse()`` を呼ぶまでは 0.0。"""
        return self._width

    @property
    def height(self) -> float:
        """ブックの高さ [mm]（設定の ``'book_height'``）。"""
        return self._height

    # 穴の数は 2 段階で数える。
    #
    # 1. 音符の数 — MIDI から読んだ音符を `merge_overlapping_notes()` で
    #    まとめたあとの数（同じ MIDI ノート番号どうしの重なりは実機で
    #    1 本のパイプにしかならないため。TODO-038）
    # 2. 分割後の数 — 長い穴は `divide_length_by_max_len()` が
    #    `'bridge_threshold'` ごとに分割するので、音符 1 個が穴 2 個以上になる。
    #    実際に開ける数はこちら。同じ MIDI でも機種によって変わる
    #
    # さらに、オルガンの音階に無い音（`scale < 0`）は破線で描くだけで
    # **穴は開けない**ので、実線とは分けて数える。

    @property
    def note_count(self) -> int:
        """MIDI から読んだ音符の数（統合後。実線と破線の合計）。"""
        return len(self._holes)

    @property
    def merged_count(self) -> int:
        """`merge_overlapping_notes()` でまとめられて減った音符の数。

        0 なら重なりが無かった（＝統合の影響なし）。
        """
        return self._raw_note_count - self.note_count

    @property
    def transpose(self) -> int:
        """実際に移調した半音数（TODO-039）。

        ``'auto'`` を渡した場合も、`parse()` のあとは**選ばれた値**が入る。
        """
        return self._transpose

    @property
    def candidates(self) -> list[TransposeCandidate]:
        """移調の候補（鳴らせる音符の多い順）。`parse()` が埋める。

        移調を指定していなくても作る。**画面で比べてから選べるように
        するのが目的**なので、選ばなかった場合こそ要る。

        調ごとの最良（最大 12 行）に加えて、**±0（移調しない）**と
        **いま適用している移調量**の行が入る。`transpose_candidates()` は
        調ごとに「いちばん音域に収まるオクターブ」しか返さないので、
        これらは並ばないことが多い。**それだと表から ±0 に戻せなくなる**うえ、
        「移調しないと何 % なのか」も分からない。
        """
        return self._candidates

    @property
    def hole_note_count(self) -> int:
        """実線で描く音符の数（オルガンの音階にあるもの）。"""
        return sum(1 for hi in self._holes if hi.scale >= 0)

    @property
    def hole_count(self) -> int:
        """実際に開ける穴の数（実線をブリッジで分割したあと）。"""
        return sum(len(hi.segments) for hi in self._holes if hi.scale >= 0)

    @property
    def off_scale_note_count(self) -> int:
        """破線で描く音符の数（オルガンの音階に無いもの）。"""
        return sum(1 for hi in self._holes if hi.scale < 0)

    @property
    def off_scale_count(self) -> int:
        """破線を分割したあとの数。穴は開けないので、参考の値。"""
        return sum(len(hi.segments) for hi in self._holes if hi.scale < 0)

    @property
    def mm_per_sec(self) -> float:
        """秒 → mm の変換係数（設定の ``'mm_per_sec'``）。

        ビューアがスクロール位置を演奏時間に直すのに使う。
        """
        return float(self._conf.get('mm_per_sec', 0.0))

    # 履歴からこの SVG を出し直すときのために、**図からは求まらない値**を
    # 属性に埋めておく。寸法と穴の数は描かれているものから読めるが、
    # 音符の数（ブリッジで分割する前）は分割が多対一なので逆算できず、
    # 秒 → mm の係数はどこにも現れない。
    #
    # 読むのは `storage.book_from_svg()`（接頭辞は module 定数の META_PREFIX）。
    def _meta_attrs(self) -> str:
        """`<svg>` に付ける諸元の属性を組み立てる。"""
        meta = {
            'model': self._model,
            'mm-per-sec': f'{self.mm_per_sec:g}',
            'notes': str(self.note_count),
            'hole-notes': str(self.hole_note_count),
            'off-scale-notes': str(self.off_scale_note_count),
            'merged': str(self.merged_count),
            'transpose': str(self.transpose),
        }

        return ''.join(
            f' {META_PREFIX}{key}={quoteattr(value)}'
            for key, value in meta.items()
        )

    def svg(self) -> str:
        """ロールブック全体を描画するSVGドキュメント文字列を生成する。

        色と線の太さは module 定数で決まる（`BOOK_COLOR` / `HOLE_COLOR` /
        `OFF_SCALE_COLOR` / `DEF_LINE_WIDTH`）。**引数で差し替えられる形に
        してあったが、既定値以外で呼ばれたことは一度も無い。**
        色は `storage.book_from_svg()` が読み直す約束でもあるので、
        呼ぶ側ごとに変えられるほうがむしろ困る。

        Returns:
            str: 生成されたSVG形式のテキスト文字列。
        """
        svg = '<svg xmlns="http://www.w3.org/2000/svg"'
        svg += f' width="{self._width:.2f}mm" height="{self._height:.2f}mm"'
        svg += ' viewBox="'
        svg += f'{-self._width:.2f} {-self._height:.2f}'
        svg += f' {self._width:.2f} {self._height:.2f}'
        svg += '"'
        svg += self._meta_attrs()
        svg += '>\n'

        svg += svg_square(0, 0, self._width, self._height, BOOK_COLOR)

        for hi in self._holes:
            if hi.scale < 0:
                s1 = hi.svg(
                    color=OFF_SCALE_COLOR, stroke_dasharray=OFF_SCALE_DASH
                )
            else:
                s1 = hi.svg(color=HOLE_COLOR)

            svg += s1

        svg += '</svg>\n'
        return svg

    def parse(self, midi_file: str | Path, channel: list | None = None) -> str:
        """MIDIファイルを解析して穴情報を生成し、SVGデータを作成する。

        Args:
            midi_file (str | Path): 解析対象のMIDIファイルパス。
            channel (list | None, optional): 対象とするMIDIチャンネルのリスト
                （None または空リストの場合は全チャンネル）。デフォルトは None。

        Returns:
            str: 生成されたSVG形式のテキスト文字列。

        Note:
            **同じインスタンスで何度呼んでも同じ結果になる。** かつては
            `_holes` を初期化せずに追加していたので、2 回目は穴が二重になり、
            `_width` も `max()` で伸びたままだった。
        """
        if channel is None:
            channel = []
        logger.debug('midi_file={}', midi_file)

        # 前回の結果を捨てる。持ち越すと穴が二重になる
        self._width = 0.0
        self._holes = []
        self._raw_note_count = 0
        self._candidates = []
        self._svg = ''

        # ytmidilib は外部パッケージなので str に落として渡す
        midi = self._midi_parser.parse(str(midi_file), channel)
        logger.debug('midi[channel_set]={}', midi['channel_set'])

        self._raw_note_count = len(midi['note_info'])
        note_info = merge_overlapping_notes(midi['note_info'])
        logger.debug(
            'raw={}, merged={}', self._raw_note_count, len(note_info)
        )

        # 候補は**移調を指定していなくても**作る。画面で比べてから選べる
        # ようにするのが目的なので、選ばなかった場合こそ要る。
        self._candidates = transpose_candidates(note_info, self._conf)

        if self._transpose_req == 'auto':
            # 1 位を採る。候補が空（音符 0 個）なら移調しない
            self._transpose = (
                self._candidates[0]['transpose'] if self._candidates else 0
            )
            logger.info('transpose=auto -> {}', self._transpose)

        # 候補に無い移調量でも、次の 2 つは必ず行にする。
        #
        # - **±0（移調しない）** — 戻る先。無いと一度移調したら元に戻せない
        # - **いま適用している値** — 手で指定した値は候補に無いことがある
        self._candidates = add_transpose_rows(
            self._candidates, note_info, self._conf, (0, self._transpose)
        )

        if self._transpose:
            note_info = transpose_notes(note_info, self._transpose)

        for ni in note_info:
            hi = HoleInfo(ni, self._conf)
            logger.debug('hi={}', hi)

            if hi.scale >= 0:
                # ロールブックを伸ばす
                self._width = max(hi.x + hi.w, self._width)

            self._holes.append(hi)

        logger.debug('width={}, len(hole)={}', self._width, len(self._holes))

        svg = self.svg()
        return svg

    def parse_to_file(
            self, midi_file: str | Path, out_file: str | Path,
            channel: list | None = None
    ) -> str:
        """MIDIファイルを解析し、指定された出力ファイルへSVGデータを保存する。

        Args:
            midi_file (str | Path): 解析対象のMIDIファイルパス。
            out_file (str | Path): 出力先のSVGファイルパス。
            channel (list | None, optional): 対象とするMIDIチャンネルのリスト
                （None または空リストの場合は全チャンネル）。
                デフォルトは None。

        Returns:
            str: 生成されたSVG形式のテキスト文字列。
        """
        if channel is None:
            channel = []
        svg = self.parse(midi_file, channel)
        Path(out_file).write_text(svg, encoding='utf-8')
        logger.debug('svg written to {}', out_file)
        return svg
