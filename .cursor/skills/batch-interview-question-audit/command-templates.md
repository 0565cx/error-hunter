# 全流程口令模板（极简优先）

优先用下面 6 条短口令。  
长版放在文末附录，只有需要时再用。

---

## A. 极简口令（默认用这个）

### 1) 启动（带试跑）

```text
按审题skill开始：先每个模型试跑2批，达标再全量；支持断点续跑。
```

### 2) 只看试跑结果

```text
先停全量，只给我pilot结果：各模型删题率、偏差、结论(pass/recalibrate)。
```

### 3) 继续跑

```text
通过的模型继续剩余批次；不要重跑done批次；每批更新进度。
```

### 4) 卡住恢复

```text
先报进度和断点（last_done/resume_from），再从未完成批次继续。
```

### 5) Round1 收尾

```text
Round1只输出：待二轮审核题表 + dashboard.html/xlsx。
```

### 6) Round2+ 收尾

```text
输出：两张重出题交付表 + dashboard.html/xlsx；JD和提示词列留空。
```

---

## B. 长版附录（需要精细控制时再用）

### B1) 启动口令（完整版）

```text
按 batch-interview-question-audit 流程开始执行本次审题任务。
要求：
1) 先执行 pilot gate（每个模型先审2个批次）；
2) pilot 通过后再继续剩余批次；
3) 严格按轮次输出规则：
   - Round1 只输出待二轮审核题表；
   - Round2+ 才输出两张重出题交付表；
4) 每轮看板只保留 round{n}_dashboard.html 和 round{n}_dashboard.xlsx；
5) 交付表里 JD、提示词两列保持为空。
请先复述你将执行的步骤和本轮输入/输出路径，再开始。
```

### B2) Round1 启动口令（完整版）

```text
开始 Round1 审核，按40题分批，模型用 GPT5.4、GPT5.4-highfast、Sonnet4.6、Opus4.5、Gemini3pro。
先跑 pilot gate（每个模型前2批），输出 pilot 结果（删题率、与同组中位数偏差、规则理解判断）。
pilot 通过后继续后续批次。
Round1 结束只输出：
1) round1_多模型审核汇总.xlsx
2) 待二轮审核题表.xlsx
3) round1_dashboard.html / round1_dashboard.xlsx
不要输出重出题交付表。
```

### B3) Pilot Gate 复核口令（完整版）

```text
先暂停全量审核，只看 pilot gate 结果。
请逐模型给我：
1) pilot 删题率；
2) 与同组中位数偏差（pp）；
3) 规则理解是否准确（举3个删除样例+2个保留样例）；
4) 结论：pass / recalibrate。
未通过模型不要继续后续批次。
```

### B4) 卡住恢复口令（完整版）

```text
当前疑似卡住，请先不要重跑整轮。
先输出恢复信息：
1) 各模型 done/running/pending/blocked 批次数；
2) 各模型 last_done_batch；
3) 各模型 resume_from_batch；
4) 是否可无重复继续（yes/no）。
然后按 resume_from_batch 继续执行，只跑未完成批次。
```

### B5) Round2+ 口令（完整版）

```text
开始 Round2（或更高轮），先pilot gate再全量。
本轮结束输出：
1) round{n}_多模型审核汇总.xlsx
2) 保留题干重出答案_交付表.xlsx
3) 待重新出题_交付表.xlsx
4) round{n}_dashboard.html / round{n}_dashboard.xlsx
注意：交付表 JD、提示词列留空。
```

### B6) 收尾汇总口令（完整版）

```text
请输出本次项目最终汇总：
1) 每轮题量变化（输入、保留、删除、回流）；
2) 每轮各模型删题率对比；
3) 每轮二级错误类型 Top5；
4) 最终待重出答案题量、待重出题目题量；
5) 剩余风险和建议人工复核点。
同时给出所有关键产物文件路径清单。
```
