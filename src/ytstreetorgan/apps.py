#
# (c) 2026 Yoichi Tanibayashi
#
"""
Application classes for ytstreetorgan CLI commands.

Separating business logic from click command definitions keeps
``__main__.py`` thin and makes these classes independently testable.
"""
import os
from loguru import logger

from ytmidilib import Parser, Player
from .rollbook import RollBook


class RollBookApp:
    """ RollBookApp """
    DEF_OUT_DIR = '~/Desktop'

    def __init__(
        self, midi_file, conf_file,
        model_name,
        channel=[],
        out_file=None,
        version='current',
        debug=False
    ):
        """ Constructor """
        self._dbg = debug
        logger.debug('midi_file={}, conf_file={}', midi_file, conf_file)
        logger.debug('model_name={}', model_name)
        logger.debug('channel={}', channel)
        logger.debug('out_file={}', out_file)
        logger.debug('version={}', version)

        self._midi_file = midi_file
        self._conf_file = conf_file
        self._model_name = model_name
        self._channel = channel
        self._version = version

        if not out_file:
            out_file = '%s.svg' % (self._midi_file)

        out_file = os.path.basename(out_file)
        out_file = '%s/%s' % (self.DEF_OUT_DIR, out_file)
        self._out_file = os.path.expanduser(out_file)
        logger.debug('[fix] out_file={}', self._out_file)

        self._rollbook = RollBook(self._model_name, self._conf_file)

    def main(self):
        """ main """
        logger.debug('')

        self._rollbook.parse_to_file(
            self._midi_file, self._out_file, self._channel
        )

    def end(self) -> None:
        """ end ... do nothing """


class MidiApp:  # pylint: disable=too-many-instance-attributes
    """ MidiApp """
    def __init__(self, midi_file,  # pylint: disable=too-many-arguments
                 channel,
                 parse_only=False,
                 visual_flag=False,
                 rate=Player.DEF_RATE,
                 sec_min=Player.SEC_MIN, sec_max=Player.SEC_MAX,
                 pos_sec=0,
                 debug=False) -> None:
        """ Constructor """
        self._dbg = debug
        logger.debug('midi_file={}, channel={}', midi_file, channel)
        logger.debug('parse_only={}, visual_flag={}', parse_only, visual_flag)
        logger.debug('rate={}', rate)
        logger.debug('sec_min/max={}/{}', sec_min, sec_max)
        logger.debug('pos_sec={}', pos_sec)

        self._midi_file = midi_file
        self._channel = channel
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
                print('(%4d) %s' % (i, data), flush=True)

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
