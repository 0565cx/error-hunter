#!/usr/bin/env python3
"""Merge Round-X (X>=3) review outputs and export rework workbook."""

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
    normalize_base_columns,
    parse_model_file_arg,
    read_excel,
    validate_current_count,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", required=True, type=int, help="Round number, must be >= 3")
    parser.add_argument("--base", required=True, help="Current round input question table xlsx")
    parser.add_argument(
        "--model-file",
        action="append",
        required=True,
        help="Current round model review file, format: ModelName=/path/to/result.xlsx",
    )
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--merged-name", default=None)
    parser.add_argument("--summary-name", default=None)
    parser.add_argument("--stats-name", default=None)
    parser.add_argument(
        "--expected-current-count",
        type=int,
        default=None,
        help=(
            "Expected current-round input count, usually previous round "
            "需要重新出题 + 保留题干重出答案. Fails if base row count differs."
        ),
    )
    args = parser.parse_args()

    if args.round < 3:
        raise SystemExit("--round must be >= 3 for merge_roundx_results.py")

    base = read_excel(Path(args.base))
    validate_current_count(base, args.expected_current_count, f"Round-{args.round} input")
    merged = normalize_base_columns(base)

    for item in args.model_file:
        model, path = parse_model_file_arg(item)
        merged = add_model_columns(
            merged,
            read_excel(path),
            model,
            delete_round=args.round,
            require_delete_round=True,
        )

    model_names = model_names_from_columns(merged)
    merged = add_merge_decision(merged, model_names)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    merged_name = args.merged_name or f"{args.round}轮审核结果汇总.xlsx"
    summary_name = args.summary_name or f"{args.round}轮题库审核汇总.xlsx"
    stats_name = args.stats_name or f"round{args.round}_error_stats.xlsx"
    merged_path = out_dir / merged_name
    summary_path = out_dir / summary_name
    stats_path = out_dir / stats_name

    merged.to_excel(merged_path, index=False)
    export_summary_workbook(merged, summary_path, round_num=args.round)
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
