"""和胶片冲印（单独的程序）的连接：没装时不显示；装了以后能把它作为独立进程启动，一体窗口多一个页签。
这里用一个假的「胶片冲印」（只回应 /ping）代替真的程序，不需要 spektrafilm。"""
import json
import sys
import textwrap
import time
import urllib.request

from _util import TMP, run

from photo_cull.server import apps, film, pages, runtime

OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
FAKE = TMP / "fake-film"


def make_fake():
    pkg = FAKE / "photo_cull_film"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "__main__.py").write_text(textwrap.dedent(f'''
        import json, os
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from pathlib import Path
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_GET(self):
                b = json.dumps({{"app": "film"}}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        s = HTTPServer(("127.0.0.1", 0), H)
        Path({str(film.REGISTRY)!r}).write_text(json.dumps({{"port": s.server_address[1], "token": "tok", "pid": os.getpid()}}))
        s.serve_forever()
    '''))


def test_not_installed():
    assert not film.installed() and film.start() is None
    assert b'"film": false' in pages.render_page("cull")


def test_start_and_shell():
    make_fake()
    film.INSTALL.parent.mkdir(parents=True, exist_ok=True)
    film.INSTALL.write_text(json.dumps({"python": sys.executable, "root": str(FAKE), "version": "test"}))
    assert film.installed() and film.running() is None
    t0 = time.time()
    url = film.start(wait=15)
    assert url and "t=tok" in url and time.time() - t0 < 15
    assert film.running() == url                      # 第二次直接用已在运行的
    assert b'"film": true' in pages.render_page("edit")
    shell_url = runtime.start_all()
    try:
        page = OP.open(shell_url).read().decode()
        assert 'id="f-film"' in page and '"film": true' in page
        r = urllib.request.Request(f"http://127.0.0.1:{apps.LOCAL['cull']['port']}/api/film", data=b"{}", method="POST",
                                   headers={"X-Token": apps.TOKEN, "Content-Type": "application/json"})
        assert json.loads(OP.open(r).read())["url"] == url
    finally:
        runtime.stop_all()
        import os
        import signal
        try:
            os.kill(json.loads(film.REGISTRY.read_text())["pid"], signal.SIGTERM)
        except Exception:
            pass


if __name__ == "__main__":
    run(globals())
