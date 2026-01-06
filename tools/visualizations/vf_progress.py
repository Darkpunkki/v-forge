#!/usr/bin/env python3
r"""
VibeForge checklist progress visualizer

Reads the VibeForge master checklist markdown and produces:
- progress_by_category.png  (stacked bar chart: Done vs Remaining)
- progress_by_category.csv  (summary table)
- progress_summary.txt      (human-readable summary)

Default checklist path (Windows):
  C:\Apps\vibeforge_skeleton\vibeforge_master_checklist.md

Output directory (relative to THIS script):
  tools/visualizations/reports/reports_<day>_<month>_<yy>
Example for Jan 5, 2026:
  tools/visualizations/reports/reports_5_1_26

If the output directory already exists and a report filename already exists,
the script avoids overwriting by adding a numeric suffix:
  progress_by_category.png
  progress_by_category_1.png
  progress_by_category_2.png

Usage:
  python tools/visualizations/vf_progress.py

Optional overrides:
  python tools/visualizations/vf_progress.py --checklist "C:\path\to\checklist.md"
  python tools/visualizations/vf_progress.py --sort percent
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


# --- Defaults (tuned to your repo path) ---
DEFAULT_CHECKLIST = Path(r"C:\Apps\vibeforge_skeleton\vibeforge_master_checklist.md")

# --- Output base (relative to script location) ---
BASE_DIR = Path(__file__).resolve().parent                      # .../tools/visualizations
REPORTS_BASE = BASE_DIR / "reports"                             # .../tools/visualizations/reports


# --- Parsing rules ---
# Accept ## or ### headings, and allow "14.", "14)", "14 -" etc.
CATEGORY_RE = re.compile(r"^#{2,3}\s+(?:(\d+)\s*[\.\)\-–—:]?\s+)?(.+?)\s*$")

# Accept "-" or "*" bullets; bold optional; accept — / – / - / : as separator; spaces optional
TASK_RE = re.compile(
    r"^\s*[-*]\s*\[(?P<mark>[ xX])\]\s+"
    r"(?:\*\*)?VF-(?P<id>\d+)(?:\*\*)?\s*"
    r"(?:[—–-]|:)\s*"
    r"(?P<title>.+?)"
    r"(?:\*\*)?\s*$"
)



@dataclass
class Task:
    vf_id: int
    title: str
    done: bool


@dataclass
class Category:
    number: Optional[int]
    name: str
    tasks: List[Task]


def parse_checklist(md_text: str) -> List[Category]:
    categories: List[Category] = []
    current: Optional[Category] = None

    for line in md_text.splitlines():
        m_cat = CATEGORY_RE.match(line.strip())
        if m_cat:
            num_str, name = m_cat.group(1), m_cat.group(2).strip()
            if name:
                current = Category(
                    number=int(num_str) if num_str is not None else None,
                    name=name,
                    tasks=[],
                )
                categories.append(current)
            continue

        m_task = TASK_RE.match(line)
        if m_task and current is not None:
            done = (m_task.group("mark").lower() == "x")
            vf_id = int(m_task.group("id"))
            title = m_task.group("title").strip()
            current.tasks.append(Task(vf_id=vf_id, title=title, done=done))

    # Ignore headings that ended up with zero tasks (narrative headings, etc.)
    categories = [c for c in categories if len(c.tasks) > 0]
    return categories


def summarize(categories: List[Category]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for c in categories:
        total = len(c.tasks)
        done = sum(1 for t in c.tasks if t.done)
        pct = (done / total * 100.0) if total else 0.0
        rows.append(
            {
                "module_number": c.number if c.number is not None else "",
                "category": c.name,
                "done": done,
                "total": total,
                "percent_done": round(pct, 1),
            }
        )

    def sort_key(r: Dict[str, object]) -> Tuple[int, str]:
        num = r["module_number"]
        if isinstance(num, int):
            return (num, str(r["category"]))
        return (10_000, str(r["category"]))

    rows.sort(key=sort_key)
    return rows


def dated_reports_dir_name(today: dt.date) -> str:
    # reports_<day>_<month>_<yy> (no leading zeros for day/month; yy is 2 digits)
    return f"reports_{today.day}_{today.month}_{today.year % 100:02d}"


def next_available_path(path: Path) -> Path:
    """
    If `path` exists, return path with _1/_2/... suffix before extension.
    Example:
      progress_by_category.png -> progress_by_category_1.png
    """
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def write_csv(rows: List[Dict[str, object]], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path = next_available_path(out_path)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["module_number", "category", "done", "total", "percent_done"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def write_text_summary(rows: List[Dict[str, object]], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path = next_available_path(out_path)

    overall_done = sum(int(r["done"]) for r in rows)
    overall_total = sum(int(r["total"]) for r in rows)
    overall_pct = (overall_done / overall_total * 100.0) if overall_total else 0.0

    lines: List[str] = []
    lines.append(f"Overall: {overall_done}/{overall_total} ({overall_pct:.1f}%)")
    lines.append("")
    lines.append("By category:")
    for r in rows:
        num = r["module_number"]
        prefix = f"{num:>2} " if isinstance(num, int) else "   "
        lines.append(
            f"{prefix}{r['category']}: {r['done']}/{r['total']} ({r['percent_done']}%)"
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def plot(rows: List[Dict[str, object]], out_path: Path, *, sort_by: str = "module") -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path = next_available_path(out_path)

    plot_rows = rows.copy()
    if sort_by == "percent":
        plot_rows.sort(key=lambda r: float(r["percent_done"]))
    elif sort_by == "remaining":
        plot_rows.sort(key=lambda r: (int(r["total"]) - int(r["done"])), reverse=True)
    # default "module" already sorted

    labels: List[str] = []
    done_vals: List[int] = []
    total_vals: List[int] = []

    for r in plot_rows:
        num = r["module_number"]
        label = f"{num} {r['category']}" if isinstance(num, int) else str(r["category"])
        labels.append(label)
        done_vals.append(int(r["done"]))
        total_vals.append(int(r["total"]))

    remaining_vals = [t - d for t, d in zip(total_vals, done_vals)]
    y = list(range(len(labels)))

    fig_h = max(4.0, min(0.45 * len(labels) + 1.5, 20.0))
    fig, ax = plt.subplots(figsize=(12, fig_h))

    ax.barh(y, done_vals, label="Done")
    ax.barh(y, remaining_vals, left=done_vals, label="Remaining")

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()

    overall_done = sum(done_vals)
    overall_total = sum(total_vals)
    overall_pct = (overall_done / overall_total * 100.0) if overall_total else 0.0
    ax.set_title(
        f"VibeForge Progress by Category — {overall_done}/{overall_total} ({overall_pct:.1f}%)"
    )
    ax.set_xlabel("Tasks")
    ax.legend(loc="lower right")

    # Percent labels at end of each bar
    for i, (d, t) in enumerate(zip(done_vals, total_vals)):
        pct = (d / t * 100.0) if t else 0.0
        ax.text(t + 0.1, i, f"{pct:.0f}%", va="center", fontsize=9)

    plt.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Visualize progress from vibeforge_master_checklist.md"
    )
    parser.add_argument(
        "--checklist",
        default=str(DEFAULT_CHECKLIST),
        help=r"Path to checklist markdown (default: C:\Apps\vibeforge_skeleton\vibeforge_master_checklist.md)",
    )
    parser.add_argument(
        "--sort",
        choices=["module", "percent", "remaining"],
        default="module",
        help="Sort order for the chart",
    )
    args = parser.parse_args()

    checklist_path = Path(args.checklist)
    if not checklist_path.exists():
        raise SystemExit(f"Checklist not found: {checklist_path.resolve()}")

    md_text = checklist_path.read_text(encoding="utf-8")
    categories = parse_checklist(md_text)
    if not categories:
        raise SystemExit(
            "No categories/tasks found. Ensure headings are '### <num> <name>' and tasks are '- [ ] **VF-...**'."
        )

    rows = summarize(categories)

    today = dt.date.today()
    out_dir = REPORTS_BASE / dated_reports_dir_name(today)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = write_csv(rows, out_dir / "progress_by_category.csv")
    txt_path = write_text_summary(rows, out_dir / "progress_summary.txt")
    png_path = plot(rows, out_dir / "progress_by_category.png", sort_by=args.sort)

    print(f"Wrote reports to: {out_dir.resolve()}")
    print(f" - {png_path.name}")
    print(f" - {csv_path.name}")
    print(f" - {txt_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
