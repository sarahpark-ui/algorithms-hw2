"""HTTP interface for the in-memory URL shortener."""
import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys
from urllib.parse import parse_qsl, urlsplit, quote

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.hash_table import HashTable, LinearProbingHashTable
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
                probing = isinstance(table, LinearProbingHashTable)
                strategy = "선형 탐지" if probing else "별도 체이닝"
                path = " → ".join(str(index) for index in table.last_probe_path) or "아직 없음"
                highlighted = list(table.last_probe_path)
                parts.append(
                    f'<h3>{title} · {strategy} (M={table.capacity}, '
                    f'α={len(table)/table.capacity:.3f})</h3>'
                )
                parts.append(
                    f'<p>최근 탐색 경로: {escape(path)} · 키 비교 '
                    f'{table.last_comparisons}회 · 슬롯 확인 {table.last_slot_checks}회</p>'
                )
                parts.append(
                    '<table border="1"><tr><th>칸</th>'
                    '<th>상태 / 저장 내용 / 충돌 근거</th></tr>'
                )
                for index in range(table.capacity):
                    if probing:
                        slot = table.slots[index]
                        if slot is None:
                            content = "빈 칸"
                        elif slot is not None and not isinstance(slot, tuple):
                            content = "삭제 표시 (tombstone)"
                        else:
                            key, value, insertion_path, collision_slots = slot
                            content = self._table_entry(
                                table,
                                key,
                                value,
                                index,
                                bool(collision_slots),
                                insertion_path=insertion_path,
                                collision_slots=collision_slots,
                            )
                            for probe_index in insertion_path:
                                if probe_index not in highlighted:
                                    highlighted.append(probe_index)
                    else:
                        node = table.buckets[index]
                        entries = []
                        while node is not None:
                            entries.append(
                                self._table_entry(
                                    table,
                                    node.key,
                                    node.value,
                                    index,
                                    node.had_collision,
                                    as_list_item=True,
                                )
                            )
                            node = node.next
                        content = (
                            '<ol class="chain">' + "".join(entries) + '</ol>'
                            if entries else "빈 칸"
                        )
                    marker = ' style="background:#fff3cd"' if index in highlighted else ""
                    parts.append(f'<tr{marker}><td>{index}</td><td>{content}</td></tr>')
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

    @staticmethod
    def _table_entry(
        table,
        key,
        value,
        storage_index,
        had_collision,
        insertion_path=None,
        collision_slots=(),
        as_list_item=False,
    ):
        trace = table.hash_trace(key)
        home_index = trace[-1][2] if trace else 0
        steps = '; '.join(
            f'{escape(repr(character))}: (31×{previous}+{ord(character)}) '
            f'mod {table.capacity}={current}'
            for character, previous, current in trace
        )
        entry = (
            f'<strong>{escape(key)} → {escape(str(value))}</strong>'
            f'<p>최초 해시 인덱스: {home_index} · 실제 저장 위치: {storage_index} · '
            f'충돌 여부: {"예" if had_collision else "아니오"}</p>'
        )
        if insertion_path is not None:
            path = " → ".join(str(index) for index in insertion_path)
            collisions = ", ".join(str(index) for index in collision_slots) or "없음"
            entry += (
                f'<p>삽입 시 탐사 경로: {path} · 충돌한 슬롯: {collisions} · '
                f'최종 저장 슬롯: {storage_index}</p>'
            )
        elif had_collision:
            entry += '<p>충돌 처리: 같은 버킷의 연결 리스트에 추가</p>'
        else:
            entry += '<p>충돌 처리: 버킷에 직접 저장</p>'
        entry += (
            f'<details><summary>Horner 계산 과정</summary>{steps or "h=0"}</details>'
        )
        safe_key = escape(key, quote=True)
        return f'<li class="hash-entry" data-key="{safe_key}">{entry}</li>' if as_list_item else (
            f'<div class="hash-entry" data-key="{safe_key}">{entry}</div>'
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--table", choices=("chaining", "linear"), default="chaining")
    parser.add_argument("--capacity", type=int, default=128)
    args = parser.parse_args()
    server = HTTPServer(("0.0.0.0", args.port), Handler)
    table_class = LinearProbingHashTable if args.table == "linear" else HashTable
    server.shortener = Shortener(table_class=table_class, capacity=args.capacity)
    print(f"Listening on port {args.port} ({args.table})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
