#!/usr/bin/env python3
"""
Build detailed error stats (A1/A2/B1/B2...) for final deleted questions.

Usage:
  python scripts/build_detailed_error_stats.py \
    --merged round1_多模型审核汇总.xlsx \
    --model-file GPT5.2=xxx.xlsx \
    --model-file Sonnet4.6=xxx.xlsx \
    --out-prefix round1_删除错误统计_细分
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


def normalize_delete(is_delete: str, confidence: str) -> str:
    c = str(confidence).strip()
    v = str(is_delete).strip()
    if c in {"肯定有", "疑似有"}:
        return "是"
    if c in {"肯定无", "疑似无"}:
        return "否"
    if v in {"是", "否"}:
        return v
    return "否"


def parse_subtypes(error_text: str) -> list[str]:
    s = str(error_text).upper().strip()
    if not s:
        return []
    s = (
        s.replace("，", ",")
        .replace("、", ",")
        .replace("；", ",")
        .replace(";", ",")
        .replace(" ", "")
    )
    parts = re.split(r"[,/|+]", s)
    out = []
    for p in parts:
        p = p.strip()
        if re.fullmatch(r"[ABC]\d+", p):
            out.append(p)
        elif re.fullmatch(r"[ABC]", p):
            out.append(p)
    return out


def load_model_file(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path).reset_index(drop=True)
    for col in ["是否删除", "错误类型", "删除原因", "疑似与肯定"]:
        if col not in df.columns:
            df[col] = ""
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged", required=True, help="Merged result xlsx path")
    parser.add_argument(
        "--model-file",
        action="append",
        required=True,
        help="Model file mapping, format: ModelName=/abs/path.xlsx",
    )
    parser.add_argument("--out-prefix", required=True, help="Output prefix without suffix")
    args = parser.parse_args()

    merged = pd.read_excel(args.merged).reset_index(drop=True)
    if "合并_是否删除" not in merged.columns:
        raise RuntimeError("Merged file missing column: 合并_是否删除")

    model_paths: dict[str, Path] = {}
    for item in args.model_file:
        if "=" not in item:
            raise RuntimeError(f"Invalid --model-file: {item}")
        name, p = item.split("=", 1)
        model_paths[name.strip()] = Path(p.strip())

    model_dfs = {name: load_model_file(path) for name, path in model_paths.items()}
    row_count = len(merged)
    for name, df in model_dfs.items():
        if len(df) != row_count:
            raise RuntimeError(f"Row mismatch for {name}: {len(df)} != {row_count}")

    detail_counter = Counter()
    family_counter = Counter()
    detail_examples: dict[str, list[dict]] = defaultdict(list)

    for i in range(row_count):
        if str(merged.at[i, "合并_是否删除"]).strip() != "是":
            continue

        qid = str(merged.at[i, "question_id"]) if "question_id" in merged.columns else f"Q{i+1:03d}"
        qtxt = str(merged.at[i, "问题"]) if "问题" in merged.columns else ""

        q_subtypes = set()
        subtype_reasons: dict[str, str] = {}

        for model, df in model_dfs.items():
            is_del = normalize_delete(df.at[i, "是否删除"], df.at[i, "疑似与肯定"])
            if is_del != "是":
                continue
            subs = parse_subtypes(df.at[i, "错误类型"])
            reason = str(df.at[i, "删除原因"]).strip()
            for sub in subs:
                q_subtypes.add(sub)
                if sub not in subtype_reasons and reason:
                    subtype_reasons[sub] = reason

        for sub in sorted(q_subtypes):
            detail_counter[sub] += 1
            fam = sub[0]
            family_counter[fam] += 1
            if len(detail_examples[sub]) < 2:
                detail_examples[sub].append(
                    {
                        "question_id": qid,
                        "问题摘要": qtxt.strip(),
                        "错误表现": subtype_reasons.get(sub, "").strip(),
                    }
                )

    # build dataframes
    detail_rows = [{"错误子类": k, "数量": v} for k, v in sorted(detail_counter.items(), key=lambda x: (x[0][0], int(re.sub(r"\D", "", x[0]) or 0)))]
    family_rows = [{"错误大类": k, "数量": v} for k, v in sorted(family_counter.items())]

    detail_df = pd.DataFrame(detail_rows)
    family_df = pd.DataFrame(family_rows)
    ex_rows = []
    for sub in sorted(detail_examples.keys(), key=lambda x: (x[0], int(re.sub(r"\D", "", x) or 0))):
        exs = detail_examples[sub]
        if not exs:
            ex_rows.append(
                {
                    "错误子类": sub,
                    "例1_question_id": "",
                    "例1_题目": "",
                    "例1_理由": "",
                    "例2_question_id": "",
                    "例2_题目": "",
                    "例2_理由": "",
                }
            )
            continue
        row = {"错误子类": sub}
        for idx in [0, 1]:
            if idx < len(exs):
                row[f"例{idx+1}_question_id"] = exs[idx]["question_id"]
                row[f"例{idx+1}_题目"] = exs[idx]["问题摘要"]
                row[f"例{idx+1}_理由"] = exs[idx]["错误表现"]
            else:
                row[f"例{idx+1}_question_id"] = ""
                row[f"例{idx+1}_题目"] = ""
                row[f"例{idx+1}_理由"] = ""
        ex_rows.append(row)
    ex_df = pd.DataFrame(ex_rows)

    out_prefix = Path(args.out_prefix)
    md_path = out_prefix.with_suffix(".md")
    xlsx_path = out_prefix.with_suffix(".xlsx")
    html_path = out_prefix.with_suffix(".html")

    # markdown
    lines = ["## 细分错误统计（删除题）", ""]
    for _, r in family_df.iterrows():
        lines.append(f"- {r['错误大类']}类：{int(r['数量'])}")
    lines.append("")
    lines.append("### 子类统计")
    for _, r in detail_df.iterrows():
        lines.append(f"- {r['错误子类']}：{int(r['数量'])}")
    lines.append("")
    lines.append("### 子类示例（每类2个）")
    for _, r in ex_df.iterrows():
        lines.append(f"- {r['错误子类']}")
        lines.append(f"  - 例1题号：{r['例1_question_id']}")
        lines.append(f"    - 题目：{r['例1_题目']}")
        lines.append(f"    - 理由：{r['例1_理由']}")
        lines.append(f"  - 例2题号：{r['例2_question_id']}")
        lines.append(f"    - 题目：{r['例2_题目']}")
        lines.append(f"    - 理由：{r['例2_理由']}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # xlsx
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        family_df.to_excel(writer, sheet_name="family_counts", index=False)
        detail_df.to_excel(writer, sheet_name="subtype_counts", index=False)
        ex_df.to_excel(writer, sheet_name="subtype_examples", index=False)

    # html
    fam_rows = "".join([f"<tr><td>{r['错误大类']}</td><td>{int(r['数量'])}</td></tr>" for _, r in family_df.iterrows()])
    sub_rows = "".join([f"<tr><td>{r['错误子类']}</td><td>{int(r['数量'])}</td></tr>" for _, r in detail_df.iterrows()])
    ex_rows_html = ""
    for _, r in ex_df.iterrows():
        ex_rows_html += (
            "<tr>"
            f"<td>{r['错误子类']}</td>"
            f"<td>{r['例1_question_id']}</td><td>{r['例1_题目']}</td><td>{r['例1_理由']}</td>"
            f"<td>{r['例2_question_id']}</td><td>{r['例2_题目']}</td><td>{r['例2_理由']}</td>"
            "</tr>"
        )
    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8" />
<title>细分错误统计</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;margin:24px;color:#1f2937;}}
table{{border-collapse:collapse;width:100%;margin:10px 0 18px;}}
th,td{{border:1px solid #e5e7eb;padding:8px 10px;vertical-align:top;}}
th{{background:#f9fafb;}}
</style></head><body>
<h1>细分错误统计（删除题）</h1>
<h2>大类统计</h2><table><thead><tr><th>错误大类</th><th>数量</th></tr></thead><tbody>{fam_rows}</tbody></table>
<h2>子类统计</h2><table><thead><tr><th>错误子类</th><th>数量</th></tr></thead><tbody>{sub_rows}</tbody></table>
<h2>子类示例（每类2个）</h2>
<table><thead><tr><th>错误子类</th><th>例1-题号</th><th>例1-题目</th><th>例1-理由</th><th>例2-题号</th><th>例2-题目</th><th>例2-理由</th></tr></thead><tbody>{ex_rows_html}</tbody></table>
</body></html>"""
    html_path.write_text(html, encoding="utf-8")

    print(f"md={md_path}")
    print(f"xlsx={xlsx_path}")
    print(f"html={html_path}")


if __name__ == "__main__":
    main()
