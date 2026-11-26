"""HTTP interface for the in-memory URL shortener."""
import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys
from urllib.parse import parse_qsl, urlsplit, quote

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.shortener import Shortener


class Handler(BaseHTTPRequestHandler):
    def page(self, status, content):
        body = ('<!doctype html><html lang="ko"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>URL 단축기</title><body><h1>URL 단축기</h1>'
                '<nav><a href="/">홈</a> | <a href="/table">해시 테이블</a></nav>'
                + content + '</body></html>').encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self.page(200, '<form method="post" action="/"><label>URL '
                      '<input name="url" type="url" required></label>'
                      '<button>단축하기</button></form>')
        elif path == "/table":
            parts = ['<h2>Horner: h = (31 × h + 문자 코드) mod M</h2>']
            shortener = self.server.shortener
            for title, table in (("URL → 코드", shortener._urls_to_codes),
                                 ("코드 → URL", shortener._codes_to_urls)):
                parts.append(f'<h3>{title} (M={table.capacity}, α={len(table)/table.capacity:.3f})</h3>')
                parts.append('<table border="1"><tr><th>칸</th><th>연결 리스트 및 계산 근거</th></tr>')
                for index, node in enumerate(table.buckets):
                    chain = []
                    while node is not None:
                        trace = table.hash_trace(node.key)
                        steps = '; '.join(f'{escape(repr(c))}: (31×{old}+{ord(c)}) mod {table.capacity}={new}' for c, old, new in trace)
                        chain.append(f'<details><summary>{escape(node.key)} → {escape(str(node.value))}</summary>{steps or "h=0"}</details>')
                        node = node.next
                    parts.append(f'<tr><td>{index}</td><td>{" → ".join(chain) or "∅"}</td></tr>')
                parts.append('</table>')
            self.page(200, ''.join(parts))
        else:
            try:
                url = self.server.shortener.expand(path[1:])
            except KeyError:
                self.page(404, '<p>등록되지 않은 코드입니다.</p>')
                return
            self.send_response(302)
            self.send_header("Location", quote(url, safe=":/?&=#%+@!$'()*,-.;[]~"))
            self.send_header("Content-Length", "0")
            self.end_headers()

    def do_POST(self):
        if urlsplit(self.path).path != "/":
            self.page(404, '<p>잘못된 경로입니다.</p>')
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                raise ValueError("입력 길이 오류")
            fields = parse_qsl(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
            url = next((value for key, value in fields if key == "url"), "")
            code = self.server.shortener.shorten(url)
        except (ValueError, TypeError):
            self.page(400, '<p>올바른 HTTP(S) URL을 입력하세요.</p>')
            return
        self.page(200, f'<p>단축 링크: <a href="/{code}">/{code}</a></p>'
                  '<p>링크를 열거나 주소를 복사하세요.</p>')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = HTTPServer(("0.0.0.0", args.port), Handler)
    server.shortener = Shortener()
    print(f"Listening on port {args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
