#
# (c) 2026 Yoichi Tanibayashi
#
import json
import math
from pathlib import Path
from typing import Literal
from xml.sax.saxutils import quoteattr

from loguru import logger
from ytmidilib import NoteInfo, Parser

from .conf import Conf, ModelConf, NoteConf, validate_config
from .transpose import (
    TransposeCandidate,
    parse_transpose_arg,
    plan_transpose,
)

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
        self.scale = note2scale(self.note_info.note, base_note, notes)

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

        # 'auto' は parse() が候補から決める。それまでは要求のまま持つ。
        # **型注釈は省かないこと。** 省くと属性の型を推論するときに
        # `Literal['auto']` が `str` へ広げられ、`plan_transpose()` に
        # 渡せなくなる（basedpyright が拾う）
        self._transpose_req: int | Literal['auto'] = parse_transpose_arg(
            transpose
        )
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

        `select_transpose_rows()` で絞ったもの（TODO-041）。±0 より
        改善する候補のうち上位 5 個に、**±0（移調しない）**と
        **いま適用している移調量**を必ず加えてある。±0 が無いと表から
        戻せなくなるうえ、「移調しないと何 % なのか」も分からない。
        """
        return self._candidates

    @property
    def playable_note_info(self) -> list[NoteInfo]:
        """実機で実際に鳴る音符（`load()` を呼ぶまでは空）。

        重なりの統合（`merge_overlapping_notes()`。TODO-038）と移調
        （`plan_transpose()`）を経たあと、**機種の音階にある音だけ**を
        残したもの。実線で描く穴（`scale >= 0`）と 1 対 1 に対応する。

        ブラウザでの試聴（TODO-063）が、鳴らす音符としてこれを使う。
        **絞り込みは移調したあとでなければ決まらない**ので、順番は
        `load()` の中の 1 通りだけにしてある（TODO-043 と同じ理由）。
        """
        return [hi.note_info for hi in self._holes if hi.scale >= 0]

    @property
    def hole_note_count(self) -> int:
        """実線で描く音符の数（オルガンの音階にあるもの）。"""
        return len(self.playable_note_info)

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

    def load(self, midi_file: str | Path, channel: list | None = None) -> None:
        """MIDIファイルを解析して、穴の情報と移調の候補を作る（SVG は作らない）。

        `parse()` から切り出したもの（TODO-063）。ブラウザでの試聴は
        鳴らす音符（`playable_note_info`）だけが要るので、**SVG を
        組み立てずにここまでで止められる**ようにしてある。
        **`parse()` の手順はここに 1 通りだけ**（写さないこと）。

        Args:
            midi_file (str | Path): 解析対象のMIDIファイルパス。
            channel (list | None, optional): 対象とするMIDIチャンネルのリスト
                （None または空リストの場合は全チャンネル）。デフォルトは None。

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

        midi = self._midi_parser.parse(midi_file, channel)
        logger.debug('midi[channel_set]={}', midi['channel_set'])

        self._raw_note_count = len(midi['note_info'])
        note_info = merge_overlapping_notes(midi['note_info'])
        logger.debug(
            'raw={}, merged={}', self._raw_note_count, len(note_info)
        )

        # 移調をどうするかは `plan_transpose()` が決める（TODO-043）。
        # `MidiApp`（`play`）も同じものを呼ぶので、手順はここに写さない。
        # 候補は**移調を指定していなくても**作られる。画面で比べてから
        # 選べるようにするのが目的なので、選ばなかった場合こそ要る。
        plan = plan_transpose(note_info, self._conf, self._transpose_req)
        self._transpose = plan.transpose
        self._candidates = plan.candidates
        note_info = plan.notes

        for ni in note_info:
            hi = HoleInfo(ni, self._conf)
            logger.debug('hi={}', hi)

            if hi.scale >= 0:
                # ロールブックを伸ばす
                self._width = max(hi.x + hi.w, self._width)

            self._holes.append(hi)

        logger.debug('width={}, len(hole)={}', self._width, len(self._holes))

    def parse(self, midi_file: str | Path, channel: list | None = None) -> str:
        """MIDIファイルを解析して穴情報を生成し、SVGデータを作成する。

        中身は `load()`（解析）＋ `svg()`（描画）。**呼ぶ側から見た
        振る舞いは切り出す前と同じ。**

        Args:
            midi_file (str | Path): 解析対象のMIDIファイルパス。
            channel (list | None, optional): 対象とするMIDIチャンネルのリスト
                （None または空リストの場合は全チャンネル）。デフォルトは None。

        Returns:
            str: 生成されたSVG形式のテキスト文字列。
        """
        self.load(midi_file, channel)
        return self.svg()

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
