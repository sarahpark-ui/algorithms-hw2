import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_collisions_updates_and_lookup(self):
        table = HashTable(capacity=5)
        table.put("a", "first")
        table.put("f", "second")

        self.assertEqual(table.get("a"), "first")
        self.assertEqual(table.get("f"), "second")
        self.assertEqual(len(table), 2)
        self.assertIn("a", table)
        self.assertNotIn("missing", table)

        table.put("a", "updated")
        self.assertEqual(table.get("a"), "updated")
        self.assertEqual(len(table), 2)

    def test_delete_and_missing_keys(self):
        table = HashTable(capacity=3)
        table.put("key", 1)
        table.delete("key")

        self.assertEqual(len(table), 0)
        self.assertNotIn("key", table)
        for operation in (lambda: table.get("key"), lambda: table.delete("key")):
            with self.assertRaises(KeyError):
                operation()

    def test_empty_key_and_more_items_than_buckets(self):
        table = HashTable(capacity=2)
        for index, key in enumerate(("", "one", "two", "three")):
            table.put(key, index)

        self.assertEqual(table.get(""), 0)
        self.assertEqual([table.get(key) for key in ("one", "two", "three")], [1, 2, 3])
        self.assertEqual(len(table), 4)


if __name__ == "__main__":
    unittest.main()
