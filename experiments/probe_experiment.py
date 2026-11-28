"""Compare separate chaining and linear probing lookup costs."""

import csv
from pathlib import Path
import random

from src.hash_table import HashTable, LinearProbingHashTable


CAPACITY = 4096
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
MISS_QUERIES = 2048
OUTPUT_DIR = Path(__file__).resolve().parent
METRICS = (
    ("successful_comparisons", "성공 탐색 키 비교"),
    ("unsuccessful_comparisons", "실패 탐색 키 비교"),
    ("successful_slots", "성공 탐색 슬롯 확인"),
    ("unsuccessful_slots", "실패 탐색 슬롯 확인"),
)
TABLES = (
    ("chaining", HashTable),
    ("linear", LinearProbingHashTable),
)


def _theoretical_costs(strategy, load_factor):
    if strategy == "chaining":
        return {
            "successful_comparisons": 1 + load_factor / 2,
            "unsuccessful_comparisons": load_factor,
            "successful_slots": 1,
            "unsuccessful_slots": 1,
        }
    successful_probes = 0.5 * (1 + 1 / (1 - load_factor))
    unsuccessful_probes = 0.5 * (1 + 1 / (1 - load_factor) ** 2)
    return {
        "successful_comparisons": successful_probes,
        "unsuccessful_comparisons": unsuccessful_probes - 1,
        "successful_slots": successful_probes,
        "unsuccessful_slots": unsuccessful_probes,
    }


def measure(load_factor, capacity=CAPACITY, miss_queries=MISS_QUERIES):
    item_count = round(capacity * load_factor)
    actual_load = item_count / capacity
    generator = random.Random(2026)
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    keys = [
        "".join(generator.choices(alphabet, k=12))
        for _ in range(item_count)
    ]
    misses = [f"missing-{index:08d}" for index in range(miss_queries)]
    rows = []

    for strategy, table_class in TABLES:
        table = table_class(capacity=capacity)
        for index, key in enumerate(keys):
            table.put(key, index)

        measured = {
            "successful_comparisons": 0,
            "unsuccessful_comparisons": 0,
            "successful_slots": 0,
            "unsuccessful_slots": 0,
        }
        for key in keys:
            table.get(key)
            measured["successful_comparisons"] += table.last_comparisons
            measured["successful_slots"] += table.last_slot_checks

        for key in misses:
            try:
                table.get(key)
            except KeyError:
                measured["unsuccessful_comparisons"] += table.last_comparisons
                measured["unsuccessful_slots"] += table.last_slot_checks

        theory = _theoretical_costs(strategy, actual_load)
        row = {
            "strategy": strategy,
            "load_factor": actual_load,
            "items": item_count,
            "successful_queries": item_count,
            "unsuccessful_queries": miss_queries,
        }
        for metric, _ in METRICS:
            divisor = item_count if metric.startswith("successful") else miss_queries
            row[f"{metric}_measured"] = measured[metric] / divisor
            row[f"{metric}_theory"] = theory[metric]
        rows.append(row)
    return rows


def write_csv(rows):
    output = OUTPUT_DIR / "probe_results.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys(),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {
                key: f"{value:.4f}" if isinstance(value, float) else value
                for key, value in row.items()
            }
            for row in rows
        )
    return output


def write_svg(rows):
    width, height = 1000, 760
    panels = (
        (70, 55, 410, 275),
        (545, 55, 410, 275),
        (70, 405, 410, 275),
        (545, 405, 410, 275),
    )
    colors = {"chaining": "#1769aa", "linear": "#d1495b"}
    labels = {"chaining": "별도 체이닝", "linear": "선형 탐지"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="28" text-anchor="middle" font-family="sans-serif" font-size="19">적재율별 탐색 비용: 실측과 이론</text>',
    ]

    for (metric, title), (left, top, panel_width, panel_height) in zip(METRICS, panels):
        plot_left, plot_top = left + 48, top + 36
        plot_width, plot_height = panel_width - 62, panel_height - 82
        all_values = [
            row[f"{metric}_{kind}"]
            for row in rows
            for kind in ("measured", "theory")
        ]
        max_y = max(all_values) * 1.12 or 1
        parts.append(
            f'<text x="{left + panel_width/2}" y="{top + 18}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="14">{title}</text>'
        )
        for tick in range(4):
            fraction = tick / 3
            value = max_y * fraction
            y = plot_top + (1 - fraction) * plot_height
            parts.append(
                f'<line x1="{plot_left}" y1="{y:.1f}" x2="{plot_left + plot_width}" '
                f'y2="{y:.1f}" stroke="#ddd"/>'
            )
            parts.append(
                f'<text x="{plot_left - 7}" y="{y + 4:.1f}" text-anchor="end" '
                f'font-family="sans-serif" font-size="10">{value:.1f}</text>'
            )
        for tick in range(1, 10, 2):
            load = tick / 10
            x = plot_left + (load - 0.1) / 0.8 * plot_width
            parts.append(
                f'<text x="{x:.1f}" y="{plot_top + plot_height + 17}" '
                f'text-anchor="middle" font-family="sans-serif" font-size="10">{load:.1f}</text>'
            )
        parts.extend((
            f'<line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" '
            f'y2="{plot_top + plot_height}" stroke="#333"/>',
            f'<line x1="{plot_left}" y1="{plot_top + plot_height}" '
            f'x2="{plot_left + plot_width}" y2="{plot_top + plot_height}" stroke="#333"/>',
            f'<text x="{plot_left + plot_width/2}" y="{top + panel_height - 7}" '
            'text-anchor="middle" font-family="sans-serif" font-size="11">적재율 (α)</text>',
        ))

        for strategy, _ in TABLES:
            for kind in ("measured", "theory"):
                points = []
                for row in rows:
                    if row["strategy"] != strategy:
                        continue
                    x = plot_left + (row["load_factor"] - 0.1) / 0.8 * plot_width
                    y = plot_top + (
                        1 - row[f"{metric}_{kind}"] / max_y
                    ) * plot_height
                    points.append(f"{x:.1f},{y:.1f}")
                dash = ' stroke-dasharray="5 4"' if kind == "theory" else ""
                parts.append(
                    f'<polyline points="{" ".join(points)}" fill="none" '
                    f'stroke="{colors[strategy]}" stroke-width="2"{dash}/>'
                )

    legend = (
        ("chaining", "별도 체이닝 실측", False),
        ("chaining", "별도 체이닝 이론", True),
        ("linear", "선형 탐지 실측", False),
        ("linear", "선형 탐지 이론", True),
    )
    for index, (strategy, label, theoretical) in enumerate(legend):
        x = 170 + index * 190
        dash = ' stroke-dasharray="5 4"' if theoretical else ""
        parts.append(
            f'<line x1="{x}" y1="730" x2="{x + 25}" y2="730" '
            f'stroke="{colors[strategy]}" stroke-width="2"{dash}/>'
        )
        parts.append(
            f'<text x="{x + 31}" y="734" font-family="sans-serif" font-size="11">{label}</text>'
        )
    parts.append("</svg>")
    output = OUTPUT_DIR / "probe_results.svg"
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return output


def main():
    rows = [
        row
        for load_factor in LOAD_FACTORS
        for row in measure(load_factor)
    ]
    csv_path = write_csv(rows)
    svg_path = write_svg(rows)

    print("적재율별 평균 탐색 비용 (실측 / 이론)")
    for row in rows:
        print(
            f'{row["strategy"]:8} α={row["load_factor"]:.2f} '
            f'성공 비교 {row["successful_comparisons_measured"]:.3f}/'
            f'{row["successful_comparisons_theory"]:.3f}, '
            f'실패 비교 {row["unsuccessful_comparisons_measured"]:.3f}/'
            f'{row["unsuccessful_comparisons_theory"]:.3f}, '
            f'성공 슬롯 {row["successful_slots_measured"]:.3f}/'
            f'{row["successful_slots_theory"]:.3f}, '
            f'실패 슬롯 {row["unsuccessful_slots_measured"]:.3f}/'
            f'{row["unsuccessful_slots_theory"]:.3f}'
        )
    print(f"생성: {csv_path.relative_to(OUTPUT_DIR.parent)}, {svg_path.relative_to(OUTPUT_DIR.parent)}")
    print("이론값은 균등 분포 가정의 평균값이다. 키 집합/해시 분포에 따라 실측값과 차이가 난다.")


if __name__ == "__main__":
    main()
