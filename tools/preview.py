"""Build and serve the exact production files at http://127.0.0.1:4001/."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit
from build import build

ROOT = Path(__file__).resolve().parents[1]
LOCK = Lock()


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_GET(self):
        if urlsplit(self.path).path in ('/', '/index.html', '/publications', '/publications/', '/publications.html'):
            with LOCK:
                build()
        super().do_GET()


if __name__ == '__main__':
    build()
    server = ThreadingHTTPServer(('127.0.0.1', 4001), partial(Handler, directory=str(ROOT / '_site')))
    print('Open http://127.0.0.1:4001/ to preview the new template. Refresh after edits.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
