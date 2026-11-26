"""Measure separate-chaining lookup costs and write a CSV table and SVG chart."""

import csv
from pathlib import Path

from src.hash_table import HashTable


CAPACITY = 4096
LOAD_FACTORS = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)
MISS_QUERIES = 2048
OUTPUT_DIR = Path(__file__).resolve().parent


def measure(load_factor):
    table = HashTable(capacity=CAPACITY)
    item_count = round(CAPACITY * load_factor)
    keys = [f"item-{index:08d}" for index in range(item_count)]
    for index, key in enumerate(keys):
        table.put(key, index)

    successful = 0
    for key in keys:
        table.get(key)
        successful += table.last_comparisons

    unsuccessful = 0
    for index in range(MISS_QUERIES):
        try:
            table.get(f"missing-{index:08d}")
        except KeyError:
            unsuccessful += table.last_comparisons

    return {
        "load_factor": item_count / CAPACITY,
        "items": item_count,
        "successful_measured": successful / item_count,
        "successful_theory": 1 + (item_count / CAPACITY) / 2,
        "unsuccessful_measured": unsuccessful / MISS_QUERIES,
        "unsuccessful_theory": item_count / CAPACITY,
    }


def write_csv(rows):
    output = OUTPUT_DIR / "probe_results.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(
            {key: f"{value:.4f}" if isinstance(value, float) else value for key, value in row.items()}
            for row in rows
        )
    return output


def write_svg(rows):
    width, height = 900, 520
    left, right, top, bottom = 80, 30, 45, 80
    plot_width, plot_height = width - left - right, height - top - bottom
    max_x = 4.0
    max_y = max(row[key] for row in rows for key in (
        "successful_measured", "successful_theory", "unsuccessful_measured", "unsuccessful_theory"
    )) * 1.12

    def point(row, key):
        x = left + row["load_factor"] / max_x * plot_width
        y = top + (1 - row[key] / max_y) * plot_height
        return f"{x:.1f},{y:.1f}"

    series = (
        ("successful_measured", "#1769aa", "성공 탐색 측정"),
        ("successful_theory", "#1769aa", "성공 탐색 이론"),
        ("unsuccessful_measured", "#d1495b", "실패 탐색 측정"),
        ("unsuccessful_theory", "#d1495b", "실패 탐색 이론"),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="25" text-anchor="middle" font-family="sans-serif" font-size="18">적재율별 평균 탐색 비교 횟수</text>',
    ]

    for tick in range(5):
        value = max_y * tick / 4
        y = top + (1 - tick / 4) * plot_height
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#ddd"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{value:.1f}</text>')
        x = left + tick / 4 * plot_width
        parts.append(f'<text x="{x:.1f}" y="{height-bottom+22}" text-anchor="middle" font-family="sans-serif" font-size="12">{tick}</text>')
    parts.extend((
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#333"/>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#333"/>',
        f'<text x="{left + plot_width/2}" y="{height-18}" text-anchor="middle" font-family="sans-serif" font-size="14">적재율 (α)</text>',
        f'<text x="20" y="{top + plot_height/2}" text-anchor="middle" transform="rotate(-90 20 {top + plot_height/2})" font-family="sans-serif" font-size="14">평균 비교 횟수</text>',
    ))

    legend_y = height - 52
    for index, (key, color, label) in enumerate(series):
        row_index, column = divmod(index, 2)
        x = left + column * 365
        y = legend_y + row_index * 20
        dash = ' stroke-dasharray="6 4"' if key.endswith("_theory") else ""
        coordinates = " ".join(point(row, key) for row in rows)
        parts.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="2"{dash}/>')
        parts.append(f'<line x1="{x}" y1="{y}" x2="{x+26}" y2="{y}" stroke="{color}" stroke-width="2"{dash}/>')
        parts.append(f'<text x="{x+34}" y="{y+4}" font-family="sans-serif" font-size="12">{label}</text>')
    parts.append("</svg>")

    output = OUTPUT_DIR / "probe_results.svg"
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return output


def main():
    rows = [measure(load_factor) for load_factor in LOAD_FACTORS]
    csv_path = write_csv(rows)
    svg_path = write_svg(rows)
    successful_error = max(abs(row["successful_measured"] - row["successful_theory"]) for row in rows)
    unsuccessful_error = max(abs(row["unsuccessful_measured"] - row["unsuccessful_theory"]) for row in rows)

    print("α, 성공 측정/이론, 실패 측정/이론")
    for row in rows:
        print(
            f'{row["load_factor"]:.2f}, '
            f'{row["successful_measured"]:.3f}/{row["successful_theory"]:.3f}, '
            f'{row["unsuccessful_measured"]:.3f}/{row["unsuccessful_theory"]:.3f}'
        )
    print(f"최대 절대 오차: 성공 {successful_error:.3f}, 실패 {unsuccessful_error:.3f}")
    print(f"생성: {csv_path.relative_to(OUTPUT_DIR.parent)}, {svg_path.relative_to(OUTPUT_DIR.parent)}")
    print("이론값은 균등 분포 가정의 평균이다. 고정 키/용량에서는 해시 분포와 유한 표본 때문에 차이가 난다.")


if __name__ == "__main__":
    main()
