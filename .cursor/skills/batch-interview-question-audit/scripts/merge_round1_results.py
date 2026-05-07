#!/usr/bin/env python3
"""Merge Round-1 model review outputs and export Round-2 input."""

from __future__ import annotations

import argparse
from pathlib import Path

from review_merge_utils import (
    ROUND2_COLUMNS,
    add_merge_decision,
    add_model_columns,
    build_error_stats,
    model_names_from_columns,
    normalize_base_columns,
    parse_model_file_arg,
    read_excel,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Original question table xlsx")
    parser.add_argument(
        "--model-file",
        action="append",
        required=True,
        help="Model review file, format: ModelName=/path/to/result.xlsx",
    )
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--merged-name", default="一轮审核结果汇总.xlsx")
    parser.add_argument("--round2-name", default="待二轮审核题表.xlsx")
    parser.add_argument("--stats-name", default="round1_error_stats.xlsx")
    args = parser.parse_args()

    base = read_excel(Path(args.base))
    merged = normalize_base_columns(base)

    for item in args.model_file:
        model, path = parse_model_file_arg(item)
        merged = add_model_columns(merged, read_excel(path), model)

    model_names = model_names_from_columns(merged)
    merged = add_merge_decision(merged, model_names)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    merged_path = out_dir / args.merged_name
    round2_path = out_dir / args.round2_name
    stats_path = out_dir / args.stats_name

    merged.to_excel(merged_path, index=False)
    round2_df = merged[merged["合并_是否删除"].astype(str).str.strip() == "否"].copy()
    round2_df[ROUND2_COLUMNS].to_excel(round2_path, index=False)
    build_error_stats(merged, stats_path)

    print(f"merged={merged_path}")
    print(f"round2_input={round2_path}")
    print(f"error_stats={stats_path}")


if __name__ == "__main__":
    main()
