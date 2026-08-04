"""履歴の画面（`/history`）とダウンロードの HTTP テスト。

`webroot` の複製は `WebAppTestCase` が用意する（削除を試すので、
リポジトリの `webroot/` をそのまま触らせない）。
"""
import json
import re

from .conftest import TEST_URL_PREFIX
from .webapp_base import WebAppTestCase


class HistoryTestBase(WebAppTestCase):
    """一覧・削除を試せるように、置き場に何本か置いておく。"""

    PORT = 10084

    def setup_files(self):
        self.put_midi('holy.mid')
        (self.webroot / 'midi' / 'other.mid').write_bytes(b'not midi')
        # 名前の扱い（L）を確かめるためのもの
        self.put_midi('テスト曲.mid')
        self.put_midi('a b.mid')
        # 諸元の属性が無い、古い形の SVG
        (self.webroot / 'svg' / 'holy.mid.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"'
            ' width="2089.30mm" height="126.00mm"'
            ' viewBox="-2089.30 -126.00 2089.30 126.00"></svg>\n',
            encoding='utf-8',
        )

    def delete(self, **payload):
        return self.fetch(
            f'{TEST_URL_PREFIX}/history', method='POST',
            body=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
        )


class TestHistoryPage(HistoryTestBase):
    def test_lists_both_kinds(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/history')

        self.assertEqual(response.code, 200)
        self.assertIn(b'holy.mid', response.body)
        self.assertIn(b'holy.mid.svg', response.body)
        # ダウンロードのリンクが両方ある
        self.assertIn(
            f'{TEST_URL_PREFIX}/download/midi/holy.mid'.encode(), response.body
        )
        self.assertIn(
            f'{TEST_URL_PREFIX}/download/holy.mid.svg'.encode(), response.body
        )


class TestHistoryDelete(HistoryTestBase):
    def test_delete_one(self):
        response = self.delete(kind='svg', name='holy.mid.svg')

        self.assertEqual(response.code, 200)
        body = json.loads(response.body)
        self.assertEqual(body['status'], 'ok')
        self.assertEqual(body['removed'], 1)
        self.assertEqual(self.names('svg'), [])
        # MIDI のほうは残っている
        self.assertIn('holy.mid', self.names('midi'))

    def test_delete_all(self):
        before = len(self.names('midi'))
        response = self.delete(kind='midi', all=True)

        self.assertEqual(response.code, 200)
        body = json.loads(response.body)
        self.assertEqual(body['removed'], before)
        self.assertEqual(self.names('midi'), [])
        self.assertEqual(self.names('svg'), ['holy.mid.svg'])

    def test_delete_missing_is_404(self):
        response = self.delete(kind='svg', name='nope.svg')

        self.assertEqual(response.code, 404)

    def test_delete_rejects_traversal(self):
        """置き場の外を指す名前は消させない。"""
        outside = self.tmp / 'keep-me.txt'
        outside.write_text('x')

        response = self.delete(kind='svg', name='../keep-me.txt')

        self.assertEqual(response.code, 400)
        self.assertTrue(outside.exists())

    def test_delete_rejects_unknown_kind(self):
        response = self.delete(kind='templates', all=True)

        self.assertEqual(response.code, 400)
        self.assertTrue((self.webroot / 'templates').is_dir())

    def test_delete_rejects_broken_json(self):
        response = self.fetch(
            f'{TEST_URL_PREFIX}/history', method='POST', body='{ not json',
            headers={'Content-Type': 'application/json'},
        )

        self.assertEqual(response.code, 400)


class TestHistoryActions(HistoryTestBase):
    def _post_root(self, **fields):
        body = '&'.join(f'{k}={v}' for k, v in fields.items())
        return self.fetch(
            f'{TEST_URL_PREFIX}/', method='POST', body=body,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )

    def test_show_stored_svg(self):
        """保存済みの SVG をそのまま出す。生成し直さない。"""
        before = (self.webroot / 'svg' / 'holy.mid.svg').stat().st_mtime_ns

        response = self._post_root(stored_svg='holy.mid.svg', model='34notes')

        self.assertEqual(response.code, 200)
        self.assertIn(b'id="svgbox"', response.body)
        self.assertIn('履歴から表示'.encode(), response.body)
        # SVG から読める寸法は出る
        self.assertIn(b'2089.3', response.body)
        # 読めないものは --- になる
        self.assertIn(b'---', response.body)
        # 触っていない
        self.assertEqual(
            (self.webroot / 'svg' / 'holy.mid.svg').stat().st_mtime_ns, before
        )

    def test_show_missing_svg(self):
        response = self._post_root(stored_svg='nope.svg', model='34notes')

        self.assertEqual(response.code, 200)
        self.assertIn('見つかりません'.encode(), response.body)
        self.assertNotIn(b'id="svgbox"', response.body)

    def test_show_rejects_traversal(self):
        response = self._post_root(
            stored_svg='..%2F..%2Fetc%2Fpasswd', model='34notes'
        )

        self.assertEqual(response.code, 200)
        self.assertIn('開けません'.encode(), response.body)

    def test_regenerate_from_stored_midi(self):
        """保存済みの MIDI から作り直す。SVG が新しくなる。"""
        svg = self.webroot / 'svg' / 'holy.mid.svg'
        before = svg.read_text(encoding='utf-8')

        response = self._post_root(stored_midi='holy.mid', model='34notes')

        self.assertEqual(response.code, 200)
        self.assertIn(b'id="svgbox"', response.body)
        self.assertIn('生成しました'.encode(), response.body)
        # 作り直されている（置いてあったダミーとは別物）
        self.assertNotEqual(svg.read_text(encoding='utf-8'), before)
        # 諸元も出る（--- ではない）
        self.assertIn('音符'.encode(), response.body)

    def test_regenerate_broken_midi_is_reported(self):
        response = self._post_root(stored_midi='other.mid', model='34notes')

        self.assertEqual(response.code, 200)
        self.assertIn('読み込めませんでした'.encode(), response.body)


class TestDownload(HistoryTestBase):
    def test_download_midi(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/download/midi/holy.mid')

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.body, (self.webroot / 'midi' / 'holy.mid').read_bytes()
        )

    def test_download_svg(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/download/holy.mid.svg')

        self.assertEqual(response.code, 200)
        self.assertIn(b'<svg', response.body)

    def test_download_missing_is_404(self):
        response = self.fetch(f'{TEST_URL_PREFIX}/download/nope.svg')

        self.assertEqual(response.code, 404)

    def test_download_japanese_name(self):
        """日本語のファイル名でも落とせる。

        名前をヘッダにそのまま入れていたころは 500 になっていた
        （ヘッダは latin-1 しか通らない）。
        """
        from urllib.parse import quote

        response = self.fetch(
            f'{TEST_URL_PREFIX}/download/midi/{quote("テスト曲.mid")}'
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.body, (self.webroot / 'midi' / 'holy.mid').read_bytes()
        )

        cd = response.headers['Content-Disposition']
        # UTF-8 の名前は filename* に入る
        self.assertIn(
            "filename*=UTF-8''" + quote('テスト曲.mid', safe=''), cd
        )
        # 読まないもの向けの ASCII 版も付く
        self.assertIn('filename="download.mid"', cd)

    def test_download_name_with_space_is_quoted(self):
        """空白入りの名前は引用符で囲む（囲まないと途中で切られうる）。"""
        from urllib.parse import quote

        response = self.fetch(
            f'{TEST_URL_PREFIX}/download/midi/{quote("a b.mid")}'
        )

        self.assertEqual(response.code, 200)
        self.assertIn('filename="a b.mid"',
                      response.headers['Content-Disposition'])


class TestBaseTemplate(HistoryTestBase):
    """`base.html` の共通部分が全ページに出ること。

    かつては `<head>` も appbar も各テンプレートが同じ内容を持っていて、
    片方だけ直すと食い違った。
    """

    PAGES = ('/', '/history', '/config')

    def test_nav_is_on_every_page(self):
        for path in self.PAGES:
            body = self.fetch(f'{TEST_URL_PREFIX}{path}').body
            for label in ('ロールブック作成', '履歴', '機種設定'):
                self.assertIn(label.encode(), body, f'{path}: {label}')

    def test_current_page_is_marked(self):
        """いま居るページのリンクだけに aria-current が付く。"""
        for path in self.PAGES:
            body = self.fetch(f'{TEST_URL_PREFIX}{path}').body.decode()

            # 現在地は 1 か所だけ
            self.assertEqual(body.count('aria-current="page"'), 1, path)

            # それが今のページのリンクであること
            # （テンプレートが行頭の空白を落とすので、空白は数えない）
            href = f'{TEST_URL_PREFIX}{path}'
            marked = re.search(
                r'<a href="' + re.escape(href) + r'"\s*aria-current="page"',
                body,
            )
            self.assertIsNotNone(marked, path)

    def test_stylesheets_are_on_every_page(self):
        for path in self.PAGES:
            body = self.fetch(f'{TEST_URL_PREFIX}{path}').body
            self.assertIn(b'css/pico.min.css', body, path)
            self.assertIn(b'css/my.css', body, path)

    def test_url_prefix_is_exposed_on_every_page(self):
        for path in self.PAGES:
            body = self.fetch(f'{TEST_URL_PREFIX}{path}').body
            self.assertIn(b'window.URL_PREFIX', body, path)
