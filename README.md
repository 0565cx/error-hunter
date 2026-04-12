# Error Hunter（AI审题 Skill）

面向“大题量、多模型、多轮次”的 AI 面试题审核流程。  
核心目标：稳定批量审题、可断点续跑、看板可视化、按轮次正确输出。

## 一句话启动

```text
按审题skill开始：先每个模型试跑2批，达标再全量；支持断点续跑。
```

## Skill 位置

- `.cursor/skills/batch-interview-question-audit/`

> 技能名（frontmatter）：`error-hunter`

## 流程规则（重点）

- `Round1`：
  - 先 pilot gate（每模型先审 1-2 批）
  - 通过后再跑剩余批次
  - 仅输出 `待二轮审核题表`
- `Round2+`：
  - 输出两张交付表：`保留题干重出答案`、`待重新出题`
  - `JD` 与 `提示词` 两列保持为空
- 看板产物每轮只保留：
  - `round{n}_dashboard.html`
  - `round{n}_dashboard.xlsx`
- 若卡住：从断点批次继续，不重跑已完成批次

## 仓库内容

- `SKILL.md`：完整执行规则（pilot、断点恢复、质量漂移告警）
- `templates.md`：输出模板与轮次路由规则
- `taxonomy.md`：错误分类与二级错误子类口径
- `command-templates.md`：极简口令 + 长版附录
- `scripts/`：看板导出、轮次产物导出、细分统计脚本

## 推荐使用顺序

1. 复制 `command-templates.md` 里的“极简口令”启动任务  
2. 先看 pilot gate，再决定是否放量  
3. 每轮只看 `dashboard.html/xlsx`  
4. 按轮次规则交付（Round1 不出重出题表，Round2+ 才出）
