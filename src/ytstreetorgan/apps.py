#
# (c) 2026 Yoichi Tanibayashi
#
"""CLI の各サブコマンドの中身。

**`__main__.py` は click の定義だけの薄い層に保つ**という決めごとがある
（テストしやすくするため）。ロジックはここに置く。
"""
from collections.abc import Sequence
from pathlib import Path

from loguru import logger
from ytmidilib import NoteInfo, Parser, Player

from .conf import Conf, ModelConf, validate_config
from .rollbook import RollBook, merge_overlapping_notes, note2scale


class RollBookApp:
    """`rollbook` コマンド。MIDI から SVG を作ってファイルに書く。

    Attributes:
        DEF_OUT_DIR: `-o` を省略したときの出力先。
    """
    DEF_OUT_DIR = '~/Desktop'

    def __init__(
        self, midi_file: str, conf_file: str,
        model_name: str,
        channel: Sequence[int] = (),
        out_file: str | None = None,
    ) -> None:
        """出力先を決めて、`RollBook` を用意する。

        Args:
            midi_file (str): 対象の MIDI ファイル。
            conf_file (str): 設定ファイル。空なら `Conf` が探す。
            model_name (str): 機種名。
            channel (Sequence[int]): 対象の MIDI チャンネル（空なら全部）。
            out_file (str | None): 出力先。**省略すると
                `DEF_OUT_DIR` に「MIDI 名 + .svg」で書く。**

        Note:
            version と debug は受け取っていたが使っていなかったので外した
            （ログの初期化は `__main__` の `loggerInit()` が済ませている）。
        """
        logger.debug('midi_file={}, conf_file={}', midi_file, conf_file)
        logger.debug('model_name={}', model_name)
        logger.debug('channel={}', channel)
        logger.debug('out_file={}', out_file)

        self._midi_file = midi_file
        self._conf_file = conf_file
        self._model_name = model_name
        self._channel = list(channel)

        if out_file:
            # 明示指定されたパスはそのまま使う（相対パスは cwd 基準）
            self._out_file = str(Path(out_file).expanduser())
        else:
            # 未指定なら DEF_OUT_DIR に <MIDIファイル名>.svg で出す
            name = Path(f'{self._midi_file}.svg').name
            self._out_file = str((Path(self.DEF_OUT_DIR) / name).expanduser())
        logger.debug('[fix] out_file={}', self._out_file)

        self._rollbook = RollBook(self._model_name, self._conf_file)

    def main(self) -> None:
        """MIDI を解析して SVG を書き出す。"""
        logger.debug('')

        self._rollbook.parse_to_file(
            self._midi_file, self._out_file, self._channel
        )

    def end(self) -> None:
        """後片付け（いまは何もしない）。`main()` と対で呼ぶ。"""


class MidiApp:
    """`parse` と `play` コマンド。MIDI を解析して、表示または再生する。"""
    def __init__(self, midi_file: str,
                 channel: Sequence[int] = (),
                 parse_only: bool = False,
                 visual_flag: bool = False,
                 rate: int = Player.DEF_RATE,
                 sec_min: float = Player.SEC_MIN,
                 sec_max: float = Player.SEC_MAX,
                 pos_sec: float = 0.0,
                 model_name: str | None = None,
                 conf_file: str = RollBook.DEF_CONF_FILE,
                 debug: bool = False) -> None:
        """解析器と再生器を用意する。

        Args:
            midi_file (str): 対象の MIDI ファイル。
            channel (Sequence[int]): 対象の MIDI チャンネル（空なら全部）。
            parse_only (bool): 解析結果を出すだけで再生しない（`parse`）。
            visual_flag (bool): 解析結果を図にして出す。
            rate (int): 再生のサンプリング周波数 [Hz]。
            sec_min (float): 音の長さの下限 [秒]。
            sec_max (float): 音の長さの上限 [秒]。
            pos_sec (float): 再生を始める位置 [秒]。
            model_name (str | None): 機種名。指定すると、その機種の音階に
                無い MIDI ノート番号を再生前に取り除く（ロールブックで
                穴が開かないのと同じ音だけを鳴らす）。`None` なら変換しない。
            conf_file (str): 設定ファイル。空なら `Conf` が探す。
                `model_name` を指定したときだけ使う。
            debug (bool): 解析器と再生器にそのまま渡す。

        Raises:
            ValueError: `model_name` を指定したのに設定に無い、または
                設定の項目が足りないとき（`RollBook.__init__` と同じ理由）。
        """
        self._dbg = debug
        logger.debug('midi_file={}, channel={}', midi_file, channel)
        logger.debug('parse_only={}, visual_flag={}', parse_only, visual_flag)
        logger.debug('rate={}', rate)
        logger.debug('sec_min/max={}/{}', sec_min, sec_max)
        logger.debug('pos_sec={}', pos_sec)
        logger.debug('model_name={}, conf_file={}', model_name, conf_file)

        self._midi_file = midi_file
        self._channel = list(channel)
        self._parse_only = parse_only
        self._visual_flag = visual_flag
        self._rate = rate
        self._sec_min = sec_min
        self._sec_max = sec_max
        self._pos_sec = pos_sec

        self._model_name = model_name
        self._model_conf: ModelConf | None = None
        if self._model_name:
            conf = Conf(conf_file).get(self._model_name)
            if not conf:
                raise ValueError(f"機種 '{self._model_name}' は設定にありません")

            valid, msg = validate_config(conf)
            if not valid:
                raise ValueError(
                    f"機種 '{self._model_name}' の設定が不正です: {msg}"
                )
            self._model_conf = conf

        self._parser = Parser(debug=self._dbg)
        self._player = Player(rate=self._rate, debug=self._dbg)

    def _convert_for_model(self, note_info: list[NoteInfo]) -> list[NoteInfo]:
        """その機種の音階に無い MIDI ノート番号を取り除き、重なりをまとめる。

        ロールブックはこうした音を破線で描くだけで穴を開けない
        （`HoleInfo.scale` が -1）。再生でも同じ音だけを鳴らして、
        実機で聞こえる音を確かめられるようにする。

        あわせて `merge_overlapping_notes()` で、同じ MIDI ノート番号の
        重なりを 1 つにまとめる（TODO-038）。実機は 1 つの音に 1 本の
        パイプしか無いため、複数パートが同じ高さを同時に鳴らしても
        実際に聞こえるのは 1 本ぶんになる。
        """
        assert self._model_conf is not None

        base_note = self._model_conf.get('base_note', 0)
        notes = self._model_conf.get('notes', [])

        merged = merge_overlapping_notes(note_info)
        converted = [
            ni for ni in merged
            if note2scale(ni.note, base_note, notes) >= 0
        ]

        logger.info(
            '[{}] {} -> {} (merge) -> {} (scale)', self._model_name,
            len(note_info), len(merged), len(converted)
        )
        return converted

    def main(self) -> None:
        """解析し、必要なら図にして出し、`parse_only` でなければ再生する。"""
        logger.debug('')

        parsed_data = self._parser.parse(self._midi_file, self._channel)

        if self._model_conf is not None:
            parsed_data['note_info'] = self._convert_for_model(
                parsed_data['note_info']
            )

        logger.debug('parsed_data=')
        if self._dbg or self._parse_only:
            for i, data in enumerate(parsed_data['note_info']):
                print(f'({i:4d}) {data}', flush=True)

        print('channel_set=', parsed_data['channel_set'], flush=True)

        if self._visual_flag:
            v_data = self._parser.mk_visual(parsed_data['note_info'])
            print()
            self._parser.print_visual(v_data, parsed_data['channel_set'])

        if self._parse_only:
            return

        self._player.play(parsed_data, self._pos_sec,
                          self._sec_min, self._sec_max)

    def end(self) -> None:
        """後片付け（いまは何もしない）。`main()` と対で呼ぶ。"""
