#!/usr/bin/env python3
"""
Export dashboard to HTML and Excel from review log.

Usage:
  python scripts/export_dashboard_views.py \
    --log review_log.csv \
    --round 1 \
    --stats round1_删除错误统计.md \
    --out-dir ./out
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd


STATUS_ORDER = ["done", "running", "pending", "blocked", "failed"]
STATUS_SYMBOL = {
    "done": "✓",
    "running": "…",
    "pending": "○",
    "blocked": "!",
    "failed": "x",
}


def pct(a: int, b: int) -> float:
    if b <= 0:
        return 0.0
    return round((a / b) * 100.0, 1)


def load_rows(log_path: Path, round_num: int) -> list[dict]:
    rows: list[dict] = []
    with log_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                r = int((row.get("round") or "0").strip())
            except ValueError:
                continue
            if r == round_num:
                rows.append(row)
    return rows


def summarize(rows: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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

    for row in rows:
        model = (row.get("model") or "unknown").strip()
        batch_id = (row.get("batch_id") or "").strip()
        status = (row.get("status") or "pending").strip().lower()
        stat = by_model[model]

        if batch_id:
            stat["all_batches"].add(batch_id)
            stat["batch_status"][batch_id] = status
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

    models = sorted(by_model.keys())
    summary_rows = []
    for model in models:
        s = by_model[model]
        total_batches = len(s["all_batches"])
        deletes = int(s["delete_count"])
        keeps = int(s["keep_count"])
        total = deletes + keeps
        main_errors = sorted([("A", s["A"]), ("B", s["B"]), ("C", s["C"])], key=lambda x: x[1], reverse=True)
        main_errors_txt = ">".join([k for k, v in main_errors if v > 0]) or "none"
        summary_rows.append(
            {
                "Model": model,
                "Done Batches": int(s["done_batches"]),
                "Total Batches": total_batches,
                "Completion %": pct(int(s["done_batches"]), total_batches),
                "Delete Rate %": pct(deletes, total),
                "Main Errors": main_errors_txt,
                "A": int(s["A"]),
                "B": int(s["B"]),
                "C": int(s["C"]),
            }
        )
    summary_df = pd.DataFrame(summary_rows)

    # batch matrix
    batch_ids = sorted({b for s in by_model.values() for b in s["all_batches"]})
    matrix_rows = []
    for model in models:
        row = {"Model": model}
        for b in batch_ids:
            status = by_model[model]["batch_status"].get(b, "pending")
            row[b] = STATUS_SYMBOL.get(status, "○")
        matrix_rows.append(row)
    matrix_df = pd.DataFrame(matrix_rows)

    # overall errors
    error_df = pd.DataFrame(
        [
            {
                "A类": int(summary_df["A"].sum()) if not summary_df.empty else 0,
                "B类": int(summary_df["B"].sum()) if not summary_df.empty else 0,
                "C类": int(summary_df["C"].sum()) if not summary_df.empty else 0,
            }
        ]
    )
    return summary_df, matrix_df, error_df


def load_detailed_stats(xlsx_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not xlsx_path.exists():
        return pd.DataFrame(), pd.DataFrame()
    try:
        subtypes = pd.read_excel(xlsx_path, sheet_name="subtype_counts")
        examples = pd.read_excel(xlsx_path, sheet_name="subtype_examples")
        return subtypes, examples
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


def bar_cell(value: float, color: str) -> str:
    width = max(0, min(100, value))
    return (
        f'<div style="background:#f2f4f8;border-radius:6px;width:180px;height:12px;display:inline-block;vertical-align:middle;">'
        f'<div style="background:{color};width:{width}%;height:12px;border-radius:6px;"></div></div>'
        f' <span style="font-size:12px;color:#444;">{value:.1f}%</span>'
    )


def to_html(
    round_num: int,
    summary_df: pd.DataFrame,
    matrix_df: pd.DataFrame,
    error_df: pd.DataFrame,
    subtype_counts_df: pd.DataFrame,
    subtype_examples_df: pd.DataFrame,
    out_html: Path,
) -> None:
    summary_html_rows = []
    for _, r in summary_df.iterrows():
        completion = bar_cell(float(r["Completion %"]), "#3b82f6")
        delete_rate = bar_cell(float(r["Delete Rate %"]), "#f59e0b")
        summary_html_rows.append(
            "<tr>"
            f"<td>{r['Model']}</td>"
            f"<td style='text-align:center'>{int(r['Done Batches'])}/{int(r['Total Batches'])}</td>"
            f"<td>{completion}</td>"
            f"<td>{delete_rate}</td>"
            f"<td style='text-align:center'>{r['Main Errors']}</td>"
            "</tr>"
        )

    matrix_head = "".join([f"<th>{c}</th>" for c in matrix_df.columns])
    matrix_rows = []
    for _, r in matrix_df.iterrows():
        tds = "".join([f"<td style='text-align:center'>{r[c]}</td>" for c in matrix_df.columns[1:]])
        matrix_rows.append(f"<tr><td>{r['Model']}</td>{tds}</tr>")

    a = int(error_df.iloc[0]["A类"]) if not error_df.empty else 0
    b = int(error_df.iloc[0]["B类"]) if not error_df.empty else 0
    c = int(error_df.iloc[0]["C类"]) if not error_df.empty else 0

    subtype_rows_html = ""
    if not subtype_counts_df.empty:
        for _, r in subtype_counts_df.iterrows():
            subtype_rows_html += f"<tr><td>{r['错误子类']}</td><td style='text-align:center'>{int(r['数量'])}</td></tr>"

    subtype_ex_rows_html = ""
    if not subtype_examples_df.empty:
        for _, r in subtype_examples_df.iterrows():
            subtype_ex_rows_html += (
                "<tr>"
                f"<td>{r.get('错误子类','')}</td>"
                f"<td>{r.get('例1_question_id','')}</td>"
                f"<td>{r.get('例1_题目','')}</td>"
                f"<td>{r.get('例1_理由','')}</td>"
                f"<td>{r.get('例2_question_id','')}</td>"
                f"<td>{r.get('例2_题目','')}</td>"
                f"<td>{r.get('例2_理由','')}</td>"
                "</tr>"
            )

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Round {round_num} Dashboard</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; margin: 24px; color: #1f2937; }}
    h1, h2, h3 {{ margin: 10px 0 12px; }}
    .cards {{ display: grid; grid-template-columns: repeat(3, minmax(140px, 220px)); gap: 12px; margin: 8px 0 18px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; background: #fafafa; }}
    .card .k {{ font-size: 12px; color: #6b7280; }}
    .card .v {{ font-size: 24px; font-weight: 700; margin-top: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 8px 0 18px; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 8px 10px; vertical-align: middle; }}
    th {{ background: #f9fafb; }}
    .legend span {{ margin-right: 12px; font-size: 13px; color: #374151; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }}
    .ex {{ margin: 6px 0; color: #374151; }}
  </style>
</head>
<body>
  <h1>Round {round_num} 审核看板</h1>

  <div class="cards">
    <div class="card"><div class="k">A类错误</div><div class="v">{a}</div></div>
    <div class="card"><div class="k">B类错误</div><div class="v">{b}</div></div>
    <div class="card"><div class="k">C类错误</div><div class="v">{c}</div></div>
  </div>

  <h2>模型进度与删除率</h2>
  <table>
    <thead>
      <tr><th>Model</th><th>批次完成</th><th>完成率</th><th>删除率</th><th>主错误</th></tr>
    </thead>
    <tbody>
      {''.join(summary_html_rows)}
    </tbody>
  </table>

  <h2>批次状态矩阵</h2>
  <div class="legend">
    <span>✓ done</span><span>… running</span><span>○ pending</span><span>! blocked</span><span>x failed</span>
  </div>
  <table>
    <thead><tr>{matrix_head}</tr></thead>
    <tbody>{''.join(matrix_rows)}</tbody>
  </table>

  <h2>细分错误统计（A1/B1...）</h2>
  <table>
    <thead><tr><th>错误子类</th><th>数量</th></tr></thead>
    <tbody>{subtype_rows_html}</tbody>
  </table>

  <h3>细分错误示例（每类2条）</h3>
  <table>
    <thead><tr><th>错误子类</th><th>例1-题号</th><th>例1-题目</th><th>例1-理由</th><th>例2-题号</th><th>例2-题目</th><th>例2-理由</th></tr></thead>
    <tbody>{subtype_ex_rows_html}</tbody>
  </table>
</body>
</html>
"""
    out_html.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("--round", required=True, type=int)
    parser.add_argument("--stats", required=False, default="")
    parser.add_argument("--detailed-stats-xlsx", required=False, default="")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(Path(args.log), args.round)
    summary_df, matrix_df, error_df = summarize(rows)
    subtype_counts_df, subtype_examples_df = (
        load_detailed_stats(Path(args.detailed_stats_xlsx))
        if args.detailed_stats_xlsx
        else (pd.DataFrame(), pd.DataFrame())
    )

    html_path = out_dir / f"round{args.round}_dashboard.html"
    xlsx_path = out_dir / f"round{args.round}_dashboard.xlsx"

    to_html(
        args.round,
        summary_df,
        matrix_df,
        error_df,
        subtype_counts_df,
        subtype_examples_df,
        html_path,
    )

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        matrix_df.to_excel(writer, sheet_name="batch_matrix", index=False)
        error_df.to_excel(writer, sheet_name="error_totals", index=False)
        if not subtype_counts_df.empty:
            subtype_counts_df.to_excel(writer, sheet_name="subtype_counts", index=False)
        if not subtype_examples_df.empty:
            subtype_examples_df.to_excel(writer, sheet_name="subtype_examples", index=False)

    print(f"html={html_path}")
    print(f"xlsx={xlsx_path}")


if __name__ == "__main__":
    main()
