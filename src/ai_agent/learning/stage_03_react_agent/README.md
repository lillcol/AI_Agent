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
- 用户输入一个数学表达式/数学题
- Agent 循环调用：
  - LLM：决定下一步是调用工具还是给出最终答案
  - Tool：调用 `calculator`（安全算术求值）
  - Observation：把工具结果回填给 LLM
- 日志：每一步会记录到 `logs/app.log`（便于公众号式逐步讲解）

运行方式（推荐直接运行）：

```bash
python src/ai_agent/learning/stage_03_react_agent/react_loop_demo.py "3的5次方加10除以2再减去8"
```

也可以不传参数，进入交互输入：

```bash
python src/ai_agent/learning/stage_03_react_agent/react_loop_demo.py
```

## 调用过程详细示意图（Thought -> Action -> Observation -> Final）

这个 demo 的循环每一轮都会完成同样的结构：
1) Thought：让 LLM 给出下一步（需要工具还是可以结束）
2) Action：如果需要计算，给出 tool 名称与 arguments
3) Observation：执行工具得到结果，再喂回 LLM
4) Repeat / Final：直到 LLM 返回 `type=final`

### 端到端单步示意（Single step）

```text
CN:
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

EN:
┌────────────────────────┐
│  User question         │
└──────────┬─────────────┘
           │ step prompt
           v
┌────────────────────────┐
│  LLM (ReAct)           │
│  returns STRICT JSON   │
│  type=action/final    │
└──────────┬─────────────┘
           │ if action
           v
┌────────────────────────┐
│  ToolRegistry          │
│  executes tool         │
└──────────┬─────────────┘
           │ tool output JSON
           v
┌────────────────────────┐
│  Observation (history)│
└──────────┬─────────────┘
           │ next step
           v
  (repeat until final)
```

### 典型执行轨迹示意（Example trace）

以问题：`3^5 + 10/2 - 8` 为例（仅示意 JSON 协议结构）：

```text
Step 1:
LLM -> {"type":"action","thought":"need calculator","tool":"calculator",
        "arguments":{"expression":"3**5+10/2-8"}}

Tool -> {"result": 243.0}

Step 2:
LLM -> {"type":"final","thought":"done","answer":"243"}
```

你可以在控制台/日志里看到对应的：
- `Step i | LLM raw`
- `Step i | Action: tool=...`
- `Step i | Observation (truncated)`
- 最终 `final_answer`
