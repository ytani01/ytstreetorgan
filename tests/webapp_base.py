"""HTTP テストの土台（テストモジュールではない）。

**`webroot` はテストごとに一時ディレクトリへ複製する。**
リポジトリの `webroot/` をそのまま渡すと、アップロードのテストが実物に
書き込み、途中で落ちると消し残る。一覧を読むテストは、そこに置いてある
実ファイルの影響も受ける。
"""
import shutil
import tempfile
from pathlib import Path

from tornado.testing import AsyncHTTPTestCase

from ytstreetorgan.webapp import WebServer

from .conftest import SAMPLE_MIDI, TEST_URL_PREFIX

REPO_ROOT = Path(__file__).resolve().parents[1]

__all__ = ['SAMPLE_MIDI', 'WebAppTestCase']


class WebAppTestCase(AsyncHTTPTestCase):
    """`webroot` を複製したサーバーを立てる。

    Attributes:
        PORT: `WebServer` に渡すポート。`AsyncHTTPTestCase` は自分で空きポートを
            使うので実際には listen しないが、区別のため分けてある。
        SERVER_KWARGS: `WebServer` への追加引数（`debug` や `size_limit`）。
    """

    PORT = 10081
    SERVER_KWARGS: dict = {}

    def get_app(self):
        """一時ディレクトリに webroot を作り、サーバーを組み立てる。"""
        self.tmp = Path(tempfile.mkdtemp(prefix='storgan-test-'))
        self.addCleanup(shutil.rmtree, self.tmp, True)

        self.webroot = self.tmp / 'webroot'
        for sub in ('templates', 'static'):
            shutil.copytree(REPO_ROOT / 'webroot' / sub, self.webroot / sub)
        for sub in ('midi', 'svg'):
            (self.webroot / sub).mkdir()

        self.setup_files()

        self.server = WebServer(
            port=self.PORT,
            urlprefix=TEST_URL_PREFIX,
            webroot=self.webroot,
            workdir=self.tmp / 'work',
            **self.SERVER_KWARGS,
        )
        return self.server._app

    def setup_files(self) -> None:
        """置き場に何か置きたいときに subclass が上書きする。"""

    def put_midi(self, name: str, src: Path = SAMPLE_MIDI) -> Path:
        """`webroot/midi/` に MIDI を 1 本置く。"""
        path = self.webroot / 'midi' / name
        shutil.copy(src, path)
        return path

    def names(self, kind: str) -> list[str]:
        """置き場にあるファイル名（並べ替え済み）。"""
        return sorted(p.name for p in (self.webroot / kind).iterdir())
