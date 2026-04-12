# Error Taxonomy (A/B/C)

Use this unified taxonomy across all rounds and models.

## A类错误（题干质量问题，建议重出题）

判定特征（满足任一即可）：

- 题目逻辑错误、歧义严重或无法作答。
- 题干与岗位/知识点不匹配。
- 题目明显不符合面试场景（过度主观、无可评估标准）。
- 题干表述严重不通顺或存在明显事实性错误。

输出建议：

- `final_action = rewrite_question`

## B类错误（答案质量问题，题干可保留）

判定特征（满足任一即可）：

- 参考答案与题干不对应或关键点缺失。
- 多层答案之间冲突、重复、层级混乱。
- 答案可用性差（过泛、不可评分、缺少可观察行为点）。

输出建议：

- `final_action = rewrite_answer`

## C类错误（合规/表达/播报风险，通常建议重出题）

判定特征（满足任一即可）：

- 不适合面试语境（歧视、冒犯、违法违规导向等）。
- 存在难以语音播报的异常符号、格式污染、乱码。
- 对候选人产生明显误导或不公平评价风险。

输出建议：

- `final_action = rewrite_question`

## none（无错误）

判定特征：

- 题干、答案、面试场景适配均正常，无删除必要。

输出建议：

- `final_action = keep`

## 多模型合并规则

- 任何模型标记 `is_delete = yes`，则该题在当前轮次合并后视为 `delete`。
- 若有多个错误类型，按 `A/C` 优先于 `B` 给最终动作建议：
  - 出现 `A` 或 `C` => `rewrite_question`
  - 仅出现 `B` => `rewrite_answer`

## 每轮统计口径

- 统计对象：当前轮次被判定删除的题目。
- 统计维度：
  - `A_count`, `B_count`, `C_count`
  - `A_examples`, `B_examples`, `C_examples`（每类固定 2 例）
- 示例应包含：
  - `question_id`
  - 问题摘要（1 句）
  - 错误表现描述（1 句）
