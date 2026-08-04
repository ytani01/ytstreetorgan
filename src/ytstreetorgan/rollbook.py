#
# (c) 2026 Yoichi Tanibayashi
#
import json
import math
from pathlib import Path
from typing import TypedDict
from xml.sax.saxutils import quoteattr

from loguru import logger
from ytmidilib import NoteInfo, Parser

from .conf import Conf, ModelConf, NoteConf

DEF_LINE_WIDTH = 0.2


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


class DivisionResult(TypedDict):
    n: int
    unit_len: float
    segments: list[tuple[float, float]]


def divide_length_by_max_len(
    total_len: float, unit_len_max: float | None, gap: float | None = 1.0
) -> DivisionResult:
    """長さ total_len を 最大 unit_len_max間隔 で分割。間隔は gap。
    最少の分割数 n で分割する。

    Args:
        total_len (float): 全長[mm]
        unit_len_max (float|None): 1要素あたりの最大長さ[mm]
        gap (float|None): 要素間の間隔[mm], default = 1.0mm

    Returns:
        DivisionResult: 分割結果 (n, unit_len, segments)
    """
    logger.debug(
        'total_len={}, unit_len_max={}, gap={}',
        total_len, unit_len_max, gap
    )

    DEFAULT_RESULT: DivisionResult = {
        "n": 1,
        "unit_len": total_len,
        "segments": [(0, total_len)]
    }

    if total_len <= 0:
        logger.error('{} <=0', total_len)
        return DEFAULT_RESULT
    if unit_len_max is None or unit_len_max <= 0:
        logger.error('{} <= 0', unit_len_max)
        return DEFAULT_RESULT
    if gap is None or gap <= 0.0:
        return DEFAULT_RESULT

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
    return {
        "n": n,
        "unit_len": round(unit_len, 4),
        "segments": segments,
    }


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
        )['segments']

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

    def svg(self, color: str = '#FF0000', line_width: float = DEF_LINE_WIDTH,
            stroke_dasharray: str = 'none') -> str:
        """穴描画用のSVGパス文字列を生成する。

        Args:
            color (str, optional): 線色。デフォルトは '#FF0000'。
            line_width (float, optional): 線の太さ（mm単位）。
                デフォルトは DEF_LINE_WIDTH。
            stroke_dasharray (str, optional): 破線のスタイル。デフォルトは 'none'。

        Returns:
            str: 生成されたSVGパス要素の文字列。
        """
        svg = ''
        for (x1, x2) in self.segments:
            logger.debug("({}, {})", x1, x2)

            svg += svg_square(
                self.x + x1, self.y, x2 - x1, self.h, color, line_width,
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
        self, model: str = DEF_MODEL_NAME, conf_file: str = DEF_CONF_FILE
    ) -> None:
        """RollBookインスタンスを初期化する。

        Args:
            model (str, optional): モデル名。
                デフォルトは DEF_MODEL_NAME。
            conf_file (str, optional): 設定ファイルのパス。
                デフォルトは DEF_CONF_FILE。
        """
        logger.info('model={}', model)

        self._model = model
        self._conf_file = conf_file
        logger.debug('model={},conf_file={}', self._model, self._conf_file)

        self._conf: ModelConf = Conf(self._conf_file).get(self._model)
        logger.debug('conf={}', json.dumps(self._conf))

        self._width = 0.0
        self._height = float(self._conf.get('book_height', 0.0))
        self._holes: list[HoleInfo] = []
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
    # 1. 音符の数 — MIDI から読んだそのままの数
    # 2. 分割後の数 — 長い穴は `divide_length_by_max_len()` が
    #    `'bridge_threshold'` ごとに分割するので、音符 1 個が穴 2 個以上になる。
    #    実際に開ける数はこちら。同じ MIDI でも機種によって変わる
    #
    # さらに、オルガンの音階に無い音（`scale < 0`）は破線で描くだけで
    # **穴は開けない**ので、実線とは分けて数える。

    @property
    def note_count(self) -> int:
        """MIDI から読んだ音符の数（実線と破線の合計）。"""
        return len(self._holes)

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
    # 読むのは `storage.book_from_svg()`。名前を storgan- で始めているのは、
    # 他のツールが付けた属性と紛れないようにするため。
    META_PREFIX = 'data-storgan-'

    def _meta_attrs(self) -> str:
        """`<svg>` に付ける諸元の属性を組み立てる。"""
        meta = {
            'model': self._model,
            'mm-per-sec': f'{self.mm_per_sec:g}',
            'notes': str(self.note_count),
            'hole-notes': str(self.hole_note_count),
            'off-scale-notes': str(self.off_scale_note_count),
        }

        return ''.join(
            f' {self.META_PREFIX}{key}={quoteattr(value)}'
            for key, value in meta.items()
        )

    def svg(
        self, color: str = '#0000FF', hole_color: str = '#FF0000',
        line_width: float = DEF_LINE_WIDTH, stroke_dasharray: str = 'none'
    ) -> str:
        """ロールブック全体を描画するSVGドキュメント文字列を生成する。

        Args:
            color (str, optional): ブック外枠の線色。
                デフォルトは '#0000FF'。
            hole_color (str, optional): 穴の線色。
                デフォルトは '#FF0000'。
            line_width (float, optional): 線の太さ（mm単位）。
                デフォルトは DEF_LINE_WIDTH。
            stroke_dasharray (str, optional): 破線のスタイル。
                デフォルトは 'none'。

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

        svg += svg_square(
            0, 0, self._width, self._height,
            color, line_width, stroke_dasharray=stroke_dasharray
        )

        for hi in self._holes:
            if hi.scale < 0:
                s1 = hi.svg(color='#000000', stroke_dasharray='3 1')
            else:
                s1 = hi.svg(color=hole_color)

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
        """
        if channel is None:
            channel = []
        logger.debug('midi_file={}', midi_file)

        # ytmidilib は外部パッケージなので str に落として渡す
        midi = self._midi_parser.parse(str(midi_file), channel)
        logger.debug('midi[channel_set]={}', midi['channel_set'])

        for ni in midi['note_info']:
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
