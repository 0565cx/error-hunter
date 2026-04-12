#!/usr/bin/env python3
"""
Export round-specific output files from merged review result.

Rules:
- Round 1: export only no_issue_for_round2.xlsx
- Round 2+: export two handoff files (rewrite_answer / rewrite_question)

Usage:
  python scripts/export_round_outputs.py \
    --merged round1_多模型审核汇总.xlsx \
    --round 1 \
    --out-dir ./out \
    --answer-template /path/保留题干重出答案的知识点表格模版.xlsx \
    --question-template /path/待重新出题的知识点表格模版.xlsx
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROUND1_FIELDS = [
    "问题",
    "参考答案-第一层",
    "参考答案-第二层",
    "参考答案-第三层",
    "难度",
    "建议作答时间",
    "行业",
    "岗位名称",
    "技能分类",
    "技能",
    "知识点",
]


def export_from_template(src_df: pd.DataFrame, template_path: Path, out_path: Path) -> None:
    tpl = pd.read_excel(template_path)
    out = pd.DataFrame(index=range(len(src_df)), columns=tpl.columns)
    field_map = {
        "招聘场景": "场景",
        "行业": "行业",
        "岗位": "岗位名称",
        "JD": None,      # keep empty by requirement
        "技能分类": "技能分类",
        "技能": "技能",
        "知识点": "知识点",
        "问题": "问题",
        "提示词": None,  # keep empty by requirement
    }
    for c in out.columns:
        src = field_map.get(c)
        if src and src in src_df.columns:
            out[c] = src_df[src].values
        else:
            out[c] = ""
    out.to_excel(out_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged", required=True, help="Merged review xlsx path")
    parser.add_argument("--round", required=True, type=int)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--answer-template", required=True)
    parser.add_argument("--question-template", required=True)
    args = parser.parse_args()

    merged = pd.read_excel(args.merged)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.round == 1:
        # Prefer merged final decision if available, fallback to keep-only action.
        if "合并_是否删除" in merged.columns:
            r2_df = merged[merged["合并_是否删除"].astype(str).str.strip() == "否"].copy()
        elif "合并_建议动作" in merged.columns:
            r2_df = merged[merged["合并_建议动作"].astype(str).str.strip() == "keep"].copy()
        else:
            r2_df = merged.copy()

        cols = [c for c in ROUND1_FIELDS if c in r2_df.columns]
        out_path = out_dir / "待二轮审核题表.xlsx"
        r2_df[cols].to_excel(out_path, index=False)
        print(f"round1_no_issue={out_path}")
        return

    # Round 2+ handoff
    if "合并_建议动作" not in merged.columns:
        raise RuntimeError("Merged file missing column: 合并_建议动作")

    rewrite_answer_df = merged[merged["合并_建议动作"].astype(str).str.strip() == "rewrite_answer"].copy()
    rewrite_question_df = merged[merged["合并_建议动作"].astype(str).str.strip() == "rewrite_question"].copy()

    ans_out = out_dir / "保留题干重出答案_交付表.xlsx"
    q_out = out_dir / "待重新出题_交付表.xlsx"
    export_from_template(rewrite_answer_df, Path(args.answer_template), ans_out)
    export_from_template(rewrite_question_df, Path(args.question_template), q_out)
    print(f"round{args.round}_rewrite_answer={ans_out}")
    print(f"round{args.round}_rewrite_question={q_out}")


if __name__ == "__main__":
    main()
