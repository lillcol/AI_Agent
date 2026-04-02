# Stage 02 - Tools and Function Calling

目标：建立工具协议、注册与执行的基本机制。

建议关注：

- 工具输入输出 schema
- 工具注册中心
- Function Calling 到工具执行的映射

## 中文版本（入门导读）

Stage 02 你要做的是实现一个经典、框架无关的 **Function Calling 学习闭环**：

1. **工具定义**：为工具准备输入/输出的 JSON Schema（让模型能按格式填参数）
2. **工具注册中心**：单例 registry（register / get / list / execute）
3. **LLM Planner 协议**：让 LLM 返回严格 JSON，告诉系统“调用哪个工具 + 参数是什么”
4. **工具执行**：解析 planner JSON -> 调用对应工具 -> 得到工具结果 JSON
5. **最终回答**：把工具结果再发给 LLM，让它输出简洁的最终文本

注意：这个 demo **不改动**已有的 DeepSeek native LLM 客户端。  
它只依赖现成的文本接口：`.chat(user_query: str) -> str`

### 会遇到的关键抽象

#### 1) Tool 接口（工具基类）

所有工具遵循统一合约：

- 静态元信息：
  - `name`：planner 选择工具用的名字
  - `description`：解释工具做什么
- 输入/输出 Schema：
  - `input_schema`：工具参数结构（会被放进 planner 的 arguments）
  - `output_schema`：工具返回值结构（便于后续理解/提示）
- 执行：
  - `run(args: dict) -> JSON-serializable result`

### 流程图 1：定义一个工具（Tool）的流程

```text
┌───────────────────────────────┐
│ Pick a capability to build    │
│ e.g. calculator/time/weather  │
└───────────────┬───────────────┘
                │
                v
┌───────────────────────────────┐
│ Define tool class:            │
│ class XxxTool(Tool)           │
│ 1) name / description          │
│ 2) input_schema / output_schema│
│ 3) implement run(args)         │
└───────────────┬───────────────┘
                │
                v
┌───────────────────────────────┐
│ Register into singleton       │
│ ToolRegistry                  │
│ registry.register(XxxTool())   │
└───────────────┬───────────────┘
                │
                v
┌───────────────────────────────┐
│ Use in demo / agent           │
│ - planner reads schemas       │
│ - registry.execute(...) runs  │
└───────────────────────────────┘
```

#### 2) JSON Schema（为什么需要它）

因为 planner 是 LLM，它需要一个“形状契约（shape contract）”：
例如参数应当长这样：`{"expression": "3**5"}`

本 demo 使用一个很小的 JSON Schema 子集（更容易理解）：

- 工具输入输出都是 `object`
- `additionalProperties: false`
- 显式 `required` 字段

#### 3) Tool Registry（单例注册中心）

典型调用流程：

1. Demo 注册工具：`registry.register(CalculatorTool())` 等
2. Orchestrator 获取工具定义：`registry.list_tools()`
3. Orchestrator 执行工具：`registry.execute(tool_name, arguments)`

工具执行结果会被包装成：

- `ToolExecutionResult(tool_name=..., output=...)`

#### 4) Planner 协议（LLM Function Calling 教学版）

为保持 demo 框架无关，本项目实现了一个 **严格 planner JSON 协议**。

planner 返回 STRICT JSON ONLY（不输出 markdown/额外文本）。

允许的返回：

1. Tool call：

```json
{
  "type": "tool_call",
  "tool_name": "calculator",
  "arguments": { "...": "..." }
}
```

1. Final：

```json
{
  "type": "final",
  "answer": "..."
}
```

解析规则：代码会从 LLM 输出中提取 **第一个 JSON 对象**（假设模型输出“基本是 JSON”）。

#### 5) 全流程调用链（Plan -> Execute -> Answer）

给定用户问题：

1. **Plan**
  - LLM -> planner JSON（tool_call 或 final）
2. **Execute**
  - 如果是 `tool_call`：
    - registry 按 `tool_name` 执行工具
    - tool 接收 `arguments`（dict）
3. **Answer**
  - LLM -> 根据 tool output JSON 生成简洁最终答案

### 流程图 2：调用工具的流程（Function Calling 执行链路）

```text
┌───────────────────────────────┐
│ User question (natural lang)  │
└───────────────┬───────────────┘
                │
                v
┌───────────────────────────────┐
│ LLM Planner (call #1)         │
│ - reads tool definitions      │
│ - returns STRICT JSON:        │
│   tool_call / final            │
└───────────────┬───────────────┘
                │ tool_call
                v
┌───────────────────────────────┐
│ ToolRegistry.execute(...)      │
│ - find tool by tool_name      │
│ - pass arguments into run()   │
│ - get tool output JSON        │
└───────────────┬───────────────┘
                │
                v
┌───────────────────────────────┐
│ LLM Answer (call #2)          │
│ - input: tool output JSON     │
│ - output: concise final text  │
└───────────────────────────────┘
```

### 可运行示例

运行 demo：

```bash
PYTHONPATH=src python src/ai_agent/learning/stage_02_tools_function_calling/function_calling_demo.py "3的5次方等于多少？"
```

试试其他问题：

- calculator：`2*(10+3)`
- time：`现在几点？`
- weather：`广州天气怎么样？`（需要 `services.amap_weather.api_key`）

### 所需配置（key 不会提交）

demo 读取：

- `configs/public.yaml`（URL）
- `configs/private.local.yaml`（API Key，不提交）

至少需要：

- `services.deepseek.api_key`
- `services.amap_weather.api_key`（如果你调用 weather 工具）

### 如何扩展你自己的工具

要新增工具：

1. 在 `src/ai_agent/tools/examples/`（或你自己的目录）创建工具文件
2. 实现继承 `Tool` 的类，设置：
  - `name`、`description`
  - `input_schema`、`output_schema`
  - `run(args)`
3. 在 demo 中注册：
  - `registry.register(YourNewTool())`

orchestrator 会从 registry 自动读取工具列表，因此不需要额外改 function calling 逻辑。

### 架构图（Plan -> Tool -> Answer）

```
┌──────────────────────┐
│  User question       │
└─────────┬────────────┘
          │
          │ tool planner (LLM call #1)
          v
┌────────────────────────┐
│ LLM Planner             │
│ returns strict JSON:    │
│ tool_call or final      │
└─────────┬──────────────┘
          │ tool_call
          v
┌──────────────────────────────┐
│ ToolRegistry (singleton)      │
│ find tool by name and execute │
└─────────┬────────────────────┘
          │ tool output JSON
          v
┌──────────────────────┐
│ LLM Answer (call #2)  │
│ concise final answer  │
└──────────────────────┘
```

---

## English Version

## What you build in Stage 02

This stage adds a classic, framework-agnostic **function-calling learning loop**:

1. **Tool definitions** (JSON Schema for inputs and outputs)
2. **Tool registry** (a singleton: register / get / list / execute)
3. **LLM planner protocol** (LLM returns strict JSON describing which tool to call)
4. **Tool execution** (parse planner JSON -> call tool -> capture tool result)
5. **Final answer** (send tool result back to the LLM to produce a concise response)

Important: this demo does **NOT** change your existing DeepSeek native LLM client.
Instead, it works with the existing `.chat(user_query: str) -> str` interface.

## Files overview

- `src/ai_agent/tools/base.py`
  - Defines the `Tool` abstract base class (metadata + schemas + `run(args)`).
- `src/ai_agent/tools/schemas.py`
  - Small helpers to build minimal JSON Schema objects for tools.
- `src/ai_agent/tools/registry.py`
  - Singleton `ToolRegistry` with:
    - `register(tool)`
    - `get(name)`
    - `list_tools()` (for prompting the LLM)
    - `execute(name, args)` (runs the tool and returns a wrapper result)
- `src/ai_agent/tools/function_calling.py`
  - Implements the end-to-end orchestrator:
    - Planner prompt -> parse planner JSON -> tool execution -> answer prompt
- `src/ai_agent/tools/examples/`
  - Example tools:
    - `calculator.py` -> safe arithmetic evaluation
    - `get_time.py` -> current time
    - `amap_weather.py` -> weather query tool (returns raw JSON)
- `src/ai_agent/learning/stage_02_tools_function_calling/function_calling_demo.py`
  - A runnable example that registers tools and runs the full loop.

## Tool interface (Tool base class)

Every tool in this scaffold follows the same contract:

- **Static metadata**
  - `name`: string used by the planner
  - `description`: shown to the planner in prompts
- **Input/Output schemas**
  - `input_schema`: JSON Schema describing tool arguments
  - `output_schema`: JSON Schema describing the tool result shape
- **Execution**
  - `run(args: dict) -> JSON-serializable result`

### Flowchart 1: How to define a Tool

```text
┌──────────────────────────────────────┐
│ Pick a capability (your new tool)    │
│ e.g. calculator / get_time / weather │
└───────────────────┬──────────────────┘
                    │
                    v
┌──────────────────────────────────────┐
│ Implement a Tool class               │
│ class XxxTool(Tool)                  │
│ 1) name / description                │
│ 2) input_schema / output_schema      │
│ 3) run(args) implementation          │
└───────────────────┬──────────────────┘
                    │
                    v
┌──────────────────────────────────────┐
│ Register into the singleton registry │
│ registry.register(XxxTool())         │
└───────────────────┬──────────────────┘
                    │
                    v
┌──────────────────────────────────────┐
│ Use it in demos/agents               │
│ - planner reads schemas -> arguments │
│ - registry.execute(...) runs tool    │
└──────────────────────────────────────┘
```

Why JSON Schema?
Since the planner is an LLM, we need a compact “shape contract” so it can put arguments
into `arguments` correctly (e.g. `{"expression": "3**5"}`).

## JSON Schema (how arguments are shaped)

In this demo we use a minimal subset of JSON Schema:

- tool input and output are objects
- `additionalProperties: false`
- explicit `required` fields

This keeps the demo small and easy to reason about.

## Tool registry (singleton architecture)

The singleton registry is used to avoid threading a registry object through many layers.

Typical flow:

1. Demo registers tools:

`registry.register(CalculatorTool())`, etc.
2. Orchestrator asks registry for tool definitions:
`registry.list_tools()`
3. Orchestrator executes the chosen tool:
`registry.execute(tool_name, arguments)`

The returned value is wrapped as:

- `ToolExecutionResult(tool_name=..., output=...)`

## Planner protocol: LLM Function Calling (planner JSON)

To keep this demo framework-agnostic, we implement our own **strict planner JSON protocol**.

The orchestrator does a first LLM call with a prompt that includes:

- the tool list (name/description/schemas)
- explicit allowed planner return formats

The LLM must return STRICT JSON ONLY (no markdown, no extra text).

Allowed planner outputs:

1. Tool call:

```json
{
  "type": "tool_call",
  "tool_name": "calculator",
  "arguments": { "...": "..." }
}
```

1. Final:

```json
{
  "type": "final",
  "answer": "..."
}
```

### Important note on parsing

The parser in `function_calling.py` extracts the **first JSON object** from the LLM output.
So it assumes the model output is “mostly JSON”.

In later stages, you can replace this with a strict JSON parser / schema validator.

## Full call flow (end-to-end)

Given a user question:

1. **Plan**
  - LLM -> planner JSON deciding:
    - tool_call OR final
2. **Execute**
  - If `tool_call`:
    - registry executes the tool by `tool_name`
    - tool receives `arguments` as a dict
3. **Answer**
  - LLM -> concise final response using the tool output JSON

### Flowchart 2: Tool calling execution flow (Function Calling)

```text
┌──────────────────────────────────────┐
│ User question (natural language)     │
└───────────────────┬──────────────────┘
                    │
                    v
┌──────────────────────────────────────┐
│ LLM Planner (call #1)                │
│ - reads tool definitions (schemas)   │
│ - returns STRICT JSON: tool_call/final│
└───────────────────┬──────────────────┘
                    │ tool_call
                    v
┌──────────────────────────────────────┐
│ ToolRegistry.execute(...)            │
│ - find tool by tool_name             │
│ - pass arguments dict into run()     │
│ - get tool output JSON               │
└───────────────────┬──────────────────┘
                    │
                    v
┌──────────────────────────────────────┐
│ LLM Answer (call #2)                 │
│ - input: tool output JSON            │
│ - output: concise final text answer  │
└──────────────────────────────────────┘
```

### Architecture diagram (Plan -> Tool -> Answer)

```
┌──────────────────────┐
│  User question       │
└─────────┬────────────┘
          │ (text)
          v
┌──────────────────────┐
│ LLM Planner (call #1)│
│  STRICT JSON only    │
│ {"type":...}         │
└─────────┬────────────┘
          │
          │ if type == "tool_call"
          v
┌──────────────────────────────┐
│ ToolRegistry (singleton)     │
│ - get tool by name          │
│ - execute with arguments    │
└─────────┬────────────────────┘
          │ (tool output JSON)
          v
┌──────────────────────┐
│ LLM Answer (call #2) │
│ concise final text   │
└──────────────────────┘
```

## Runnable example (end-to-end)

Run the demo:

```bash
PYTHONPATH=src python src/ai_agent/learning/stage_02_tools_function_calling/function_calling_demo.py "3的5次方等于多少？"
```

Try other queries:

- calculator: `2*(10+3)`
- time: `现在几点？`
- weather: `广州天气怎么样？` (requires `services.amap_weather.api_key`)

## Required configuration (keys are not committed)

This demo reads config from:

- `configs/public.yaml` (URLs)
- `configs/private.local.yaml` (API keys, not committed)

You need:

- `services.deepseek.api_key`
- `services.amap_weather.api_key` (only if you call `amap_weather`)

## How to add your own tool (extension)

To add a new tool:

1. Create a new tool file under `src/ai_agent/tools/examples/` (or your own folder)
2. Implement a class inheriting `Tool`:
  - set `name`, `description`
  - define `input_schema` and `output_schema`
  - implement `run(args)`
3. Register it in the demo:
  - `registry.register(YourNewTool())`

No changes needed in the orchestrator: it reads tool definitions from the registry.
