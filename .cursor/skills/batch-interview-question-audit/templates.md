# Templates

## 1) Review Log CSV Template

File name suggestion: `review_log.csv`

```csv
round,model,batch_id,status,start_time,end_time,duration_sec,questions_total,delete_count,keep_count,error_A_count,error_B_count,error_C_count,notes
1,GPT5.4,R1-B001,done,2026-04-12 10:00:00,2026-04-12 10:08:00,480,40,9,31,3,4,2,
1,Sonnet4.6,R1-B001,running,2026-04-12 10:02:00,,,40,,,,,,waiting for response
```

Status values:

- `pending`
- `running`
- `done`
- `blocked`
- `failed`

## 2) Round Summary Table Template

```markdown
## Round {round} Summary

| Model | Done Batches | Total Batches | Completion | Delete Rate | Main Errors |
|---|---:|---:|---:|---:|---|
| GPT5.5 | 12 | 20 | 60% | 24.5% | A>B>C |
| GPT5.4 | 11 | 20 | 55% | 22.0% | B>A>C |
| Sonnet4.6 | 13 | 20 | 65% | 20.5% | A=C>B |
| Opus4.7 | 10 | 20 | 50% | 26.0% | A>C>B |
| Gemini3.1pro | 9 | 20 | 45% | 21.5% | B>C>A |
```

## 2.2 Round-1 Merged Result Columns (5 Models)

Round-1 merged table should keep base columns and append model columns in this pattern:

Base columns:

- `问题`
- `第一层`
- `第二层`
- `第三层`
- `难度`
- `建议作答时间`
- `行业`
- `岗位名称`
- `技能分类`
- `技能`
- `知识点`
- `场景`

Per-model columns:

- `{模型名}_是否删除`
- `{模型名}_错误类型`
- `{模型名}_删除原因`
- `{模型名}_疑似与肯定`

Round-1 model list:

- `GPT5.5`
- `GPT5.4`
- `Sonnet4.6`
- `Opus4.7`
- `Gemini3.1pro`

## 2.3 Round-2 Merged Result Columns (5 Models)

Round-2 updates the Round-1 merged result table. Each model should append five columns:

- `{模型名}_是否删除`
- `{模型名}_错误类型`
- `{模型名}_删除原因`
- `{模型名}_疑似与肯定`
- `{模型名}_删除轮次`

## 2.4 Round-3+ Merged Result Columns (2 Models + 合并)

For round 3 to N, use two models and append final merge field:

- `GPT5.5_是否删除`
- `GPT5.5_错误类型`
- `GPT5.5_删除原因`
- `GPT5.5_疑似与肯定`
- `Gemini3.1pro_是否删除`
- `Gemini3.1pro_错误类型`
- `Gemini3.1pro_删除原因`
- `Gemini3.1pro_疑似与肯定`
- `合并`（即两个模型“是否删除”的合并结果）

## 2.1 Dashboard Output Rule (Per Round)

Per round, only keep these dashboard files:

- `round{n}_dashboard.html`
- `round{n}_dashboard.xlsx`

Do not keep standalone detailed dashboard files, such as:

- `round{n}_删除错误统计_细分.html`
- `round{n}_删除错误统计_细分.xlsx`
- `round{n}_删除错误统计_细分.md`

Detailed subtype statistics and examples should be embedded in `round{n}_dashboard.html` and `round{n}_dashboard.xlsx`.

## 2.2 Pilot Gate Template (Before Full Run)

Use this table after first 1-2 batches per model:

```markdown
## Pilot Gate (Round {round})

| Model | Pilot Batches | Delete Rate | Peer Median Gap | Rule Understanding | Decision |
|---|---:|---:|---:|---|---|
| GPT5.4 | 2 | 22.5% | +1.2pp | aligned | pass |
| Sonnet4.6 | 2 | 41.0% | +19.7pp | over-strict on B类 | recalibrate |
```

Decision values:

- `pass`: continue all remaining batches
- `recalibrate`: pause and rerun pilot after prompt correction

## 3) Error Statistics Template (with 2 examples each)

```markdown
## Round {round} Deletion Error Stats

- A类错误：{A_count}
- B类错误：{B_count}
- C类错误：{C_count}

### 二级错误类型统计
- A1：{A1_count}
- A2：{A2_count}
- B1：{B1_count}
- B2：{B2_count}
- B3：{B3_count}
- C2：{C2_count}

### 二级错误类型示例（每类2个）
- A1
  - 例1：[{question_id}] {question_brief}；表现：{why}
  - 例2：[{question_id}] {question_brief}；表现：{why}
- A2
  - 例1：[{question_id}] {question_brief}；表现：{why}
  - 例2：[{question_id}] {question_brief}；表现：{why}
- B1
  - 例1：[{question_id}] {question_brief}；表现：{why}
  - 例2：[{question_id}] {question_brief}；表现：{why}
```

## 4) Progress Visualization Template (Mermaid)

```text
## Round {round} Progress
```

```mermaid
xychart-beta
  title "Round {round} model completion"
  x-axis ["GPT5.5","GPT5.4","Sonnet4.6","Opus4.7","Gemini3.1pro"]
  y-axis "Done Batches" 0 --> {max_batches}
  bar [{gpt55_done},{gpt54_done},{sonnet46_done},{opus47_done},{gemini31_done}]
```

```text
## Round {round} Error Distribution
```

```mermaid
pie title "Round {round} delete error mix"
  "A类" : {A_count}
  "B类" : {B_count}
  "C类" : {C_count}
```

## 5) Intervention Alert Template

Use this section whenever any model is `blocked` or `failed`.

```markdown
## Intervention Alerts

- Model: {model}
- Batch: {batch_id}
- Status: {status}
- Root cause: {root_cause}
- Impact: {impact}
- Proposed action: {action}
- Need PM decision: {yes_or_no}
```

For stall/resume cases, append:

```markdown
- Last done batch: {last_done_batch}
- Resume from batch: {resume_from_batch}
- Safe to resume without rerun done batches: {yes_or_no}
```

## 5.1 Quality Drift Alert Template

```markdown
## Quality Drift Alert

- Model: {model}
- Pilot/Delete rate: {rate}
- Peer median gap: {gap_pp}
- Alert type: {too_lenient|too_strict|semantic_drift}
- Evidence (5 keep + 5 delete spot checks): {summary}
- Action: {pause_and_recalibrate|continue}
- Need PM decision: {yes_or_no}
```

## 6) Final Consolidation Template

```markdown
## Final Consolidation

- Keep (题干和答案可直接保留): {keep_count}
- Rewrite Question (A/C类): {rewrite_question_count}
- Rewrite Answer (仅B类): {rewrite_answer_count}
- Pending Manual Decision: {pending_count}
```

## 7) Mandatory Handoff Files (Do Not Re-generate In This Skill)

Round-based output routing:

- Round 1: formal outputs are `审题结果` and `一轮审核结果汇总`; prepare `待二轮审核题表` as the next round input from no-error questions.
- Round 2: output `二轮审核后需要重出的内容` and `可保留题目答案`.
- Round 3 to N: output `X轮审核后需要重出的内容` and `可保留题目答案`; loop regenerated items into the next round until the problematic set is below the manual-check threshold.

### 7.1 Round 1 Outputs

`待二轮审核题表` rule:

- Generate it from `一轮审核结果汇总`.
- Include only questions where all Round-1 models are `否` after `疑似/肯定` normalization.
- Place it under the Round-2 input folder `待二轮审核题表`.
- Keep fields:
  - `问题`
  - `第一层`
  - `第二层`
  - `第三层`
  - `难度`
  - `建议作答时间`
  - `行业`
  - `岗位名称`
  - `技能分类`
  - `技能`
  - `知识点`
  - `场景`

Normalization rule (mandatory):

- `疑似与肯定` in (`肯定有`, `疑似有`, `疑似无`) => `是否删除 = 是`
- `疑似与肯定` = `肯定无` => `是否删除 = 否`

### 7.2 Round 2+ Outputs

Preferred output is one `题库审核汇总.xlsx` workbook with three sheets:

1. `可保留题目答案`:
   - Include items with final action `keep`.
2. `需要重新出题`:
   - Include items with final action `rewrite_question` (A类 or C类).
3. `保留题干重出答案`:
   - Include items with final action `rewrite_answer` (typically only B类).

Recommended columns for the three sheets:

- `问题`
- `第一层`
- `第二层`
- `第三层`
- `技能分类`
- `技能`
- `知识点`
- `难度`
- `行业`
- `岗位名称`
- `场景`
- `一审_是否删除`
- `一审_删除原因`
- `二审_是否删除`
- `二审_删除原因`
- `题目是否修改`
- `是否重新出题`
- `一审_错误大类集合`
- `二审_错误大类集合`

Column-fill rule if a downstream handoff file still requires `JD` or `提示词`:

- Keep `JD` empty.
- Keep `提示词` empty.

Round continuation rule:

- User sends back regenerated questions from downstream team.
- This skill then continues the next review round on returned questions.
