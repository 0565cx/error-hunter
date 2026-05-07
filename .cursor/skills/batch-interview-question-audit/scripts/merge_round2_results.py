#!/usr/bin/env python3
"""Merge Round-2 review outputs into Round-1 summary and export rework workbook."""

from __future__ import annotations

import argparse
from pathlib import Path

from review_merge_utils import (
    add_merge_decision,
    add_model_columns,
    action_counts,
    build_error_stats,
    export_summary_workbook,
    model_names_from_columns,
    parse_model_file_arg,
    read_excel,
    validate_current_count,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round1-merged", required=True, help="Round-1 merged result xlsx")
    parser.add_argument(
        "--model-file",
        action="append",
        required=True,
        help="Round-2 model review file, format: ModelName=/path/to/result.xlsx",
    )
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--merged-name", default="二轮审核结果汇总.xlsx")
    parser.add_argument("--summary-name", default=None)
    parser.add_argument("--stats-name", default="round2_error_stats.xlsx")
    parser.add_argument(
        "--expected-current-count",
        type=int,
        default=None,
        help="Expected full question-bank count for this round; fails if merged row count differs.",
    )
    args = parser.parse_args()

    merged = read_excel(Path(args.round1_merged))
    validate_current_count(merged, args.expected_current_count, "Round-2 input")

    for item in args.model_file:
        model, path = parse_model_file_arg(item)
        merged = add_model_columns(
            merged,
            read_excel(path),
            model,
            delete_round=2,
            require_delete_round=True,
        )

    model_names = model_names_from_columns(merged)
    merged = add_merge_decision(merged, model_names)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_name = args.summary_name or "2轮题库审核汇总.xlsx"
    merged_path = out_dir / args.merged_name
    summary_path = out_dir / summary_name
    stats_path = out_dir / args.stats_name

    merged.to_excel(merged_path, index=False)
    export_summary_workbook(merged, summary_path, round_num=2)
    build_error_stats(merged, stats_path)
    counts = action_counts(merged)

    print(f"merged={merged_path}")
    print(f"summary={summary_path}")
    print(f"error_stats={stats_path}")
    print(
        "count_check="
        f"total:{counts['total']},keep:{counts['keep']},"
        f"rewrite_question:{counts['rewrite_question']},"
        f"rewrite_answer:{counts['rewrite_answer']},"
        f"next_round_expected:{counts['next_round_expected']}"
    )


if __name__ == "__main__":
    main()
