#
# (c) 2026 Yoichi Tanibayashi
#
from pathlib import Path

import tornado.httpserver
import tornado.ioloop
import tornado.web
from loguru import logger

from . import __version__
from .conf import Conf
from .config_handler import ConfigHandler
from .handler1 import Download, Handler1
from .history import HistoryHandler
from .livereload import LiveReloadHandler, watch_webroot
from .mylog import exmsg


class WebServer:
    """
    Web application server
    """
    DEF_PORT = 10081

    DEF_WEBROOT = './webroot'
    URL_PREFIX = '/storgan2'

    DEF_WORKDIR = '/tmp'

    DEF_SIZE_LIMIT = 100 * 1024 * 1024  # 100MB

    def __init__(
        self, port=DEF_PORT,
        urlprefix=URL_PREFIX,
        webroot=DEF_WEBROOT,
        workdir=DEF_WORKDIR,
        size_limit=DEF_SIZE_LIMIT,
        version=__version__,
        debug=False
    ):
        """ Constructor

        Parameters
        ----------
        port: int
            port number

        urlprefix: str

        webroot: str | Path
            静的ファイルとテンプレートの置き場。内部では Path に正規化し、
            app.settings にも Path のまま渡す（各ハンドラも Path で受ける）。

        workdir: str | Path

        size_limit: int
            max upload size
        version: str
            version string
        debug: bool
            開発用。ブラウザの live reload を有効にする
            （`/livereload` を生やし、テンプレートと静的ファイルも
            autoreload の監視対象にする）。
        """
        # loggerInit(debug)
        logger.debug(
            'port={}, urlprefix={}, webroot={}, workdir={}, size_limit={}',
            port, urlprefix, webroot, workdir, size_limit
        )
        logger.debug('version={}', version)

        self._port = port
        self._urlprefix = urlprefix
        self._webroot = Path(webroot)
        self._workdir = Path(workdir)
        self._size_limit = size_limit
        self._version = version
        self._debug = debug

        self._models = Conf().models
        logger.info('_models={}', self._models)

        try:
            self._workdir.mkdir(parents=True, exist_ok=True)
        except Exception as ex:
            logger.error(exmsg(ex))
            raise ex

        handlers: list = [
            (r'/', Handler1),
            (rf'{self._urlprefix}', Handler1),
            (rf'{self._urlprefix}/', Handler1),
            (rf'{self._urlprefix}/config.*', ConfigHandler),
            (rf'{self._urlprefix}/history/?', HistoryHandler),
            # 種別つき（midi/）と、SVG 用の従来の形の両方を受ける
            (rf'{self._urlprefix}/download/(midi/)?(.*)', Download),
        ]
        if self._debug:
            # 開発用。ブラウザはこれが切れたのを合図に再読み込みする
            handlers.append(
                (rf'{self._urlprefix}/livereload', LiveReloadHandler)
            )

        self._app = tornado.web.Application(
            handlers,
            static_path=self._webroot / 'static',
            static_url_prefix=self._urlprefix + '/static/',
            template_path=self._webroot / 'templates',
            # autoreload だけでは .py しか反映されない。テンプレートと
            # 静的ファイルのハッシュもキャッシュを切らないと、直しても
            # サーバーを再起動するまで反映されない。
            autoreload=True,
            compiled_template_cache=False,
            static_hash_cache=False,
            # xsrf_cookies=False,

            webroot=self._webroot,
            workdir=self._workdir,
            urlprefix=self._urlprefix,
            size_limit=self._size_limit,
            version=self._version,
            models=self._models,
            # テンプレートが livereload.js を出すかどうかの判断に使う
            livereload=self._debug,
        )
        logger.debug('app={}', self._app.__dict__)

        if self._debug:
            # autoreload だけでは .py しか見ていないので、テンプレートと
            # 静的ファイルを直したときも再起動するようにする
            watch_webroot(self._webroot)

        self._svr = tornado.httpserver.HTTPServer(
            self._app, max_buffer_size=self._size_limit
        )
        logger.debug('svr={}', self._svr.__dict__)

    def main(self):
        """ main """
        logger.debug('')

        self._svr.listen(self._port)
        logger.info('start server: run forever ..')

        tornado.ioloop.IOLoop.current().start()

        logger.debug('done')
