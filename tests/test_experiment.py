import unittest

from experiments.probe_experiment import measure


class ProbeExperimentTests(unittest.TestCase):
    def test_compares_both_tables_with_separate_comparison_and_slot_metrics(self):
        rows = measure(0.5, capacity=100, miss_queries=20)

        self.assertEqual([row["strategy"] for row in rows], ["chaining", "linear"])
        for row in rows:
            self.assertEqual(row["items"], 50)
            for metric in (
                "successful_comparisons",
                "unsuccessful_comparisons",
                "successful_slots",
                "unsuccessful_slots",
            ):
                self.assertGreaterEqual(row[f"{metric}_measured"], 0)
                self.assertGreaterEqual(row[f"{metric}_theory"], 0)


if __name__ == "__main__":
    unittest.main()
