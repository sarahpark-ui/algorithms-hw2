import unittest

from src.hash_table import HashTable, LinearProbingHashTable


TABLE_CLASSES = (HashTable, LinearProbingHashTable)


class HashTableContractTests(unittest.TestCase):
    def test_collisions_updates_and_lookup(self):
        for table_class in TABLE_CLASSES:
            with self.subTest(table_class=table_class.__name__):
                table = table_class(capacity=5)
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
        for table_class in TABLE_CLASSES:
            with self.subTest(table_class=table_class.__name__):
                table = table_class(capacity=3)
                table.put("key", 1)
                table.delete("key")

                self.assertEqual(len(table), 0)
                self.assertNotIn("key", table)
                for operation in (lambda: table.get("key"), lambda: table.delete("key")):
                    with self.assertRaises(KeyError):
                        operation()

    def test_empty_key_and_empty_table(self):
        for table_class in TABLE_CLASSES:
            with self.subTest(table_class=table_class.__name__):
                table = table_class(capacity=2)
                self.assertEqual(len(table), 0)
                table.put("", 1)
                self.assertEqual(table.get(""), 1)
                table.delete("")
                self.assertEqual(len(table), 0)

    def test_lookup_reports_comparisons_and_slot_checks_separately(self):
        for table_class in TABLE_CLASSES:
            with self.subTest(table_class=table_class.__name__):
                table = table_class(capacity=5)
                table.put("a", 1)
                table.put("f", 2)

                self.assertEqual(table.get("f"), 2)
                self.assertEqual(table.last_comparisons, 2)
                self.assertEqual(table.last_slot_checks, 1 if table_class is HashTable else 2)
                self.assertEqual(len(table.last_probe_path), table.last_slot_checks)


class SeparateChainingTests(unittest.TestCase):
    def test_stores_more_items_than_buckets(self):
        table = HashTable(capacity=2)
        for index, key in enumerate(("one", "two", "three")):
            table.put(key, index)

        self.assertEqual([table.get(key) for key in ("one", "two", "three")], [0, 1, 2])
        self.assertEqual(len(table), 3)


class LinearProbingTests(unittest.TestCase):
    def test_probe_wraps_from_last_slot_to_zero(self):
        table = LinearProbingHashTable(capacity=5)
        table.put("c", 1)
        table.put("h", 2)
        table.put("m", 3)

        self.assertEqual(table.get("m"), 3)
        self.assertEqual(table.last_probe_path, [4, 0, 1])

    def test_search_continues_after_deleting_a_colliding_key(self):
        table = LinearProbingHashTable(capacity=5)
        table.put("a", 1)
        table.put("f", 2)
        table.put("k", 3)

        table.delete("f")

        self.assertEqual(table.get("k"), 3)
        self.assertEqual(table.last_probe_path, [2, 3, 4])
        self.assertNotIn("f", table)

    def test_reuses_deleted_slot_and_rejects_new_key_when_full(self):
        table = LinearProbingHashTable(capacity=3)
        for index, key in enumerate(("a", "b", "c")):
            table.put(key, index)

        with self.assertRaises(OverflowError):
            table.put("d", 4)

        table.delete("b")
        table.put("d", 4)
        self.assertEqual(table.get("d"), 4)
        self.assertEqual(len(table), 3)
        table.put("a", "updated")
        self.assertEqual(table.get("a"), "updated")
        self.assertEqual(len(table), 3)


if __name__ == "__main__":
    unittest.main()
