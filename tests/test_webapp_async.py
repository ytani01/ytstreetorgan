"""ロールブック作成（`/`）とダウンロードの HTTP テスト。

`webroot` の複製は `WebAppTestCase` が用意する。**実物を渡してはいけない**
（アップロードのテストが `webroot/midi/` と `webroot/svg/` に実際に書く。
途中で落ちれば消し残るし、一覧を読むテストが実ファイルの影響を受ける）。
"""
import tornado.websocket

from .conftest import TEST_URL_PREFIX
from .webapp_base import REPO_ROOT, WebAppTestCase


class TestWebAppAsync(WebAppTestCase):
    SERVER_KWARGS = {'size_limit': 1024 * 1024}

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
                reuse=False, model='34notes'):
        """MIDI を 1 本アップロードする（multipart を手で組み立てる）。"""
        # 送る中身はリポジトリの実ファイルから読む。書き込む先は複製のほう
        midi_data = (REPO_ROOT / 'webroot' / 'midi' / src).read_bytes()

        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        fields = f'--{boundary}\r\n' \
            'Content-Disposition: form-data; name="model"\r\n\r\n' \
            f'{model}\r\n'
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

    def test_post_unknown_model_shows_a_message(self):
        """知らない機種名は 500 にせず、理由を画面に出す。

        `RollBook` が断るようになる前は、`Conf.get()` が `{}` を返して
        「高さ 0 の空のブック」が何事もなく出ていた。
        """
        response = self._upload(model='no-such-model')

        self.assertEqual(response.code, 200)
        self.assertIn(b"no-such-model", response.body)
        self.assertIn("設定にありません".encode(), response.body)
        # ロールブックは作らないし、MIDI も残さない
        self.assertNotIn(b'id="svgbox"', response.body)
        self.assertFalse((self.webroot / 'midi' / 'dummy.mid').exists())

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
            (REPO_ROOT / 'webroot' / 'midi' / 'holy.mid').read_bytes(),
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
        # どのファイルから作ったのか名前も出る
        self.assertIn("前回アップロードした".encode(), response.body)
        self.assertIn(b"dummy.mid", response.body)
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
        self.assertNotIn("前回アップロードした".encode(), response.body)


class TestWebAppLiveReload(WebAppTestCase):
    """``webapp --debug`` のときだけ live reload が有効になること。"""

    PORT = 10082
    SERVER_KWARGS = {'debug': True}

    def test_script_is_included(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/')
        self.assertIn(b'js/livereload.js', response.body)

    def test_script_is_included_on_every_page(self):
        # base.html に 1 回書いてあるので、全ページに出る
        for path in ('/config', '/history'):
            response = self.fetch(f'{TEST_URL_PREFIX}{path}')
            self.assertIn(b'js/livereload.js', response.body, path)

    def test_websocket_endpoint_accepts_a_connection(self):
        url = self.get_url(f'{TEST_URL_PREFIX}/livereload').replace(
            'http://', 'ws://'
        )
        conn = self.io_loop.run_sync(
            lambda: tornado.websocket.websocket_connect(url)
        )
        self.assertIsNotNone(conn)
        conn.close()


class TestWebAppNoLiveReload(WebAppTestCase):
    """既定（debug なし）では live reload を出さないこと。"""

    PORT = 10083

    def test_script_is_not_included(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/')
        self.assertNotIn(b'js/livereload.js', response.body)

    def test_websocket_endpoint_is_absent(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/livereload')
        self.assertEqual(response.code, 404)
