import unittest

from src.hash_table import HashTable, LinearProbingHashTable
from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    def test_shortens_and_expands_with_both_table_implementations(self):
        for table_class in (HashTable, LinearProbingHashTable):
            with self.subTest(table_class=table_class.__name__):
                shortener = Shortener(table_class=table_class, capacity=7)
                first_url = "https://example.com/a"
                second_url = "http://example.org/b"

                first_code = shortener.shorten(first_url)
                self.assertEqual(first_code, "0")
                self.assertEqual(shortener.shorten(first_url), first_code)

                second_code = shortener.shorten(second_url)
                self.assertEqual(second_code, "1")
                self.assertEqual(shortener.expand(first_code), first_url)
                self.assertEqual(shortener.expand(second_code), second_url)

    def test_accepts_an_injected_table_class(self):
        shortener = Shortener(table_class=LinearProbingHashTable, capacity=7)
        self.assertEqual(shortener.expand(shortener.shorten("https://example.com")), "https://example.com")

    def test_rejects_invalid_urls_and_unknown_codes(self):
        shortener = Shortener()
        for url in ("", "relative/path", "ftp://example.com", "http:///missing-host"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                shortener.shorten(url)
        with self.assertRaises(KeyError):
            shortener.expand("unknown")

    def test_rejects_non_string_url(self):
        with self.assertRaises(TypeError):
            Shortener().shorten(None)


if __name__ == "__main__":
    unittest.main()
