from unittest.mock import MagicMock, patch

from ytstreetorgan.handler1 import Download, Handler1


def test_handler1_size_unit():
    # get_size_unit is now in utils, test via utils directly
    from ytstreetorgan.utils import get_size_unit
    assert get_size_unit(1023) == (1023, 'B')
    assert get_size_unit(1024) == (1.0, 'KB')
    assert get_size_unit(1024 * 1024) == (1.0, 'MB')

    # Handler1 still has get_filesize (via StorganBaseHandler)
    app = MagicMock()
    app.settings = {
        'urlprefix': '/',
        'webroot': '/tmp',
        'workdir': '/tmp',
        'size_limit': 1024,
        'url_prefix_handler1': '/handler1',
        'version': '1.0.0'
    }
    req = MagicMock()
    with patch('tornado.web.RequestHandler.__init__'):
        handler = Handler1(app, req)
        handler.application = app
        handler.request = req
        assert handler.get_filesize('/nonexistent') is None

def test_handler1_get_filesize(tmp_path):
    app = MagicMock()
    app.settings = {
        'urlprefix': '/',
        'webroot': '/tmp',
        'workdir': '/tmp',
        'size_limit': 1024,
        'url_prefix_handler1': '/handler1',
        'version': '1.0.0'
    }
    req = MagicMock()

    with patch('tornado.web.RequestHandler.__init__'):
        handler = Handler1(app, req)
        handler.application = app
        handler.request = req

        # Test non-existent file
        assert handler.get_filesize(str(tmp_path / "non_existent")) is None

        # Test existing file
        file_path = tmp_path / "test.txt"
        file_path.write_text("hello")
        size, unit = handler.get_filesize(str(file_path))
        assert size == 5
        assert unit == 'B'

def test_download_init():
    app = MagicMock()
    app.settings = {
        'urlprefix': '/',
        'webroot': '/tmp',
        'workdir': '/tmp',
        'size_limit': 1024,
        'url_prefix_handler1': '/handler1',
        'version': '1.0.0'
    }
    req = MagicMock()

    with patch('tornado.web.RequestHandler.__init__'):
        download = Download(app, req)
        assert download._urlprefix == '/'
