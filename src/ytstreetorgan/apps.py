#
# (c) 2026 Yoichi Tanibayashi
#
"""
Application classes for ytstreetorgan CLI commands.

Separating business logic from click command definitions keeps
``__main__.py`` thin and makes these classes independently testable.
"""
from collections.abc import Sequence
from pathlib import Path

from loguru import logger
from ytmidilib import Parser, Player

from .rollbook import RollBook


class RollBookApp:
    """ RollBookApp """
    DEF_OUT_DIR = '~/Desktop'

    def __init__(
        self, midi_file: str, conf_file: str,
        model_name: str,
        channel: Sequence[int] = (),
        out_file: str | None = None,
    ) -> None:
        """ Constructor

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
        """ main """
        logger.debug('')

        self._rollbook.parse_to_file(
            self._midi_file, self._out_file, self._channel
        )

    def end(self) -> None:
        """ end ... do nothing """


class MidiApp:
    """ MidiApp """
    def __init__(self, midi_file: str,
                 channel: Sequence[int] = (),
                 parse_only: bool = False,
                 visual_flag: bool = False,
                 rate: int = Player.DEF_RATE,
                 sec_min: float = Player.SEC_MIN,
                 sec_max: float = Player.SEC_MAX,
                 pos_sec: float = 0.0,
                 debug: bool = False) -> None:
        """ Constructor """
        self._dbg = debug
        logger.debug('midi_file={}, channel={}', midi_file, channel)
        logger.debug('parse_only={}, visual_flag={}', parse_only, visual_flag)
        logger.debug('rate={}', rate)
        logger.debug('sec_min/max={}/{}', sec_min, sec_max)
        logger.debug('pos_sec={}', pos_sec)

        self._midi_file = midi_file
        self._channel = list(channel)
        self._parse_only = parse_only
        self._visual_flag = visual_flag
        self._rate = rate
        self._sec_min = sec_min
        self._sec_max = sec_max
        self._pos_sec = pos_sec

        self._parser = Parser(debug=self._dbg)
        self._player = Player(rate=self._rate, debug=self._dbg)

    def main(self) -> None:
        """ main """
        logger.debug('')

        parsed_data = self._parser.parse(self._midi_file, self._channel)

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
        """ end

        do nothing
        """
