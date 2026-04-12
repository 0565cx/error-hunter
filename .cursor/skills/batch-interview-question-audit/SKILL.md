---
name: batch-interview-question-audit
description: Execute multi-round, multi-model batch review for AI interview questions, including 40-question batching, delete/keep decisions, error taxonomy aggregation, round-specific output routing, and per-model progress visualization. Use when the user mentions 审题、批量审题、题库审核、多轮审核、A/B/C类错误、删除原因统计、审核看板、进度可视化、保留题干重出答案、待重新出题.
---

# Batch Interview Question Audit

## Use This Skill When

- User asks to audit a large interview question bank for one or more roles.
- Workflow requires multiple models and multiple rounds.
- User needs per-round statistics on deletion errors.
- User wants visual tracking for each model's progress and output quality.

## Inputs You Must Confirm First

Collect and restate these fields before execution:

1. `industry` and `roles` (single role or role list).
2. Source question file path(s).
3. Current round number and target round range.
4. Model lineup by round:
   - Round 1: `GPT5.4`, `GPT5.4-highfast`, `Sonnet4.6`, `Opus4.5`, `Gemini3pro`.
   - Round 2: same as Round 1 unless user overrides.
   - Round 3~N: default `GPT5.4` + `Sonnet4.6`.
5. Batch size (default `40`).
6. Prompt source:
   - Local prompt files if available.
   - User-provided prompt document link.

If any item is missing, ask concise follow-up questions before running.

## Standard Workflow

### Step 1: Prepare Batches

- Split each role's questions into batches of 40 in stable order.
- Use deterministic batch IDs: `R{round}-B{index:03d}`.
- Keep one master index with fields:
  - `question_id`, `industry`, `role`, `batch_id`, `question`, `answer_l1`, `answer_l2`, `answer_l3`, `difficulty`, `skill_category`, `skill`, `knowledge_point`.

### Step 1.1: Pilot Gate Before Full Run (Quality Calibration)

Before running all batches, run a pilot gate for each model:

- Audit first `1-2` batches only (recommended `2`, i.e. up to 80 questions).
- Compute model delete-rate and compare with peer models and historical expectation.
- Validate rule understanding:
  - For deleted questions: check whether reason aligns with error taxonomy and prompt intent.
  - For kept questions: check whether model can explain why no deletion is needed.
- If model behavior is unstable (too loose or too strict), stop full run for that model and calibrate prompt, then rerun pilot.

Do not start full 20+ batches until pilot gate passes.

### Step 2: Run Round-1 Review (5 Models)

- Run each batch through all models independently.
- Require explicit per-question decision:
  - `is_delete`: `yes` or `no`
  - `confidence`: `肯定有` / `疑似有` / `肯定无` / `疑似无`
  - `error_type`: use second-level subtype first (for example `A1`/`A2`/`B1`/`B2`/`B3`/`C2`), fallback to `A`/`B`/`C` only when subtype is unknown
  - `error_reason`: short Chinese explanation
- Never sample. Review all questions.
- Persist per-batch outputs immediately (one file per model per batch) for crash-safe resume.

### Step 3: Normalize Labels

- Normalize by confidence:
  - `肯定有` or `疑似有` => `is_delete = yes`
  - `肯定无` or `疑似无` => `is_delete = no`
- Aggregate multi-model decisions per question for the round:
  - If any model says `yes`, round result is `delete`.
  - Else round result is `keep`.

### Step 3.1: Progress Checkpoint and Resume (Anti-Stall)

For large runs (20+ batches), enforce checkpointing:

- Update progress log on every batch state change:
  - `pending` -> `running` -> `done` / `blocked` / `failed`
- If a model stalls:
  - Mark current batch `blocked`.
  - Record last completed batch ID and processed question count.
  - Ask/execute "continue from next unfinished batch" instead of restarting whole round.
- Resume rule:
  - Never rerun completed (`done`) batches unless user explicitly asks.
  - Continue from the first non-done batch in order.

### Step 4: Round-2 Re-Review (No-Issue Set)

- Collect questions where all Round-1 models marked `no`.
- Re-run full review on this set with the configured model lineup.
- Apply same normalization and aggregation rules.

### Step 5: Round-Specific Output Routing (Do Not Re-generate Here)

This skill does **not** execute "re-generate questions/answers".

- Round 1 output:
  - Export only `no_issue_for_round2` (第一轮无错题，进入第二轮审核).
  - Do **not** export re-generation handoff files.
- Round 2 and later output:
  - Split reviewed problematic items into two output sets only:
    - `rewrite_answer`: 题干保留，只需要重新出答案（通常是仅 `B` 类错误）。
    - `rewrite_question`: 题目和答案都需要重出（出现 `A` 或 `C` 类错误）。
  - Hand over both outputs to user for downstream re-generation by another team.

### Step 6: Human Final Check

- Human review checklist:
  - Is wording fluent and natural?
  - Any phrase unsuitable for interview context?
  - Any punctuation/symbols hard for TTS broadcast?
- Mark final action: `keep`, `rewrite_question`, `rewrite_answer`.

### Step 7: Next-Round Handover Protocol

- After user provides newly regenerated questions, treat them as next-round input.
- Continue round workflow (batching, multi-model review, stats, dashboard) on the new set.

## Required Outputs Per Round

For every round, output baseline artifacts:

1. **Merged review table** (all model columns + merged decision).
2. **Deletion error statistics**:
   - Count by top-level category (`A/B/C`) and second-level subtype (`A1/A2/B1/B2/B3...`).
   - For each subtype, provide exactly 2 representative examples.
3. **Progress + quality dashboard**:
   - Per-model, per-batch status.
   - Completion ratio and ETA hint.
   - Delete rate and main error types.
   - Include detailed subtype stats and subtype examples inside dashboard.
   - Output format is only `dashboard.html` and `dashboard.xlsx`.
   - Do **not** output standalone detailed-dashboard files (for example `*_删除错误统计_细分.html/.xlsx/.md`).
Round-specific routing artifacts:

- **Round 1 mandatory**:
  - 待二轮审核题表（all models marked `no` after normalization）
- **Round 2+ mandatory**:
  - 题干保留重出答案表（output based on template #1）
  - 待重新出题表（output based on template #2）

Use templates in [templates.md](templates.md) and taxonomy in [taxonomy.md](taxonomy.md).

## Mandatory Output Templates By Round

Round 1:

1. 待二轮审核题表（字段按 `templates.md` 定义）

Round 2+:

1. `/Users/risei/Desktop/北森-测评产品经理/AI面试官/专业能力/6月迭代/保留题干重出答案的知识点表格模版.xlsx`
2. `/Users/risei/Desktop/北森-测评产品经理/AI面试官/专业能力/6月迭代/待重新出题的知识点表格模版.xlsx`

Do not invent new columns unless user explicitly requests.

## Visualization Rules

- Always provide both:
  - `dashboard.html`
  - `dashboard.xlsx`
- Detailed subtype stats should be embedded in dashboard content, not separate dashboard files.
- Minimum chart set per round:
  1. Model completion status chart.
  2. Error category distribution chart.
- If live status is requested, refresh dashboard after each finished batch.

## Logging Contract (Mandatory)

Track every model-batch execution in a log file with fields:

- `round`, `model`, `batch_id`, `status`, `start_time`, `end_time`, `duration_sec`
- `questions_total`, `delete_count`, `keep_count`
- `error_A_count`, `error_B_count`, `error_C_count`
- `notes`

`status` must be one of: `pending`, `running`, `done`, `blocked`, `failed`.

If review execution stalls, include a `blocked` row with root-cause notes.

## Stall Management SLA

- Heartbeat interval: update progress at least every 1 batch completion.
- Stall trigger: no batch state update for >= 10 minutes during active run.
- On stall trigger, produce:
  1. `current_status_summary` (done/running/pending/blocked counts),
  2. `last_done_batch_by_model`,
  3. `resume_plan` (exact next batch ID per model).
- Resume action must be idempotent: no duplicate write to already finished batch result files.

## Quality Drift Guardrails

Use both absolute and relative checks during pilot and during long runs:

- Absolute delete-rate alert:
  - `< 5%` => possibly too lenient
  - `> 45%` => possibly over-strict
- Relative drift alert:
  - model delete-rate deviates by `> 15 percentage points` from peer median.
- Semantic drift alert:
  - repeated deletion reasons that do not map to taxonomy/prompt rules.

If any alert fires:

1. Pause that model's remaining batches.
2. Show 5 kept + 5 deleted spot examples with model rationale.
3. Calibrate prompt and rerun pilot batches for that model.
4. Resume only after alignment is confirmed.

## Error Handling Playbook

- If a model output is malformed:
  - retry once with stricter output schema.
  - if still invalid, mark `failed`, continue with other models, and surface risk.
- If one model is delayed:
  - keep round running with other models.
  - dashboard must highlight delayed model in `blocked/running`.
- If prompt link cannot be directly read:
  - ask user to provide prompt text or local file path, then proceed.

## Response Format To User

When reporting progress, use this order:

1. Current round summary (`done/running/pending/blocked`).
2. Top risks/blockers (if any).
3. Deletion error counts by category.
4. Deletion error counts by subtype.
5. Two examples per subtype.
6. Next action and whether user intervention is needed.

When stalled or quality-drifted, append:

7. `resume_from_batch` per model.
8. `pilot_recheck_required` (`yes/no`) per model.

## Optional Automation

- Use `scripts/generate_dashboard.py` to build a markdown dashboard from log CSV.
- Input CSV format is documented in [templates.md](templates.md).
