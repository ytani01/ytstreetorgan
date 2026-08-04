from pathlib import Path
from unittest.mock import MagicMock, patch

from ytstreetorgan.handler1 import Download, Handler1

APP_SETTINGS = {
    'urlprefix': '/',
    'webroot': Path('/tmp'),
    'workdir': Path('/tmp'),
    'size_limit': 1024,
    'version': '1.0.0',
}


def make_app():
    app = MagicMock()
    app.settings = dict(APP_SETTINGS)
    return app


def test_handler1_reads_settings():
    """`StorganBaseHandler` が app.settings から拾うもの。"""
    app, req = make_app(), MagicMock()

    with patch('tornado.web.RequestHandler.__init__'):
        handler = Handler1(app, req)

        assert handler._webroot == Path('/tmp')
        assert handler._size_limit == 1024
        # 末尾のスラッシュは必須（get() がこれと突き合わせる）
        assert handler._url_path.endswith('/')


def test_download_init():
    app, req = make_app(), MagicMock()

    with patch('tornado.web.RequestHandler.__init__'):
        download = Download(app, req)
        assert download._urlprefix == '/'
