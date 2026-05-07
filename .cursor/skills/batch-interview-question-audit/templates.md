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
| GPT5.4 | 12 | 20 | 60% | 24.5% | A>B>C |
| GPT5.4-highfast | 11 | 20 | 55% | 22.0% | B>A>C |
| Sonnet4.6 | 13 | 20 | 65% | 20.5% | A=C>B |
| Opus4.5 | 10 | 20 | 50% | 26.0% | A>C>B |
| Gemini3pro | 9 | 20 | 45% | 21.5% | B>C>A |
```

## 2.2 Round-1 Merged Result Columns (5 Models)

Round-1 merged table should keep base columns and append model columns in this pattern:

Base columns:

- `问题`
- `参考答案-第一层`
- `参考答案-第二层`
- `参考答案-第三层`
- `难度`
- `行业`
- `岗位名称`
- `技能`
- `技能分类`
- `知识点`

Per-model columns:

- `{模型名}_是否删除`
- `{模型名}_错误类型`
- `{模型名}_删除原因`
- `{模型名}_疑似与肯定`

Round-1 model list:

- `GPT5.4highfast`
- `GPT5.4`
- `Sonnet4.6`
- `Opus4.5`
- `Gemini3pro`

## 2.3 Round-2 Merged Result Columns (5 Models)

Round-2 uses same output pattern as Round-1 (5 models, same four per-model columns).

## 2.4 Round-3+ Merged Result Columns (2 Models + 合并)

For round 3 to N, use two models and append final merge field:

- `GPT5.4_是否删除`
- `GPT5.4_错误类型`
- `GPT5.4_删除原因`
- `GPT5.4_疑似与肯定`
- `Sonnet4.6_是否删除`
- `Sonnet4.6_错误类型`
- `Sonnet4.6_删除原因`
- `Sonnet4.6_疑似与肯定`
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
  x-axis ["GPT5.4","GPT5.4-highfast","Sonnet4.6","Opus4.5","Gemini3pro"]
  y-axis "Done Batches" 0 --> {max_batches}
  bar [{gpt54_done},{gpt54_highfast_done},{sonnet46_done},{opus45_done},{gemini_done}]
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

- Round 1: output `待二轮审核题表` only.
- Round 2 and later: output two handoff files for downstream re-generation.

### 7.1 Round 1 Output (No re-generation tables)

`待二轮审核题表` rule:

- Include only questions where all models are `否` after `疑似/肯定` normalization.
- Keep fields:
  - `问题`
  - `参考答案-第一层`
  - `参考答案-第二层`
  - `参考答案-第三层`
  - `难度`
  - `建议作答时间`
  - `行业`
  - `岗位名称`
  - `技能分类`
  - `技能`
  - `知识点`

Normalization rule (mandatory):

- `疑似与肯定` in (`肯定有`, `疑似有`) => `是否删除 = 是`
- `疑似与肯定` in (`肯定无`, `疑似无`) => `是否删除 = 否`

### 7.2 Round 2+ Outputs

1. `题干保留，重出答案`:
   - Template path: `/Users/risei/Desktop/北森-测评产品经理/AI面试官/专业能力/6月迭代/保留题干重出答案的知识点表格模版.xlsx`
   - Rule: include items with final action `rewrite_answer` (typically only B类).
2. `题目和答案都重出`:
   - Template path: `/Users/risei/Desktop/北森-测评产品经理/AI面试官/专业能力/6月迭代/待重新出题的知识点表格模版.xlsx`
   - Rule: include items with final action `rewrite_question` (A类 or C类).

Column-fill rule for both handoff files:

- Keep `JD` empty.
- Keep `提示词` empty.

Round continuation rule:

- User sends back regenerated questions from downstream team.
- This skill then continues the next review round on returned questions.
