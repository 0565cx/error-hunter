#!/usr/bin/env python3
"""Shared helpers for Error Hunter review result merge scripts."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


BASE_COLUMNS = [
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

ROUND2_COLUMNS = BASE_COLUMNS

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

REVIEW_FIELDS = ["是否删除", "错误类型", "删除原因", "疑似与肯定"]


def read_excel(path: Path) -> pd.DataFrame:
    return pd.read_excel(path).fillna("")


def parse_model_file_arg(item: str) -> tuple[str, Path]:
    if "=" not in item:
        raise ValueError(f"Invalid --model-file value: {item}. Expected ModelName=/path/file.xlsx")
    name, path = item.split("=", 1)
    return name.strip(), Path(path.strip())


def get_col(df: pd.DataFrame, target: str) -> pd.Series:
    for col in FIELD_ALIASES.get(target, [target]):
        if col in df.columns:
            return df[col]
    if target in df.columns:
        return df[target]
    return pd.Series([""] * len(df), index=df.index)


def normalize_base_columns(df: pd.DataFrame, columns: list[str] = BASE_COLUMNS) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for col in columns:
        out[col] = get_col(df, col)
    return out.reset_index(drop=True)


def make_match_key(df: pd.DataFrame) -> pd.Series:
    if "question_id" in df.columns:
        return df["question_id"].astype(str).str.strip()
    question = get_col(df, "问题").astype(str).str.strip()
    return question.str.replace(r"\s+", "", regex=True)


def normalize_delete(is_delete: object, confidence: object) -> str:
    """Align with SKILL: 肯定有/疑似有/疑似无 => 删除；肯定无 => 保留."""
    c = str(confidence).strip()
    v = str(is_delete).strip()
    if c in {"肯定有", "疑似有", "疑似无"}:
        return "是"
    if c in {"肯定无"}:
        return "否"
    if v in {"是", "否"}:
        return v
    return "否"


def normalize_review_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().fillna("")
    for col in REVIEW_FIELDS:
        if col not in out.columns:
            out[col] = ""
    out["是否删除"] = [
        normalize_delete(is_delete, confidence)
        for is_delete, confidence in zip(out["是否删除"], out["疑似与肯定"])
    ]
    return out


def add_model_columns(
    merged: pd.DataFrame,
    source: pd.DataFrame,
    model: str,
    delete_round: int | None = None,
    require_delete_round: bool = False,
) -> pd.DataFrame:
    src = normalize_review_df(source).reset_index(drop=True)
    out = merged.copy().reset_index(drop=True)

    if len(src) == len(out):
        aligned = src
    else:
        src = src.copy()
        src["_match_key"] = make_match_key(src)
        out_keys = make_match_key(out)
        lookup = src.drop_duplicates("_match_key").set_index("_match_key")
        aligned = pd.DataFrame(index=out.index)
        for col in REVIEW_FIELDS:
            aligned[col] = out_keys.map(lookup[col]).fillna("")
        aligned = normalize_review_df(aligned)

    for col in REVIEW_FIELDS:
        out[f"{model}_{col}"] = aligned[col].values
    if require_delete_round:
        out[f"{model}_删除轮次"] = [
            str(delete_round or "") if v == "是" else "" for v in aligned["是否删除"]
        ]
    return out


def model_names_from_columns(df: pd.DataFrame) -> list[str]:
    suffix = "_是否删除"
    names = [c[: -len(suffix)] for c in df.columns if c.endswith(suffix)]
    return list(dict.fromkeys(names))


def collect_row_review(row: pd.Series, model_names: list[str]) -> dict[str, object]:
    deletes: list[str] = []
    errors: list[str] = []
    reasons: list[str] = []
    for model in model_names:
        is_delete = normalize_delete(row.get(f"{model}_是否删除", ""), row.get(f"{model}_疑似与肯定", ""))
        if is_delete == "是":
            deletes.append(model)
            error = str(row.get(f"{model}_错误类型", "")).strip()
            reason = str(row.get(f"{model}_删除原因", "")).strip()
            if error:
                errors.append(error)
            if reason:
                reasons.append(f"{model}: {reason}")
    return {
        "is_delete": "是" if deletes else "否",
        "errors": errors,
        "reasons": reasons,
    }


def parse_error_codes(value: object) -> list[str]:
    text = str(value).upper().strip()
    if not text:
        return []
    text = (
        text.replace("，", ",")
        .replace("、", ",")
        .replace("；", ",")
        .replace(";", ",")
        .replace(" ", "")
    )
    return re.findall(r"[ABC]\d*|[ABC]", text)


def error_family_set(errors: list[str]) -> str:
    families = sorted({code[0] for err in errors for code in parse_error_codes(err) if code})
    return "".join(families)


def action_from_errors(errors: list[str], is_delete: str) -> str:
    if is_delete != "是":
        return "keep"
    families = set(error_family_set(errors))
    if "A" in families or "C" in families:
        return "rewrite_question"
    return "rewrite_answer"


def add_merge_decision(df: pd.DataFrame, model_names: list[str]) -> pd.DataFrame:
    out = df.copy()
    decisions = [collect_row_review(row, model_names) for _, row in out.iterrows()]
    out["合并_是否删除"] = [d["is_delete"] for d in decisions]
    out["合并_错误类型"] = ["、".join(d["errors"]) for d in decisions]
    out["合并_删除原因"] = ["；".join(d["reasons"]) for d in decisions]
    out["合并_错误大类集合"] = [error_family_set(d["errors"]) for d in decisions]
    out["合并_建议动作"] = [
        action_from_errors(d["errors"], str(d["is_delete"])) for d in decisions
    ]
    return out


def split_actions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    action = df.get("合并_建议动作", pd.Series(["keep"] * len(df), index=df.index)).astype(str).str.strip()
    return (
        df[action == "keep"].copy(),
        df[action == "rewrite_question"].copy(),
        df[action == "rewrite_answer"].copy(),
    )


def action_counts(df: pd.DataFrame) -> dict[str, int]:
    keep_df, rewrite_question_df, rewrite_answer_df = split_actions(df)
    return {
        "total": len(df),
        "keep": len(keep_df),
        "rewrite_question": len(rewrite_question_df),
        "rewrite_answer": len(rewrite_answer_df),
        "next_round_expected": len(rewrite_question_df) + len(rewrite_answer_df),
    }


def validate_current_count(df: pd.DataFrame, expected_count: int | None, label: str) -> None:
    if expected_count is None:
        return
    actual = len(df)
    if actual != expected_count:
        raise ValueError(
            f"{label} count mismatch: expected {expected_count}, got {actual}. "
            "Do not continue until missing, duplicate, or extra returned questions are resolved."
        )


def first_non_empty(row: pd.Series, columns: list[str]) -> str:
    for col in columns:
        val = str(row.get(col, "")).strip()
        if val:
            return val
    return ""


def final_summary_frame(df: pd.DataFrame, round_num: int) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for col in FINAL_SUMMARY_COLUMNS:
        if col == "一审_是否删除":
            out[col] = df.apply(lambda r: first_non_empty(r, [c for c in df.columns if c.endswith("_是否删除")]), axis=1)
        elif col == "一审_删除原因":
            out[col] = df.apply(lambda r: first_non_empty(r, [c for c in df.columns if c.endswith("_删除原因")]), axis=1)
        elif col == "二审_是否删除":
            out[col] = df["合并_是否删除"] if "合并_是否删除" in df.columns else ""
        elif col == "二审_删除原因":
            out[col] = df["合并_删除原因"] if "合并_删除原因" in df.columns else ""
        elif col == "题目是否修改":
            out[col] = "否"
        elif col == "是否重新出题":
            out[col] = df.get("合并_建议动作", "").map(
                {"rewrite_question": "是", "rewrite_answer": "否", "keep": "否"}
            ) if "合并_建议动作" in df.columns else ""
        elif col == "一审_错误大类集合":
            out[col] = df.apply(
                lambda r: error_family_set(
                    [str(r.get(c, "")) for c in df.columns if c.endswith("_错误类型")]
                ),
                axis=1,
            )
        elif col == "二审_错误大类集合":
            out[col] = df["合并_错误大类集合"] if "合并_错误大类集合" in df.columns else ""
        else:
            out[col] = get_col(df, col)
    return out.reset_index(drop=True)


def export_summary_workbook(merged: pd.DataFrame, out_path: Path, round_num: int) -> None:
    keep_df, rewrite_question_df, rewrite_answer_df = split_actions(merged)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        final_summary_frame(keep_df, round_num).to_excel(writer, sheet_name="可保留题目答案", index=False)
        final_summary_frame(rewrite_question_df, round_num).to_excel(writer, sheet_name="需要重新出题", index=False)
        final_summary_frame(rewrite_answer_df, round_num).to_excel(writer, sheet_name="保留题干重出答案", index=False)


def build_error_stats(merged: pd.DataFrame, out_path: Path) -> None:
    deleted = merged[merged.get("合并_是否删除", "") == "是"].copy()
    family_counter: Counter[str] = Counter()
    subtype_counter: Counter[str] = Counter()
    examples: dict[str, list[dict[str, str]]] = defaultdict(list)

    for idx, row in deleted.iterrows():
        errors = str(row.get("合并_错误类型", ""))
        reason = str(row.get("合并_删除原因", ""))
        question = str(get_col(pd.DataFrame([row]), "问题").iloc[0])
        qid = str(row.get("question_id", f"Q{idx + 1:03d}"))
        for code in parse_error_codes(errors):
            family_counter[code[0]] += 1
            subtype_counter[code] += 1
            if len(examples[code]) < 2:
                examples[code].append({"question_id": qid, "问题": question, "理由": reason})

    family_df = pd.DataFrame(
        [{"错误大类": k, "数量": v} for k, v in sorted(family_counter.items())]
    )
    subtype_df = pd.DataFrame(
        [{"错误子类": k, "数量": v} for k, v in sorted(subtype_counter.items())]
    )
    example_rows = []
    for code, rows in sorted(examples.items()):
        item = {"错误子类": code}
        for i in range(2):
            row = rows[i] if i < len(rows) else {"question_id": "", "问题": "", "理由": ""}
            item[f"例{i + 1}_question_id"] = row["question_id"]
            item[f"例{i + 1}_题目"] = row["问题"]
            item[f"例{i + 1}_理由"] = row["理由"]
        example_rows.append(item)
    examples_df = pd.DataFrame(example_rows)

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        family_df.to_excel(writer, sheet_name="family_counts", index=False)
        subtype_df.to_excel(writer, sheet_name="subtype_counts", index=False)
        examples_df.to_excel(writer, sheet_name="subtype_examples", index=False)
