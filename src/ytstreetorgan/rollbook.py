#
# (c) 2026 Yoichi Tanibayashi
#
import json
from ytmidilib import NoteInfo, Parser
from loguru import logger
from .conf import Conf


DEF_LINE_WIDTH = 0.1


def note2scale(midi_note, base_note, note_offset=[]) -> int:
    """
    Parameters
    ----------
    midi_note: int
    base_note: int
    note_offset: list of int

    Returns
    -------
    scale: int
    """
    scale = -1

    for s, offset in enumerate(note_offset):
        if base_note + offset == midi_note:
            scale = s
            break

    return scale


def svg_square(x, y, w, h, color, line_width=DEF_LINE_WIDTH,
               stroke_dasharray='none') -> str:
    """
    Parameters
    ----------
    x, y, w, h: float
    color: str
    line_width: float
    stroke_dasharray: str

    Returns
    -------
    svg: str

    """
    svg = '<path style="'
    svg += 'fill:none;'
    svg += 'stroke:%s;' % (color)
    svg += 'stroke-width:%s;' % (line_width)
    svg += 'stroke-dasharray:%s"' % (stroke_dasharray)
    svg += ' d="M %.2f %.2f h %.2f v %.2f h %.2f Z" />\n' % (
        -x, -y, -w, -h, w)

    return svg


class HoleInfo:
    """
    Roll Book Hole data entity

    Attributes
    ----------
    note_info: ytmidilib.NoteInfo
        MIDI note information
    sec: float
        length in sec
    scale: int
        scale number
    x, y, w, h: float
        coordinate in mm
    """
    def __init__(self, note_info: NoteInfo, conf: dict):
        self.note_info = note_info
        self.conf = conf

        self.start_sec = self.note_info.abs_time
        self.sec = self.note_info.length()
        self.scale = note2scale(self.note_info.note,
                                self.conf['base note'],
                                self.conf['note offset'])

        self.x = self.start_sec * self.conf['1sec']
        self.y = self.scale * self.conf['pitch'] + self.conf['margin']
        self.w = self.sec * self.conf['1sec']
        self.h = self.conf['hole height']

    def __str__(self):
        """ __str__ """
        str_data = 'note:%03d start_sec:%07.2f sec:%05.2f' % (
            self.note_info.note, self.start_sec, self.sec)
        str_data += ' scale:%02d' % (self.scale)
        str_data += ' (%.2f, %.2f)-(%.2f, %.2f)' % (
            self.x, self.y, self.w, self.h)
        return str_data

    def svg(self, color='#FF0000', line_width=DEF_LINE_WIDTH,
            stroke_dasharray='none'):
        """ generate SVG

        Parameters
        ----------
        color: str
        line_width: float
        stroke_dasharray: str

        Returns
        -------
        svg: str
            SVG data
        """
        svg = svg_square(self.x, self.y, self.w, self.h,
                         color, line_width,
                         stroke_dasharray=stroke_dasharray)

        return svg


class RollBook:
    """ RollBook class
    """
    DEF_MODEL_NAME = '34notes'
    DEF_CONF_FILE = ''

    def __init__(
        self, model: str = DEF_MODEL_NAME, conf_file: str = DEF_CONF_FILE
    ):
        """ Constructor

        Parameters
        ----------
        model: str
            Model Name
        conf_file: str
        """
        logger.info('model={}', model)

        self._model = model
        self._conf_file = conf_file
        logger.debug('model={},conf_file={}', self._model, self._conf_file)

        self._conf = Conf(self._conf_file).get(self._model)
        logger.debug('conf={}', json.dumps(self._conf))

        self._width = 0
        self._height = self._conf['book height']
        self._holes: list[HoleInfo] = []
        self._svg = ''

        self._midi_parser = Parser()

    def svg(self, color='#0000FF', hole_color='#FF0000',
            line_width=DEF_LINE_WIDTH, stroke_dasharray='none'):
        """ generate SVG

        Parameters
        ----------
        color: str
        hole_color: str
        line_width: float
        stroke_dasharray: str

        Returns
        -------
        svg: str
            SVG data
        """
        svg = '<svg xmlns="http://www.w3.org/2000/svg"'
        svg += ' width="%.2fmm" height="%.2fmm"' % (
            self._width, self._height)
        svg += ' viewBox="%s %s %s %s">\n' % (
            -self._width, -self._height, self._width, self._height)
        # svg += '<g id="all">\n'

        svg += svg_square(0, 0, self._width, self._height,
                          color, line_width,
                          stroke_dasharray=stroke_dasharray)

        for hi in self._holes:
            if hi.scale < 0:
                s1 = hi.svg(color='#000000', stroke_dasharray='3 1')
            else:
                s1 = hi.svg(color=hole_color)

            svg += s1

        # svg += '</g>\n'
        svg += '</svg>\n'
        return svg

    def parse(self, midi_file, channel=[]):
        """
        Parameters
        ----------
        midi_file: str
            MIDI file name
        channel: list of int
            selected MIDI channel ([]: all)

        Returns
        -------
        svg: str
            SVG data (text)
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

    def parse_to_file(self, midi_file: str, out_file: str, channel: list = []) -> str:
        """
        Parse MIDI and write the resulting SVG directly to a file.

        Parameters
        ----------
        midi_file: str
            Path to the MIDI file.
        out_file: str
            Path to write the SVG output.
        channel: list of int
            Selected MIDI channels ([] = all).

        Returns
        -------
        svg: str
            The generated SVG data.
        """
        svg = self.parse(midi_file, channel)
        with open(out_file, mode='w') as f:
            f.write(svg)
        logger.debug('svg written to {}', out_file)
        return svg
