#
# (c) 2026 Yoichi Tanibayashi
#
import json
from ytmidilib import NoteInfo, Parser
from loguru import logger
from .conf import Conf, ModelConf


DEF_LINE_WIDTH = 0.2


def note2scale(midi_note: int, base_note: int, note_offset: list[int]) -> int:
    """MIDIノート番号からスケール番号（インデックス）を取得する。

    Args:
        midi_note (int): 対象のMIDIノート番号。
        base_note (int): 基準となるベースノート番号。
        note_offset (list[int]): 各スケールに対するノートのオフセット値のリスト。

    Returns:
        int: 対応するスケール番号（インデックス）。該当するものがない場合は -1。
    """
    scale = -1

    for s, offset in enumerate(note_offset):
        if base_note + offset == midi_note:
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
        stroke_dasharray (str, optional): 破線のスタイル（例: 'none', '3 1'）。デフォルトは 'none'。
        hairline (bool, optional): ヘアライン指定。デフォルト 'True'

    Returns:
        str: 生成されたSVGパス要素の文字列。
    """
    style_str:str = 'fill:none;'
    style_str += f'stroke:{color};'
    style_str += f'stroke-width:{line_width};'
    style_str += f'stroke-dasharray:{stroke_dasharray};'
    if hairline:
        style_str += 'vector-effect:non-scaling-stroke;'
        style_str += '-inkscape-stroke:hairline;'

    d_str:str = f'M {-x:.2f},{-y:.2f} h {-w:.2f} v {-h:.2f} h {w:.2f} Z'

    svg:str = f'<path style="{style_str}" d="{d_str}" />'

    return svg


class HoleInfo:
    """ロールブックの穴情報を管理するデータエンティティクラス。

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

        base_note = self.conf.get('base note', 0)
        note_offset = self.conf.get('note offset', [])
        note_val = self.note_info.note if self.note_info.note is not None else -1
        self.scale = note2scale(note_val, base_note, note_offset)

        sec_per_sec = self.conf.get('1sec', 0.0)
        pitch = self.conf.get('pitch', 0.0)
        margin = self.conf.get('margin', 0.0)
        hole_height = self.conf.get('hole height', 0.0)

        self.x = self.start_sec * sec_per_sec
        self.y = self.scale * pitch + margin
        self.w = self.sec * sec_per_sec
        self.h = hole_height

    def __str__(self) -> str:
        """オブジェクトの文字列表現を取得する。

        Returns:
            str: ノート情報や座標データを含むフォーマット済み文字列。
        """
        str_data = 'note:%03d start_sec:%07.2f sec:%05.2f' % (
            self.note_info.note, self.start_sec, self.sec
        )
        str_data += ' scale:%02d' % (self.scale)
        str_data += ' (%.2f, %.2f)-(%.2f, %.2f)' % (
            self.x, self.y, self.w, self.h
        )
        return str_data

    def svg(self, color: str = '#FF0000', line_width: float = DEF_LINE_WIDTH,
            stroke_dasharray: str = 'none') -> str:
        """穴描画用のSVGパス文字列を生成する。

        Args:
            color (str, optional): 線色。デフォルトは '#FF0000'。
            line_width (float, optional): 線の太さ（mm単位）。デフォルトは DEF_LINE_WIDTH。
            stroke_dasharray (str, optional): 破線のスタイル。デフォルトは 'none'。

        Returns:
            str: 生成されたSVGパス要素の文字列。
        """
        svg = svg_square(
            self.x, self.y, self.w, self.h, color, line_width,
            stroke_dasharray=stroke_dasharray
        )

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
        self._height = float(self._conf.get('book height', 0.0))
        self._holes: list[HoleInfo] = []
        self._svg = ''

        self._midi_parser = Parser()

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
        svg += '">\n'

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

    def parse(self, midi_file: str, channel: list = []) -> str:
        """MIDIファイルを解析して穴情報を生成し、SVGデータを作成する。

        Args:
            midi_file (str): 解析対象のMIDIファイルパス。
            channel (list, optional): 対象とするMIDIチャンネルのリスト
                （空リストの場合は全チャンネル）。デフォルトは []。

        Returns:
            str: 生成されたSVG形式のテキスト文字列。
        """
        logger.debug('midi_file={}', midi_file)

        midi = self._midi_parser.parse(midi_file, channel)
        logger.debug('midi[channel_set]={}', midi['channel_set'])

        for ni in midi['note_info']:
            hi = HoleInfo(ni, self._conf)
            logger.debug('hi={}', hi)

            if hi.scale >= 0:
                self._width = max(hi.x + hi.w, self._width)

            self._holes.append(hi)

        logger.debug('width={}, len(hole)={}', self._width, len(self._holes))

        svg = self.svg()
        return svg

    def parse_to_file(
            self, midi_file: str, out_file: str, channel: list = []
    ) -> str:
        """MIDIファイルを解析し、指定された出力ファイルへSVGデータを保存する。

        Args:
            midi_file (str): 解析対象のMIDIファイルパス。
            out_file (str): 出力先のSVGファイルパス。
            channel (list, optional): 対象とするMIDIチャンネルのリスト
                （空リストの場合は全チャンネル）。
                デフォルトは []。

        Returns:
            str: 生成されたSVG形式のテキスト文字列。
        """
        svg = self.parse(midi_file, channel)
        with open(out_file, mode='w') as f:
            f.write(svg)
        logger.debug('svg written to {}', out_file)
        return svg
