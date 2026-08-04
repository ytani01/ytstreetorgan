from pathlib import Path

import tornado.websocket
from tornado.testing import AsyncHTTPTestCase

from ytstreetorgan.webapp import WebServer

from .conftest import TEST_URL_PREFIX


class TestWebAppAsync(AsyncHTTPTestCase):
    def get_app(self):
        # Create web server instance and extract the tornado Application
        self.workdir = Path('/tmp/storgan_test_workdir')
        self.webroot = Path('./webroot')
        self.server = WebServer(
            port=10081,
            urlprefix=TEST_URL_PREFIX,
            webroot=self.webroot,
            workdir=self.workdir,
            size_limit=1024*1024
        )
        return self.server._app

    def tearDown(self):
        # Cleanup dummy files
        for dummy in (self.webroot / 'midi' / 'dummy.mid',
                      self.webroot / 'svg' / 'dummy.mid.svg'):
            dummy.unlink(missing_ok=True)
        super().tearDown()

    def test_homepage_redirect(self):
        # The homepage should respond 200 for missing trailing slash
        # (due to regex matching)
        response = self.fetch(TEST_URL_PREFIX)
        self.assertEqual(response.code, 200)

    def test_homepage_content(self):
        # Fetch the actual page
        response = self.fetch(f'{TEST_URL_PREFIX}/')
        self.assertEqual(response.code, 200)
        # Should contain the default message
        self.assertIn("MIDI ファイルを選んでください".encode(), response.body)

    def _upload(self, fname='dummy.mid', overwrite=False, src='d-kaeru.mid',
                reuse=False):
        """MIDI を 1 本アップロードする（multipart を手で組み立てる）。"""
        midi_data = (self.webroot / 'midi' / src).read_bytes()

        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        fields = f'--{boundary}\r\n' \
            'Content-Disposition: form-data; name="model"\r\n\r\n' \
            '34notes\r\n'
        for name, on in (('overwrite', overwrite), ('reuse', reuse)):
            if on:
                fields += (
                    f'--{boundary}\r\n'
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                    '1\r\n'
                )
        body = (
            fields
            + f'--{boundary}\r\n'
            + f'Content-Disposition: form-data; name="file1"; filename="{fname}"'
            + '\r\n'
            'Content-Type: audio/midi\r\n\r\n'
        ).encode() + midi_data + f'\r\n--{boundary}--\r\n'.encode()

        return self.fetch(
            f'{TEST_URL_PREFIX}/', method='POST', body=body,
            headers={'Content-Type':
                     f'multipart/form-data; boundary={boundary}'},
        )

    def test_post_upload(self):
        response = self._upload()
        self.assertEqual(response.code, 200)
        # It should render the SVG data variable injected into HTML
        self.assertIn(b"<svg ", response.body)

    def test_post_same_name_without_overwrite_is_refused(self):
        """overwrite が無い同名の POST は、置き換えずに断る。

        画面は storgan.js が先に訊くのでここへは来ないが、
        サーバー側だけで見ても古いファイルを黙って使わないこと。
        """
        self.assertEqual(self._upload().code, 200)
        before = (self.webroot / 'midi' / 'dummy.mid').read_bytes()

        # 同じ名前で別の中身を送る
        response = self._upload(src='holy.mid')

        self.assertEqual(response.code, 200)
        self.assertIn("既にあります".encode(), response.body)
        # ロールブックは作らない（<svg は装飾のロゴにも出るので、
        # ビューアの置き場があるかどうかで見る）
        self.assertNotIn(b'id="svgbox"', response.body)
        # 中身も置き換わっていない
        self.assertEqual(
            (self.webroot / 'midi' / 'dummy.mid').read_bytes(), before
        )

    def test_post_same_name_with_overwrite_replaces(self):
        """overwrite=1 なら置き換えて、新しい中身で作り直す。"""
        self.assertEqual(self._upload().code, 200)

        response = self._upload(src='holy.mid', overwrite=True)

        self.assertEqual(response.code, 200)
        self.assertIn(b"<svg ", response.body)
        self.assertEqual(
            (self.webroot / 'midi' / 'dummy.mid').read_bytes(),
            (self.webroot / 'midi' / 'holy.mid').read_bytes(),
        )

    def test_download(self):
        # Create a dummy svg file to download
        svg_dir = self.webroot / 'svg'
        svg_dir.mkdir(parents=True, exist_ok=True)
        (svg_dir / 'dummy.mid.svg').write_text('<svg>dummy</svg>')

        response = self.fetch(f'{TEST_URL_PREFIX}/download/dummy.mid.svg')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b'<svg>dummy</svg>')

    def test_post_same_name_with_reuse_keeps_the_previous_file(self):
        """reuse=1 なら置き換えず、サーバーにある前回のファイルから作る。"""
        self.assertEqual(self._upload().code, 200)
        before = (self.webroot / 'midi' / 'dummy.mid').read_bytes()

        # 同じ名前で別の中身を送るが、使うのは前回のほう
        response = self._upload(src='holy.mid', reuse=True)

        self.assertEqual(response.code, 200)
        self.assertIn(b'id="svgbox"', response.body)
        self.assertIn("前回アップロードしたファイル".encode(), response.body)
        self.assertEqual(
            (self.webroot / 'midi' / 'dummy.mid').read_bytes(), before
        )

    def test_post_reuse_without_the_file_falls_back_to_writing(self):
        """reuse=1 でもサーバーに無ければ、普通に受け取って書く。"""
        (self.webroot / 'midi' / 'dummy.mid').unlink(missing_ok=True)

        response = self._upload(reuse=True)

        self.assertEqual(response.code, 200)
        self.assertIn(b'id="svgbox"', response.body)
        self.assertTrue((self.webroot / 'midi' / 'dummy.mid').exists())
        # 前回のファイルは無かったので、その旨は出さない
        self.assertNotIn("前回アップロードしたファイル".encode(), response.body)


class TestWebAppLiveReload(AsyncHTTPTestCase):
    """``webapp --debug`` のときだけ live reload が有効になること。"""

    def get_app(self):
        self.server = WebServer(
            port=10082,
            urlprefix=TEST_URL_PREFIX,
            webroot=Path('./webroot'),
            workdir=Path('/tmp/storgan_test_workdir'),
            debug=True,
        )
        return self.server._app

    def test_script_is_included(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/')
        self.assertIn(b'js/livereload.js', response.body)

    def test_script_is_included_on_the_config_page(self):
        # 全ページに要る（テンプレートは 2 本あって共通の親が無い）
        response = self.fetch(f'{TEST_URL_PREFIX}/config')
        self.assertIn(b'js/livereload.js', response.body)

    def test_websocket_endpoint_accepts_a_connection(self):
        url = self.get_url(f'{TEST_URL_PREFIX}/livereload').replace(
            'http://', 'ws://'
        )
        conn = self.io_loop.run_sync(
            lambda: tornado.websocket.websocket_connect(url)
        )
        self.assertIsNotNone(conn)
        conn.close()


class TestWebAppNoLiveReload(AsyncHTTPTestCase):
    """既定（debug なし）では live reload を出さないこと。"""

    def get_app(self):
        self.server = WebServer(
            port=10083,
            urlprefix=TEST_URL_PREFIX,
            webroot=Path('./webroot'),
            workdir=Path('/tmp/storgan_test_workdir'),
        )
        return self.server._app

    def test_script_is_not_included(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/')
        self.assertNotIn(b'js/livereload.js', response.body)

    def test_websocket_endpoint_is_absent(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/livereload')
        self.assertEqual(response.code, 404)
