#
# (c) 2021 Yoichi Tanibayashi
#
"""
main for midi_tools
"""
import os
import click
from loguru import logger
from ytmidilib import Parser, Player
from . import RollBook, WebServer
from .mylog import loggerInit


class RollBookApp:
    """ RollBookApp """
    DEF_OUT_DIR = '~/Desktop'

    def __init__(self, midi_file, conf_file,
                 model_name,
                 channel=[],
                 out_file=None,
                 version='current',
                 debug=False):
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

        self._rollbook = RollBook(self._model_name, self._conf_file,
                                  debug=self._dbg)

    def main(self):
        """ main """
        logger.debug('')

        svg = self._rollbook.parse(self._midi_file, self._channel)

        with open(self._out_file, mode='w') as f:
            f.write(svg)

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

        self._log.debug('parsed_data=')
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


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(invoke_without_command=True,
             context_settings=CONTEXT_SETTINGS, help='''
storgan Apps
''')
@click.pass_context
def cli(ctx):
    """ click group """
    loggerInit(True)
    logger.debug(ctx)
    
    subcmd = ctx.invoked_subcommand

    if subcmd is None:
        print(ctx.get_help())
    else:
        pass


@cli.command(help="""
Web server""")
@click.option('--port', '-p', 'port', type=int,
              default=WebServer.DEF_PORT,
              help='port number')
@click.option('--webroot', '-r', 'webroot', type=click.Path(exists=True),
              default=WebServer.DEF_WEBROOT,
              help='Web root directory')
@click.option('--workdir', '-w', 'workdir', type=click.Path(),
              default=WebServer.DEF_WORKDIR,
              help='work directory')
@click.option('--size_limit', '-l', 'size_limit', type=int,
              default=100*1024*1024,
              help='upload size limit, default=%s' % (
                  WebServer.DEF_SIZE_LIMIT))
@click.option('--version', 'version', type=str, default='current',
              help='version string')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def webapp(port, webroot, workdir, size_limit, version, debug):
    """ cmd1  """
    loggerInit(debug)

    app = WebServer(port, webroot, workdir, size_limit, version,
                    debug=debug)
    try:
        app.main()
    finally:
        logger.info('end')


@cli.command(context_settings=CONTEXT_SETTINGS, help='''
Roll Book
''')
@click.argument('midi_file', type=click.Path(exists=True))
@click.option('--conf_file', '-f', 'conf_file',
              type=click.Path(exists=True),
              default='%s' % (RollBook.DEF_CONF_FILE),
              help='configuration file')
@click.option('--model', '-m', 'model_name', type=str,
              default='ModelName',
              help='Model Name')
@click.option('--channel', '-c', 'channel', type=int, multiple=True,
              help='MIDI channel')
@click.option('--version', 'version', type=str, default='current',
              help='version string')
@click.option('--debug', '-d', 'dbg', is_flag=True, default=False,
              help='debug flag')
def rollbook(midi_file, conf_file, model_name, channel, version,
             dbg) -> None:
    """
    rollbook main
    """
    loggerInit(dbg)

    app = RollBookApp(midi_file, conf_file, model_name, channel,
                      version, debug=dbg)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()


@cli.command(context_settings=CONTEXT_SETTINGS, help='''
MIDI parser
''')
@click.argument('midi_file', type=click.Path(exists=True))
@click.option('--channel', '-c', 'channel', type=int, multiple=True,
              help='MIDI channel')
@click.option('--visual', '-v', 'visual_flag', is_flag=True,
              default=False,
              help='Visual flag')
@click.option('--debug', '-d', 'dbg', is_flag=True, default=False,
              help='debug flag')
def parse(midi_file, channel, visual_flag, dbg) -> None:
    """
    parser main
    """
    loggerInit(dbg)

    app = MidiApp(midi_file, channel, parse_only=True,
                  visual_flag=visual_flag,
                  debug=dbg)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()


@cli.command(context_settings=CONTEXT_SETTINGS, help='''
MIDI player
''')
@click.argument('midi_file', type=click.Path(exists=True))
@click.option('--pos_sec', '-s', 'pos_sec', type=float, default=0,
              help='seek position in sec')
@click.option('--channel', '-c', 'channel', type=int, multiple=True,
              help='MIDI channel')
@click.option('--rate', '-r', 'rate', type=int,
              default=Player.DEF_RATE,
              help='sampling rate, default=%s Hz' % Player.DEF_RATE)
@click.option('--sec_min', '--min', 'sec_min', type=float,
              default=Player.SEC_MIN,
              help='min sound length, default=%s' % (Player.SEC_MIN))
@click.option('--sec_max', '--max', 'sec_max', type=float,
              default=Player.SEC_MAX,
              help='max sound length, default=%s' % (Player.SEC_MAX))
@click.option('--debug', '-d', 'dbg', is_flag=True, default=False,
              help='debug flag')
def play(midi_file,  # pylint: disable=too-many-arguments
         pos_sec, channel, rate, sec_min, sec_max, dbg) -> None:
    """
    player main
    """
    loggerInit(dbg)

    app = MidiApp(midi_file, channel, parse_only=False,
                  visual_flag=False, rate=rate,
                  sec_min=sec_min, sec_max=sec_max, pos_sec=pos_sec,
                  debug=dbg)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()


if __name__ == '__main__':
    cli(prog_name='Storgan')
