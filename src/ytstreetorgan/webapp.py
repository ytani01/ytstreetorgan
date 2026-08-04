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
    """Tornado の Web サーバー。

    URL のプレフィックスは :data:`URL_PREFIX`（既定 `/storgan2`）。
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
        """サーバーを組み立てる（listen は `main()`）。

        Args:
            port (int): 待ち受けるポート。
            urlprefix (str): URL の頭に付ける。
            webroot (str | Path): 静的ファイルとテンプレートの置き場。
                内部では `Path` に正規化し、`app.settings` にも `Path` の
                まま渡す（各ハンドラも `Path` で受ける）。
            workdir (str | Path): 作業用ディレクトリ。無ければ作る。
            size_limit (int): アップロードの上限 [byte]。
            version (str): 画面のフッターに出す版。
            debug (bool): 開発用。ブラウザの live reload を有効にする
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

        # 起動時に設定を読めるか確かめる（読めなければここで落ちる）。
        # 機種の一覧は各ハンドラがその都度読み直すので、app.settings には
        # 載せない。載せていた頃は誰も読まないうえ、機種を足しても
        # 起動時の値のままだった。
        logger.info('models={}', Conf().models)

        try:
            self._workdir.mkdir(parents=True, exist_ok=True)
        except Exception as ex:
            logger.error(exmsg(ex))
            raise ex

        # 形を揃える。`/config.*` は `/configXYZ` まで拾っていた
        handlers: list = [
            (r'/', Handler1),
            (rf'{self._urlprefix}', Handler1),
            (rf'{self._urlprefix}/', Handler1),
            # /config, /config/, /config/api/data, /config/save
            (rf'{self._urlprefix}/config(?:/.*)?', ConfigHandler),
            (rf'{self._urlprefix}/history/?', HistoryHandler),
            # 種別は URL ではなく初期化引数で渡す（並び順が意味を持つので、
            # midi のほうを先に置くこと）。SVG は種別なしの従来の形
            (rf'{self._urlprefix}/download/midi/(.*)', Download,
             {'kind': 'midi'}),
            (rf'{self._urlprefix}/download/(.*)', Download, {'kind': 'svg'}),
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
            # テンプレートが livereload.js を出すかどうかの判断に使う
            livereload=self._debug,
        )

        if self._debug:
            # autoreload だけでは .py しか見ていないので、テンプレートと
            # 静的ファイルを直したときも再起動するようにする
            watch_webroot(self._webroot)

        # app と svr の __dict__ を丸ごと出していたが、-d のとき
        # 数百行になるだけで読めたものではなかったので出さない
        self._svr = tornado.httpserver.HTTPServer(
            self._app, max_buffer_size=self._size_limit
        )

    def main(self):
        """待ち受けを始めて、イベントループを回す（戻らない）。"""
        logger.debug('')

        self._svr.listen(self._port)
        logger.info('start server: run forever ..')

        tornado.ioloop.IOLoop.current().start()

        logger.debug('done')
