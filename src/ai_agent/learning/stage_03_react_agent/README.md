# Stage 03 - ReAct Agent

目标：实现最小思考-行动-观察循环。

建议关注：

- 状态机与循环控制
- 最大步数和终止条件
- 可观测日志设计

## ReAct 入门示例：计算器极简闭环

示例文件：
- `src/ai_agent/learning/stage_03_react_agent/react_loop_demo.py`

示例功能：
- 用户输入一个数学表达式/数学题（命令行参数或交互输入）。
- 初始化运行上下文：
  - 读取 DeepSeek 配置（`base_url` / `api_key`）。
  - 创建 `DeepSeekClient` 与 `CalculatorReActAgent`。
  - 注册 `calculator` 工具到 `ToolRegistry`（保证 demo 可独立运行）。
- Agent 循环执行（最多 `max_steps`）：
  - 构建 step prompt：`system_instructions` + 用户问题 + 历史执行轨迹（`Execution history so far`）。
  - 调用 LLM 获取严格 JSON（`action` 或 `final`）。
  - 解析 JSON 到结构化字段（`type/thought/tool/arguments/answer`）。
  - 若 `type=action`：执行 `calculator`，得到 `observation`，写回历史继续下一轮。
  - 若 `type=final`：结束循环并输出最终答案。
- 状态与可观测性：
  - 记录每一轮的 `THOUGHT`、`ACTION`、`OBSERVATION`、`Parsed type`。
  - 记录并累计 token 使用：`prompt_tokens` / `completion_tokens` / `total_tokens`。
  - 输出 `observations` 的完整内容与统计信息（条目数、字符总量、最新条目长度）。
- 最终输出：
  - 控制台打印 `final_answer`。
  - 控制台打印 token 汇总（calls / prompt / completion / total）。
  - 详细过程落盘到 `logs/app.log`，便于复盘每一步决策与成本。

运行方式（推荐直接运行）：

```bash
python src/ai_agent/learning/stage_03_react_agent/react_loop_demo.py "四加五然后除以 2 再加上 2 的平方最后除以 3"
```

也可以不传参数，进入交互输入：

```bash
python src/ai_agent/learning/stage_03_react_agent/react_loop_demo.py
```

## 真实调用日志示例（Thought -> Action -> Observation -> Token）

下面是一次真实运行日志，输入问题为：`四加五然后除以 2 再加上 2 的平方最后除以 3`。

```text
2026-04-08 16:50:57 | INFO | react_agent | === ReAct Run Start ===
2026-04-08 16:50:57 | INFO | react_agent | Question: 四加五然后除以 2  再加上 2 的平方最后除以 3
2026-04-08 16:50:57 | INFO | react_agent | Max steps: 6
2026-04-08 16:50:57 | INFO | react_agent | --- Step 1/6 ---
2026-04-08 16:50:59 | INFO | react_agent | Step 1 | THOUGHT: 先计算四加五
2026-04-08 16:50:59 | INFO | react_agent | Step 1 | ACTION: tool=calculator args={"expression": "4 + 5"}
2026-04-08 16:50:59 | INFO | react_agent | Step 1 | OBSERVATION: {"result": 9.0}
2026-04-08 16:50:59 | INFO | react_agent | Step 1 | Token usage: prompt=208 completion=27 total=235
2026-04-08 16:50:59 | INFO | react_agent | --- Step 2/6 ---
2026-04-08 16:51:01 | INFO | react_agent | Step 2 | THOUGHT: Divide previous result by 2
2026-04-08 16:51:01 | INFO | react_agent | Step 2 | ACTION: tool=calculator args={"expression": "9 / 2"}
2026-04-08 16:51:01 | INFO | react_agent | Step 2 | OBSERVATION: {"result": 4.5}
2026-04-08 16:51:01 | INFO | react_agent | Step 2 | Token usage: prompt=243 completion=28 total=271
2026-04-08 16:51:04 | INFO | react_agent | Step 3 | THOUGHT: Calculate 2 squared
2026-04-08 16:51:04 | INFO | react_agent | Step 3 | ACTION: tool=calculator args={"expression": "2 ^ 2"}
2026-04-08 16:51:04 | INFO | react_agent | Step 3 | OBSERVATION: {"result": 4.0}
2026-04-08 16:51:06 | INFO | react_agent | Step 4 | THOUGHT: Add 4.5 and 4
2026-04-08 16:51:06 | INFO | react_agent | Step 4 | ACTION: tool=calculator args={"expression": "4.5 + 4"}
2026-04-08 16:51:06 | INFO | react_agent | Step 4 | OBSERVATION: {"result": 8.5}
2026-04-08 16:51:08 | INFO | react_agent | Step 5 | THOUGHT: Divide the sum by 3
2026-04-08 16:51:08 | INFO | react_agent | Step 5 | ACTION: tool=calculator args={"expression": "8.5 / 3"}
2026-04-08 16:51:08 | INFO | react_agent | Step 5 | OBSERVATION: {"result": 2.8333333333333335}
2026-04-08 16:51:10 | INFO | react_agent | Step 6 | THOUGHT: All calculations are complete.
2026-04-08 16:51:10 | INFO | react_agent | Step 6 | FINAL ANSWER: 2.8333333333333335
2026-04-08 16:51:10 | INFO | react_agent | Token summary | calls=6 prompt=1734 completion=167 total=1901
2026-04-08 16:51:10 | INFO | react_agent | === ReAct Run End ===
2.8333333333333335
[Token Usage] calls=6, prompt=1734, completion=167, total=1901
```

## System Prompt 设计逻辑（核心）

`react_loop_demo.py` 中的 `system_instructions` 是这个 Stage 的核心控制面。目标不是让模型“更会聊”，而是让执行过程可控、可解析、可复盘。

### 原始提示词（与代码一致）

```text
You are a ReAct-style agent.
You must output STRICT JSON ONLY.

Decide one step at a time:
1) If you need calculation, return:
{ "type":"action","thought":"<short note>","tool":"calculator","arguments":{"expression":"<arithmetic expression>"} }

2) If you can answer, return:
{ "type":"final","thought":"<short note>","answer":"<final answer text>" }

Rules:
- calculator.expression must be a simple arithmetic expression.
- Do not repeat an action that was already executed successfully.
- Continue from the latest computed result whenever possible.
- If a previous step already included a sub-expression, do not recalculate it separately.
- Do not output any additional text.
```

### 对照解释（Prompt -> 目的）

- `You must output STRICT JSON ONLY.`
  - 目的：强制协议化输出，保证程序可解析，减少格式漂移导致的失败。
- `type=action` / `type=final` 双分支模板
  - 目的：把流程做成显式状态机，代码分支清晰，不依赖语义猜测。
- `thought:"<short note>"`
  - 目的：保留最小决策可观测性，便于日志排查，同时避免长文本占用 token。
- `calculator.expression must be a simple arithmetic expression.`
  - 目的：规范工具输入格式，降低工具执行歧义。
- `Do not repeat an action that was already executed successfully.`
  - 目的：抑制重复动作，避免同一步骤反复调用。
- `Continue from the latest computed result whenever possible.`
  - 目的：引导基于最新结果推进链路，减少回溯重算。
- `If a previous step already included a sub-expression, do not recalculate it separately.`
  - 目的：避免对子表达式拆分后重复求值，降低无效步数和 token 消耗。
- `Do not output any additional text.`
  - 目的：禁止 JSON 外文本污染，确保解析稳定与执行确定性。

## 调用过程详细示意图（Thought -> Action -> Observation -> Final）

这个 demo 的循环每一轮都会完成同样的结构：
1) Thought：让 LLM 给出下一步（需要工具还是可以结束）
2) Action：如果需要计算，给出 tool 名称与 arguments
3) Observation：执行工具得到结果，再喂回 LLM
4) Repeat / Final：直到 LLM 返回 `type=final`

### 端到端单步示意（Single step）

```text
┌────────────────────────┐
│  User question         │
└──────────┬─────────────┘
           │ Step prompt
           v
┌────────────────────────┐
│  LLM (ReAct)            │
│  returns STRICT JSON   │
│  type=action/final     │
└──────────┬─────────────┘
           │ if action
           v
┌────────────────────────┐
│  ToolRegistry           │
│  execute tool_name      │
└──────────┬─────────────┘
           │ tool output JSON
           v
┌────────────────────────┐
│  Observation           │
│  appended to history  │
└──────────┬─────────────┘
           │ next step
           v
  (repeat until final)

```