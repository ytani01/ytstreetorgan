from pathlib import Path

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
        self.assertIn(b"Please select a MIDI file", response.body)

    def test_post_upload(self):
        # Simulate an upload of a small real midi file
        midi_data = (self.webroot / 'midi' / 'd-kaeru.mid').read_bytes()

        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="model"\r\n\r\n'
            '34notes\r\n'
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="file1"; filename="dummy.mid"\r\n'
            'Content-Type: audio/midi\r\n\r\n'
        ).encode() + midi_data + f'\r\n--{boundary}--\r\n'.encode()
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        response = self.fetch(
            f'{TEST_URL_PREFIX}/', method='POST', headers=headers, body=body
        )
        self.assertEqual(response.code, 200)
        # It should render the SVG data variable injected into HTML
        self.assertIn(b"<svg ", response.body)

    def test_download(self):
        # Create a dummy svg file to download
        svg_dir = self.webroot / 'svg'
        svg_dir.mkdir(parents=True, exist_ok=True)
        (svg_dir / 'dummy.mid.svg').write_text('<svg>dummy</svg>')

        response = self.fetch(f'{TEST_URL_PREFIX}/download/dummy.mid.svg')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b'<svg>dummy</svg>')
