import unittest
import threading
from http.client import HTTPConnection
from http.server import HTTPServer
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

    def test_service(self):
        self.assertIn("<form", self.request("GET", "/")[2])
        self.assertIn('href="/0"', self.request("POST", "/", "url=https%3A%2F%2Fexample.com")[2])
        self.assertEqual(self.request("GET", "/0")[:2], (302, "https://example.com"))
        self.assertIn("Horner", self.request("GET", "/table")[2])
        self.assertEqual(self.request("GET", "/missing")[0], 404)
        self.assertEqual(self.request("POST", "/", "url=invalid")[0], 400)
