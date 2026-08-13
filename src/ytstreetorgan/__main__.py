#
# (c) 2026 Yoichi Tanibayashi
#
"""CLI の入口（Storgan）。

**この層は薄く保つ。** click の定義だけを置き、中身は :mod:`apps` の
アプリクラスに任せる（テストしやすくするため）。
"""
import click
from ytmidilib import Player

from . import __version__
from .apps import MidiApp, RollBookApp
from .click_utils import click_common_opts
from .mylog import getLogger, loggerInit
from .rollbook import RollBook
from .webapp import WebServer

_log = getLogger('main')

"""
# click コマンド群
"""


@click.group()
@click_common_opts(__version__)
def cli(ctx, debug):
    """MIDI から手回しオルガン用のロールブックを作る。"""
    loggerInit(debug)
    _log.debug(ctx)
    _log.debug(debug)

    subcmd = ctx.invoked_subcommand

    if subcmd is None:
        print(ctx.get_help())
    else:
        pass


@cli.command()
@click.option('--port', '-p', 'port', type=int,
              default=WebServer.DEF_PORT, show_default=True,
              help='port number')
@click.option('--urlprefix', '-u', 'urlprefix', type=str,
              default=WebServer.URL_PREFIX, show_default=True,
              help='URL prefix')
@click.option('--webroot', '-r', 'webroot', type=click.Path(exists=True),
              default=WebServer.DEF_WEBROOT, show_default=True,
              help='Web root directory')
@click.option('--workdir', '-w', 'workdir', type=click.Path(),
              default=WebServer.DEF_WORKDIR, show_default=True,
              help='work directory')
@click.option('--size_limit', '-l', 'size_limit', type=int,
              default=WebServer.DEF_SIZE_LIMIT, show_default=True,
              help=f'upload size limit, default={WebServer.DEF_SIZE_LIMIT}')
@click_common_opts(__version__)
def webapp(ctx, port, urlprefix, webroot, workdir, size_limit, debug):
    """Web サーバーを起動する（--debug でブラウザの live reload も有効）。"""
    loggerInit(debug)
    _log.debug('command={!r}', ctx.command.name)
    _log.debug("__version__={}", __version__)

    app = WebServer(port, urlprefix, webroot, workdir, size_limit, debug=debug)
    try:
        app.main()
    finally:
        _log.info('end')


@cli.command()
@click.argument('midi_file', type=click.Path(exists=True))
@click.option(
    '--conf_file', '-f', 'conf_file',
    type=click.Path(exists=False),
    default=RollBook.DEF_CONF_FILE,
    show_default=True,
    help='configuration file'
)
@click.option(
    '--model', '-m', 'model_name', type=str,
    default=RollBook.DEF_MODEL_NAME,
    show_default=True,
    help='Model Name'
)
@click.option(
    '--channel', '-c', 'channel', type=int, multiple=True,
    help='MIDI channel'
)
@click.option(
    '--out_file', '-o', 'out_file', type=click.Path(),
    default=None,
    help='Output SVG file path'
)
@click.option(
    '--transpose', '-t', 'transpose', type=str,
    default='0', show_default=True,
    help="移調する半音数。'auto' で鳴らせる音符が最多になる値を選ぶ"
)
@click_common_opts(__version__)
def rollbook(
    ctx, midi_file, conf_file, model_name, channel, out_file, transpose, debug
) -> None:
    """MIDI からロールブックの SVG を作る（-o 省略時は ~/Desktop）。"""
    loggerInit(debug)
    _log.debug('command={!r}', ctx.command.name)

    app = RollBookApp(
        midi_file, conf_file, model_name, channel, out_file, transpose
    )
    try:
        app.main()
    finally:
        _log.debug('finally')
        app.end()


@cli.command()
@click.argument('midi_file', type=click.Path(exists=True))
@click.option(
    '--channel', '-c', 'channel', type=int, multiple=True,
    help='MIDI channel'
)
@click.option(
    '--visual', '-v', 'visual_flag', is_flag=True,
    default=False,  show_default=True,
    help='Visual flag'
)
@click.option(
    '--model', '-m', 'model_name', type=str,
    default=None,
    help='機種名。指定すると移調の候補を表にして出す'
)
@click.option(
    '--conf_file', '-f', 'conf_file',
    type=click.Path(exists=False),
    default=RollBook.DEF_CONF_FILE,
    show_default=True,
    help='configuration file（--model 指定時のみ使う）'
)
@click.option(
    '--transpose', '-t', 'transpose', type=str,
    default='0', show_default=True,
    help="移調する半音数。'auto' で最多になる値を選ぶ（--model と併用）"
)
@click_common_opts(__version__, use_v=False)
def parse(
    ctx, midi_file, channel, visual_flag, model_name, conf_file, transpose,
    debug
) -> None:
    """MIDI を解析して中身を表示する（-v で図、-m で移調の候補）。"""
    loggerInit(debug)
    _log.debug('command={!r}', ctx.command.name)

    app = MidiApp(
        midi_file, channel, parse_only=True, visual_flag=visual_flag,
        model_name=model_name, conf_file=conf_file, transpose=transpose
    )
    try:
        app.main()
    finally:
        _log.debug('finally')
        app.end()


@cli.command()
@click.argument('midi_file', type=click.Path(exists=True))
@click.option(
    '--pos_sec', '-s', 'pos_sec', type=float, default=0.0, show_default=True,
    help='seek position in sec'
)
@click.option(
    '--channel', '-c', 'channel', type=int, multiple=True,
    help='MIDI channel'
)
@click.option(
    '--rate', '-r', 'rate', type=int,
    default=Player.DEF_RATE, show_default=True,
    help=f'sampling rate, default={Player.DEF_RATE} Hz'
)
@click.option(
    '--sec_min', '--min', 'sec_min', type=float,
    default=Player.SEC_MIN, show_default=True,
    help=f'min sound length, default={Player.SEC_MIN}'
)
@click.option(
    '--sec_max', '--max', 'sec_max',
    type=float, default=Player.SEC_MAX, show_default=True,
    help=f'max sound length, default={Player.SEC_MAX}'
)
@click.option(
    '--model', '-m', 'model_name', type=str,
    default=None,
    help='指定すると、その機種の音階に無い音を除いて再生する'
)
@click.option(
    '--conf_file', '-f', 'conf_file',
    type=click.Path(exists=False),
    default=RollBook.DEF_CONF_FILE,
    show_default=True,
    help='configuration file（--model 指定時のみ使う）'
)
@click.option(
    '--transpose', '-t', 'transpose', type=str,
    default='0', show_default=True,
    help="移調する半音数。'auto' で最多になる値を選ぶ（--model と併用）"
)
@click_common_opts(__version__)
def play(
    ctx, midi_file, pos_sec, channel, rate, sec_min, sec_max,
    model_name, conf_file, transpose, debug
) -> None:
    """MIDI を再生する（-m で機種を指定すると、その機種用に変換して再生する）。"""
    loggerInit(debug)
    _log.debug('command={!r}', ctx.command.name)

    app = MidiApp(
        midi_file, channel, parse_only=False,
        visual_flag=False, rate=rate,
        sec_min=sec_min, sec_max=sec_max, pos_sec=pos_sec,
        model_name=model_name, conf_file=conf_file, transpose=transpose
    )
    try:
        app.main()
    finally:
        _log.debug('finally')
        app.end()


if __name__ == '__main__':
    cli(prog_name='Storgan')
