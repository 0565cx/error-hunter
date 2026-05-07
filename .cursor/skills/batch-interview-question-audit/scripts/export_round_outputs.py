#!/usr/bin/env python3
"""
Export round-specific output files from merged review result.

Rules:
- Round 1: export no_issue_for_round2.xlsx as the next round input
- Round 2+: export one review summary workbook with keep/rewrite_question/rewrite_answer sheets

Usage:
  python scripts/export_round_outputs.py \
    --merged round1_多模型审核汇总.xlsx \
    --round 1 \
    --out-dir ./out
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROUND1_FIELDS = [
    "问题",
    "第一层",
    "第二层",
    "第三层",
    "难度",
    "建议作答时间",
    "行业",
    "岗位名称",
    "技能分类",
    "技能",
    "知识点",
    "场景",
]

FINAL_SUMMARY_COLUMNS = [
    "问题",
    "第一层",
    "第二层",
    "第三层",
    "技能分类",
    "技能",
    "知识点",
    "难度",
    "行业",
    "岗位名称",
    "场景",
    "一审_是否删除",
    "一审_删除原因",
    "二审_是否删除",
    "二审_删除原因",
    "题目是否修改",
    "是否重新出题",
    "一审_错误大类集合",
    "二审_错误大类集合",
]

FIELD_ALIASES = {
    "问题": ["问题", "题目"],
    "第一层": ["第一层", "参考答案-第一层"],
    "第二层": ["第二层", "参考答案-第二层"],
    "第三层": ["第三层", "参考答案-第三层"],
    "建议作答时间": ["建议作答时间", "建议作答时长"],
    "岗位名称": ["岗位名称", "岗位"],
    "场景": ["场景", "招聘场景"],
}


def get_col(df: pd.DataFrame, target: str) -> pd.Series:
    for col in FIELD_ALIASES.get(target, [target]):
        if col in df.columns:
            return df[col]
    if target in df.columns:
        return df[target]
    return pd.Series([""] * len(df), index=df.index)


def normalize_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for col in columns:
        out[col] = get_col(df, col)
    return out.reset_index(drop=True)


def split_actions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if "合并_建议动作" in df.columns:
        action = df["合并_建议动作"].astype(str).str.strip()
    elif "合并_是否删除" in df.columns:
        delete = df["合并_是否删除"].astype(str).str.strip()
        error_cols = [c for c in df.columns if "错误类型" in c or "错误大类集合" in c]
        error_text = df[error_cols].astype(str).agg(" ".join, axis=1) if error_cols else pd.Series([""] * len(df), index=df.index)
        action = pd.Series("keep", index=df.index)
        action = action.mask((delete == "是") & error_text.str.contains("A|C", regex=True), "rewrite_question")
        action = action.mask((delete == "是") & ~error_text.str.contains("A|C", regex=True), "rewrite_answer")
    else:
        action = pd.Series("keep", index=df.index)

    keep_df = df[action == "keep"].copy()
    rewrite_question_df = df[action == "rewrite_question"].copy()
    rewrite_answer_df = df[action == "rewrite_answer"].copy()
    return keep_df, rewrite_question_df, rewrite_answer_df


def export_summary_workbook(keep_df: pd.DataFrame, rewrite_question_df: pd.DataFrame, rewrite_answer_df: pd.DataFrame, out_path: Path) -> None:
    with pd.ExcelWriter(out_path) as writer:
        normalize_columns(keep_df, FINAL_SUMMARY_COLUMNS).to_excel(writer, sheet_name="可保留题目答案", index=False)
        normalize_columns(rewrite_question_df, FINAL_SUMMARY_COLUMNS).to_excel(writer, sheet_name="需要重新出题", index=False)
        normalize_columns(rewrite_answer_df, FINAL_SUMMARY_COLUMNS).to_excel(writer, sheet_name="保留题干重出答案", index=False)


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
    parser.add_argument("--answer-template", required=False)
    parser.add_argument("--question-template", required=False)
    args = parser.parse_args()

    merged = pd.read_excel(args.merged)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.round == 1:
        keep_df, _, _ = split_actions(merged)

        if "合并_是否删除" in merged.columns:
            r2_df = merged[merged["合并_是否删除"].astype(str).str.strip() == "否"].copy()
        elif "合并_建议动作" in merged.columns:
            r2_df = merged[merged["合并_建议动作"].astype(str).str.strip() == "keep"].copy()
        else:
            r2_df = keep_df.copy()

        out_path = out_dir / "待二轮审核题表.xlsx"
        normalize_columns(r2_df, ROUND1_FIELDS).to_excel(out_path, index=False)
        print(f"round1_no_issue={out_path}")
        return

    keep_df, rewrite_question_df, rewrite_answer_df = split_actions(merged)

    summary_out = out_dir / "题库审核汇总.xlsx"
    export_summary_workbook(keep_df, rewrite_question_df, rewrite_answer_df, summary_out)
    print(f"round{args.round}_summary={summary_out}")

    if args.answer_template and args.question_template:
        ans_out = out_dir / "保留题干重出答案_交付表.xlsx"
        q_out = out_dir / "待重新出题_交付表.xlsx"
        export_from_template(rewrite_answer_df, Path(args.answer_template), ans_out)
        export_from_template(rewrite_question_df, Path(args.question_template), q_out)
        print(f"round{args.round}_rewrite_answer={ans_out}")
        print(f"round{args.round}_rewrite_question={q_out}")


if __name__ == "__main__":
    main()
