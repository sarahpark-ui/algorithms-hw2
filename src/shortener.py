"""URL shortening backed by a configurable hash table implementation."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable


class Shortener:
    def __init__(self, table_class=HashTable, capacity=128):
        self._urls_to_codes = table_class(capacity=capacity)
        self._codes_to_urls = table_class(capacity=capacity)
        self._next_id = 0

    @staticmethod
    def _validate_url(url):
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if not url or url != url.strip() or any(character.isspace() for character in url):
            raise ValueError("url must not be empty or contain whitespace")
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError("url must be a valid absolute HTTP(S) URL") from error
        if parsed.scheme not in ("http", "https") or not hostname:
            raise ValueError("url must be a valid absolute HTTP(S) URL")

    def shorten(self, url):
        self._validate_url(url)
        try:
            return self._urls_to_codes.get(url)
        except KeyError:
            pass

        code = encode(self._next_id)
        self._next_id += 1
        self._urls_to_codes.put(url, code)
        self._codes_to_urls.put(code, url)
        return code

    def expand(self, code):
        return self._codes_to_urls.get(code)
