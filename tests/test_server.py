import re
import threading
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from urllib.parse import urlencode
from src.hash_table import LinearProbingHashTable
from src.server import Handler
from src.shortener import Shortener

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.server.shortener = Shortener(capacity=7)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def request(self, method, path, body=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port)
        conn.request(method, path, body, headers={"Content-Type": "application/x-www-form-urlencoded"})
        response = conn.getresponse()
        result = response.status, response.getheader("Location"), response.read().decode()
        conn.close()
        return result

    def submit_url(self, url):
        body = urlencode({"url": url})
        status, _, page = self.request("POST", "/", body)
        self.assertEqual(status, 200)
        return page

    def test_service(self):
        self.assertIn("<form", self.request("GET", "/")[2])
        self.assertIn('href="/0"', self.request("POST", "/", "url=https%3A%2F%2Fexample.com")[2])
        self.assertEqual(self.request("GET", "/0")[:2], (302, "https://example.com"))
        self.assertIn("Horner", self.request("GET", "/table")[2])
        self.assertEqual(self.request("GET", "/missing")[0], 404)
        self.assertEqual(self.request("POST", "/", "url=invalid")[0], 400)

    def test_linear_probing_table_page_shows_slots_and_probe_path(self):
        self.server.shortener = Shortener(
            table_class=LinearProbingHashTable,
            capacity=5,
        )
        self.server.shortener.shorten("https://example.com/a")
        self.server.shortener.shorten("https://example.com/b")

        status, _, page = self.request("GET", "/table")

        self.assertEqual(status, 200)
        self.assertIn("선형 탐지", page)
        table = self.server.shortener._urls_to_codes
        path = " → ".join(str(index) for index in table.last_probe_path)
        self.assertIn(f"최근 탐색 경로: {path}", page)
        self.assertIn("빈 칸", page)
        self.assertIn("(31×", page)
        self.assertIn("Horner", page)

    def test_chaining_page_explains_home_slot_and_collision_chain(self):
        self.server.shortener = Shortener(capacity=8)
        urls = (
            "https://naver.com",
            "https://yonsei.ac.kr",
            "https://google.com",
            "https://github.com",
        )
        for url in urls:
            self.submit_url(url)

        status, _, page = self.request("GET", "/table")
        self.assertEqual(status, 200)
        url_table = page.split("<h3>URL → 코드", 1)[1].split("<h3>코드 → URL", 1)[0]

        self.assertIn("M=8", page)
        self.assertIn("최초 해시 인덱스: 3", url_table)
        self.assertIn("실제 저장 위치: 3", url_table)
        self.assertIn("<ol", url_table)
        yonsei = re.search(
            r'<li class="hash-entry" data-key="https://yonsei\.ac\.kr">(.*?)</li>',
            url_table,
            re.DOTALL,
        ).group(1)
        google = re.search(
            r'<li class="hash-entry" data-key="https://google\.com">(.*?)</li>',
            url_table,
            re.DOTALL,
        ).group(1)
        self.assertIn("충돌 여부: 아니오", yonsei)
        self.assertIn("충돌 여부: 예", google)
        self.assertIn("같은 버킷의 연결 리스트에 추가", google)

    def test_linear_page_shows_each_insertion_path_and_collision_slots(self):
        self.server.shortener = Shortener(
            table_class=LinearProbingHashTable,
            capacity=8,
        )
        urls = (
            "https://naver.com",
            "https://yonsei.ac.kr",
            "https://google.com",
            "https://github.com",
        )
        for url in urls:
            self.submit_url(url)
        self.server.shortener._urls_to_codes.get(urls[0])

        status, _, page = self.request("GET", "/table")
        self.assertEqual(status, 200)
        url_table = page.split("<h3>URL → 코드", 1)[1].split("<h3>코드 → URL", 1)[0]

        self.assertIn("최초 해시 인덱스: 3", url_table)
        self.assertIn("실제 저장 위치: 5", url_table)
        self.assertIn("삽입 시 탐사 경로: 3 → 4 → 5", url_table)
        self.assertIn("충돌한 슬롯: 3, 4", url_table)
        self.assertIn("최종 저장 슬롯: 5", url_table)
        self.assertIn("삽입 시 탐사 경로: 5 → 6", url_table)
        self.assertIn("충돌한 슬롯: 5", url_table)
        self.assertIn("최종 저장 슬롯: 6", url_table)
