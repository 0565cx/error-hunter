#!/usr/bin/env python3
"""
Build a markdown dashboard from review_log.csv.

Usage:
  python scripts/generate_dashboard.py \
    --log review_log.csv \
    --round 1 \
    --out round1_dashboard.md
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def pct(a: int, b: int) -> str:
    if b <= 0:
        return "0.0%"
    return f"{(a / b) * 100:.1f}%"


def load_rows(path: Path, round_num: int) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                r = int((row.get("round") or "0").strip())
            except ValueError:
                continue
            if r == round_num:
                rows.append(row)
    return rows


def summarize(rows: list[dict]) -> tuple[dict, dict]:
    by_model: dict[str, dict] = defaultdict(
        lambda: {
            "done_batches": 0,
            "all_batches": set(),
            "delete_count": 0,
            "keep_count": 0,
            "A": 0,
            "B": 0,
            "C": 0,
            "batch_status": {},
        }
    )
    blocked_or_failed = {"blocked", "failed"}
    risks: list[dict] = []

    for row in rows:
        model = (row.get("model") or "unknown").strip()
        status = (row.get("status") or "").strip().lower()
        batch_id = (row.get("batch_id") or "").strip()

        stat = by_model[model]
        if batch_id:
            stat["all_batches"].add(batch_id)
            stat["batch_status"][batch_id] = status or "pending"
        if status == "done":
            stat["done_batches"] += 1

        for src, key in [
            ("delete_count", "delete_count"),
            ("keep_count", "keep_count"),
            ("error_A_count", "A"),
            ("error_B_count", "B"),
            ("error_C_count", "C"),
        ]:
            try:
                stat[key] += int((row.get(src) or "0").strip())
            except ValueError:
                pass

        if status in blocked_or_failed:
            risks.append(
                {
                    "model": model,
                    "batch_id": batch_id or "-",
                    "status": status,
                    "notes": (row.get("notes") or "").strip(),
                }
            )

    return by_model, {"risks": risks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, help="Path to review_log.csv")
    parser.add_argument("--round", required=True, type=int, help="Round number")
    parser.add_argument("--out", required=True, help="Output markdown path")
    args = parser.parse_args()

    log_path = Path(args.log)
    out_path = Path(args.out)

    rows = load_rows(log_path, args.round)
    by_model, extra = summarize(rows)

    models = sorted(by_model.keys())
    done_counts = []
    max_batches = 0
    total_a = total_b = total_c = 0
    delete_rates: list[float] = []

    lines = []
    lines.append(f"## Round {args.round} Dashboard\n")
    lines.append("| Model | Done Batches | Total Batches | Completion | Delete Rate | Main Errors |")
    lines.append("|---|---:|---:|---:|---:|---|")

    for model in models:
        s = by_model[model]
        total_batches = len(s["all_batches"])
        done_batches = int(s["done_batches"])
        done_counts.append(done_batches)
        max_batches = max(max_batches, total_batches)

        deletes = int(s["delete_count"])
        keeps = int(s["keep_count"])
        total = deletes + keeps
        delete_rate = pct(deletes, total)
        delete_rate_num = (deletes / total * 100.0) if total > 0 else 0.0
        delete_rates.append(delete_rate_num)

        err_pairs = [("A", s["A"]), ("B", s["B"]), ("C", s["C"])]
        err_pairs.sort(key=lambda x: x[1], reverse=True)
        main_errors = ">".join([k for k, _ in err_pairs if _ > 0]) or "none"

        total_a += int(s["A"])
        total_b += int(s["B"])
        total_c += int(s["C"])

        lines.append(
            f"| {model} | {done_batches} | {total_batches} | {pct(done_batches, total_batches)} | {delete_rate} | {main_errors} |"
        )

    # Progress chart
    if models:
        model_labels = ",".join([f"\"{m}\"" for m in models])
        bar_vals = ",".join([str(v) for v in done_counts])
        lines.append("\n## Progress Chart\n")
        lines.append("```mermaid")
        lines.append("xychart-beta")
        lines.append(f"  title \"Round {args.round} model completion\"")
        lines.append(f"  x-axis [{model_labels}]")
        lines.append(f"  y-axis \"Done Batches\" 0 --> {max_batches or 1}")
        lines.append(f"  bar [{bar_vals}]")
        lines.append("```")

    # Delete-rate comparison chart
    if models:
        model_labels = ",".join([f"\"{m}\"" for m in models])
        rate_vals = ",".join([f"{x:.1f}" for x in delete_rates])
        lines.append("\n## Model Delete Rate Comparison\n")
        lines.append("```mermaid")
        lines.append("xychart-beta")
        lines.append(f"  title \"Round {args.round} model delete rate (%)\"")
        lines.append(f"  x-axis [{model_labels}]")
        lines.append("  y-axis \"Delete Rate %\" 0 --> 100")
        lines.append(f"  bar [{rate_vals}]")
        lines.append("```")

    # Batch status matrix
    if models:
        batch_union = set()
        for model in models:
            batch_union.update(by_model[model]["all_batches"])
        batches = sorted(batch_union)
        if batches:
            lines.append("\n## Batch Status Matrix\n")
            lines.append("| Model | " + " | ".join(batches) + " |")
            lines.append("|---|" + "|".join(["---"] * len(batches)) + "|")

            def status_symbol(status: str) -> str:
                mapping = {
                    "done": "✅",
                    "running": "🟡",
                    "pending": "⚪",
                    "blocked": "⛔",
                    "failed": "❌",
                }
                return mapping.get(status, "⚪")

            for model in models:
                stat = by_model[model]
                cells = []
                for b in batches:
                    s = stat["batch_status"].get(b, "pending")
                    cells.append(status_symbol(s))
                lines.append("| " + model + " | " + " | ".join(cells) + " |")

            lines.append("\n状态说明：`✅ done` `🟡 running` `⚪ pending` `⛔ blocked` `❌ failed`")

    # Error distribution chart
    lines.append("\n## Error Distribution\n")
    lines.append("```mermaid")
    lines.append(f"pie title \"Round {args.round} delete error mix\"")
    lines.append(f"  \"A类\" : {total_a}")
    lines.append(f"  \"B类\" : {total_b}")
    lines.append(f"  \"C类\" : {total_c}")
    lines.append("```")

    risks = extra["risks"]
    if risks:
        lines.append("\n## Intervention Alerts\n")
        for r in risks:
            notes = r["notes"] or "(no notes)"
            lines.append(
                f"- Model `{r['model']}` batch `{r['batch_id']}` is `{r['status']}`. Root cause: {notes}"
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
