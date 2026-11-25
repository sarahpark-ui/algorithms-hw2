import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_round_trip_boundaries(self):
        for number in (0, 1, 61, 62, 63, 3843, 3844, 2**64):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_zero_encodes_as_zero(self):
        self.assertEqual(encode(0), "0")

    def test_rejects_negative_or_non_integer_input(self):
        with self.assertRaises(ValueError):
            encode(-1)
        for value in (True, 1.5, "12"):
            with self.subTest(value=value), self.assertRaises(TypeError):
                encode(value)

    def test_rejects_empty_or_invalid_codes(self):
        for value in ("", "a!", "a "):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode(value)
        with self.assertRaises(TypeError):
            decode(62)


if __name__ == "__main__":
    unittest.main()
