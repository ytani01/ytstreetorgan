from tornado.testing import AsyncHTTPTestCase
from ytstreetorgan.webapp import WebServer
import os

class TestWebAppAsync(AsyncHTTPTestCase):
    def get_app(self):
        # Create web server instance and extract the tornado Application
        self.workdir = '/tmp/storgan_test_workdir'
        self.webroot = './webroot'
        self.server = WebServer(
            port=10081,
            urlprefix='/storgan2',
            webroot=self.webroot,
            workdir=self.workdir,
            size_limit=1024*1024
        )
        return self.server._app

    def tearDown(self):
        # Cleanup dummy files
        dummy_midi = os.path.join(self.webroot, 'midi', 'dummy.mid')
        dummy_svg = os.path.join(self.webroot, 'svg', 'dummy.mid.svg')
        if os.path.exists(dummy_midi):
            os.remove(dummy_midi)
        if os.path.exists(dummy_svg):
            os.remove(dummy_svg)
        super().tearDown()

    def test_homepage_redirect(self):
        # The homepage should respond 200 for missing trailing slash (due to regex matching)
        response = self.fetch('/storgan2')
        self.assertEqual(response.code, 200)

    def test_homepage_content(self):
        # Fetch the actual page
        response = self.fetch('/storgan2/')
        self.assertEqual(response.code, 200)
        # Should contain the default message
        self.assertIn(b"Please select a MIDI file", response.body)

    def test_post_upload(self):
        # Simulate an upload of a small real midi file
        with open(os.path.join(self.webroot, 'midi', 'd-kaeru.mid'), 'rb') as f:
            midi_data = f.read()
            
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="model"\r\n\r\n'
            '34notes\r\n'
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="file1"; filename="dummy.mid"\r\n'
            'Content-Type: audio/midi\r\n\r\n'
        ).encode('utf-8') + midi_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        response = self.fetch('/storgan2/', method='POST', headers=headers, body=body)
        self.assertEqual(response.code, 200)
        # It should render the SVG data variable injected into HTML
        self.assertIn(b"<svg ", response.body)

    def test_download(self):
        # Create a dummy svg file to download
        svg_dir = os.path.join(self.webroot, 'svg')
        os.makedirs(svg_dir, exist_ok=True)
        test_file = os.path.join(svg_dir, 'dummy.mid.svg')
        with open(test_file, 'w') as f:
            f.write('<svg>dummy</svg>')
        
        response = self.fetch('/storgan2/download/dummy.mid.svg')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b'<svg>dummy</svg>')
