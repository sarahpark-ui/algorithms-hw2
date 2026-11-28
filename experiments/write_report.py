"""Write a one-page, dependency-free PDF summary of the probe experiment."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "probe_results.csv"
PDF_PATH = ROOT / "probe_report.pdf"
PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def _pdf_text(x, y, text, size=9, bold=False):
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    font = "/F2" if bold else "/F1"
    return f"BT {font} {size} Tf {x:.1f} {y:.1f} Td ({safe}) Tj ET\n"


def _line(x1, y1, x2, y2, color=(0.2, 0.2, 0.2), width=0.7, dashed=False):
    r, g, b = color
    dash = "[4 3] 0 d " if dashed else "[] 0 d "
    return (
        f"{r:.3f} {g:.3f} {b:.3f} RG {width:.1f} w {dash}"
        f"{x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S [] 0 d\n"
    )


def _chart(rows, metric, title, left):
    chart_bottom = 512
    chart_width = 250
    plot_left = left + 35
    plot_bottom = chart_bottom + 20
    plot_width = 205
    plot_height = 122
    values = [
        row[f"{metric}_{kind}"]
        for row in rows
        for kind in ("measured", "theory")
    ]
    max_value = max(values) * 1.08 or 1
    output = [_pdf_text(left, chart_bottom + 160, title, 10, True)]

    for tick in range(4):
        fraction = tick / 3
        y = plot_bottom + fraction * plot_height
        value = fraction * max_value
        output.append(_line(plot_left, y, plot_left + plot_width, y, (0.85, 0.85, 0.85), 0.4))
        output.append(_pdf_text(plot_left - 28, y - 3, f"{value:.1f}", 7))
    output.append(_line(plot_left, plot_bottom, plot_left, plot_bottom + plot_height))
    output.append(_line(plot_left, plot_bottom, plot_left + plot_width, plot_bottom))

    for load in (0.1, 0.5, 0.9):
        x = plot_left + (load - 0.1) / 0.8 * plot_width
        output.append(_pdf_text(x - 7, plot_bottom - 13, f"{load:.1f}", 7))
    output.append(_pdf_text(plot_left + 60, chart_bottom + 1, "Load factor", 8))

    colors = {"chaining": (0.09, 0.41, 0.67), "linear": (0.82, 0.28, 0.35)}
    for strategy in ("chaining", "linear"):
        for kind in ("measured", "theory"):
            points = []
            for row in rows:
                if row["strategy"] != strategy:
                    continue
                x = plot_left + (row["load_factor"] - 0.1) / 0.8 * plot_width
                y = plot_bottom + row[f"{metric}_{kind}"] / max_value * plot_height
                points.append((x, y))
            for first, second in zip(points, points[1:]):
                output.append(
                    _line(
                        first[0],
                        first[1],
                        second[0],
                        second[1],
                        colors[strategy],
                        1.4,
                        kind == "theory",
                    )
                )

    legend_y = chart_bottom - 14
    for index, (strategy, label, theoretical) in enumerate((
        ("chaining", "Chain", False),
        ("chaining", "Chain theory", True),
        ("linear", "Linear", False),
        ("linear", "Linear theory", True),
    )):
        x = left + 4 + index * 61
        output.append(
            _line(x, legend_y + 3, x + 12, legend_y + 3, colors[strategy], 1.3, theoretical)
        )
        output.append(_pdf_text(x + 14, legend_y, label, 6))
    return "".join(output)


def _find_row(rows, strategy, target_load):
    candidates = [row for row in rows if row["strategy"] == strategy]
    return min(candidates, key=lambda row: abs(row["load_factor"] - target_load))


def create_report():
    with CSV_PATH.open(newline="", encoding="utf-8") as file:
        rows = [
            {
                key: (float(value) if key.endswith("_measured") or key.endswith("_theory")
                      or key == "load_factor" else value)
                for key, value in row.items()
            }
            for row in csv.DictReader(file)
        ]

    content = [
        _pdf_text(50, 755, "Hash Table Probe Cost Comparison", 17, True),
        _pdf_text(50, 737, "Separate chaining vs. linear probing | fixed capacity: 4,096", 10),
        _pdf_text(50, 718, "Same deterministic 12-character key set; load factors 0.1-0.9.", 9),
        _pdf_text(50, 704, "Averages count key equality checks separately from array-slot checks.", 9),
        _chart(rows, "successful_comparisons", "Successful lookup: key comparisons", 42),
        _chart(rows, "unsuccessful_comparisons", "Unsuccessful lookup: key comparisons", 320),
        _pdf_text(50, 478, "Theory (uniform hashing): chaining hit 1+alpha/2, miss alpha; linear-probing", 8),
        _pdf_text(50, 466, "probes: hit 0.5*(1+1/(1-alpha)), miss 0.5*(1+1/(1-alpha)^2).", 8),
        _pdf_text(50, 449, "Selected measurements / theory (comparisons; slots), averages per lookup:", 9, True),
    ]
    headers = (
        (50, "Method"),
        (121, "Load"),
        (168, "Hit cmp"),
        (229, "Miss cmp"),
        (294, "Hit slots"),
        (362, "Miss slots"),
    )
    for x, label in headers:
        content.append(_pdf_text(x, 431, label, 8, True))
    content.append(_line(48, 426, 420, 426, width=0.5))

    y = 411
    for target in (0.1, 0.5, 0.9):
        for strategy, display in (("chaining", "Chain"), ("linear", "Linear")):
            row = _find_row(rows, strategy, target)
            hit_cmp = f'{row["successful_comparisons_measured"]:.2f}/{row["successful_comparisons_theory"]:.2f}'
            miss_cmp = f'{row["unsuccessful_comparisons_measured"]:.2f}/{row["unsuccessful_comparisons_theory"]:.2f}'
            hit_slots = f'{row["successful_slots_measured"]:.2f}/{row["successful_slots_theory"]:.2f}'
            miss_slots = f'{row["unsuccessful_slots_measured"]:.2f}/{row["unsuccessful_slots_theory"]:.2f}'
            content.extend((
                _pdf_text(50, y, display, 8),
                _pdf_text(121, y, f'{row["load_factor"]:.2f}', 8),
                _pdf_text(168, y, hit_cmp, 8),
                _pdf_text(229, y, miss_cmp, 8),
                _pdf_text(294, y, hit_slots, 8),
                _pdf_text(362, y, miss_slots, 8),
            ))
            y -= 13
    content.extend((
        _line(48, y + 6, 420, y + 6, width=0.5),
        _pdf_text(50, 304, "Reading: each cell is measured/theory. Chaining checks one bucket slot;", 8),
        _pdf_text(50, 291, "linear probing checks each visited slot, including the terminating empty slot.", 8),
        _pdf_text(50, 269, "The theoretical curves assume uniformly distributed home slots. Our fixed", 8),
        _pdf_text(50, 256, "Horner hash and finite sample can deviate, especially as primary clusters grow.", 8),
        _pdf_text(50, 234, "Artifacts: probe_results.csv (all 18 rows) and probe_results.svg (four metrics).", 8),
        _pdf_text(50, 214, "Reproduce with: make experiment && make report", 8, True),
    ))
    _write_pdf("".join(content))
    return PDF_PATH


def _write_pdf(content):
    stream = content.encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
        + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    PDF_PATH.write_bytes(output)


if __name__ == "__main__":
    print(f"Generated {create_report().relative_to(ROOT.parent)}")
