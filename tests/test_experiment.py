import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from experiments import probe_experiment, write_report
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

    def test_writes_csv_to_required_results_filename(self):
        rows = measure(0.5, capacity=100, miss_queries=20)

        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            with patch.object(probe_experiment, "OUTPUT_DIR", output_dir):
                csv_path = probe_experiment.write_csv(rows)

            self.assertEqual(csv_path, output_dir / "results.csv")
            with csv_path.open(newline="", encoding="utf-8") as file:
                self.assertEqual(len(list(csv.DictReader(file))), 2)

    def test_report_explains_spec_correction_and_measured_performance(self):
        rows = [
            row
            for load_factor in (0.1, 0.5, 0.9)
            for row in measure(load_factor, capacity=100, miss_queries=20)
        ]
        linear_high_load = next(
            row
            for row in rows
            if row["strategy"] == "linear" and row["load_factor"] == 0.9
        )

        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            csv_path = output_dir / "results.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=rows[0].keys(), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)

            pdf_path = output_dir / "report.pdf"
            with (
                patch.object(write_report, "CSV_PATH", csv_path),
                patch.object(write_report, "PDF_PATH", pdf_path),
            ):
                write_report.create_report()

            pdf = pdf_path.read_bytes()
            self.assertIn(b"181598c", pdf)
            self.assertIn(b"Initial SPEC draft", pdf)
            self.assertIn(
                f'{linear_high_load["unsuccessful_slots_measured"]:.2f}'.encode(),
                pdf,
            )
            self.assertIn(b"primary clustering", pdf)
            page_tree = pdf.split(b"/Type /Pages", 1)[1]
            page_count = int(page_tree.split(b"/Count ", 1)[1].split()[0])
            self.assertLessEqual(page_count, 2)


if __name__ == "__main__":
    unittest.main()
