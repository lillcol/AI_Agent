# Stage 04 - Memory

目标：实现带记忆的 ReAct Agent（多轮对话 + 知识积累）。

## 你会构建什么

- 短期记忆（ShortTermMemory）
  - 存储当前会话中的用户输入、助手回答、工具结果。
  - 支持自动裁剪，避免上下文无限增长。
- 长期记忆（LongTermMemoryFile）
  - 把长期可复用知识写入本地 JSONL 文件（持久化）。
  - 后续可替换为数据库/向量库，不影响 Agent 主流程。
- 统一记忆管理器（MemoryManager）
  - 统一读写短期/长期记忆，给 Agent 提供单一调用入口。
- 记忆增强 ReAct Demo（memory_react_demo.py）
  - 在每轮推理前进行记忆召回，并把召回内容注入 prompt。

## 目录与文件

- `src/ai_agent/core/memory/base.py`
  - 抽象接口 `BaseMemory` 与统一记录结构 `MemoryRecord`。
- `src/ai_agent/core/memory/short_term.py`
  - 列表型短期记忆实现，支持双重裁剪：最大条数 + 字符预算。
- `src/ai_agent/core/memory/long_term_file.py`
  - JSONL 文件型长期记忆实现，支持读写/检索。
  - 写入时按 `topic + content` 归一化哈希去重，避免重复知识污染。
- `src/ai_agent/core/memory/manager.py`
  - 统一管理短期和长期记忆的读写与格式化召回。
- `src/ai_agent/learning/stage_04_memory/memory_react_demo.py`
  - 可运行示例：多轮问答 + 记忆召回 + 工具调用 + 长期知识沉淀。

## 运行方式

脚本化示例（默认 3 轮问题）：

```bash
python src/ai_agent/learning/stage_04_memory/memory_react_demo.py
```

交互模式：

```bash
python src/ai_agent/learning/stage_04_memory/memory_react_demo.py --interactive
```

交互模式支持命令：

- `/clear`：清空短期记忆（不影响长期记忆文件）

查看长期记忆快照（运行前后都会打印）：

```bash
python src/ai_agent/learning/stage_04_memory/memory_react_demo.py --show-long-memory
```

## 默认示例场景

1) `3的5次方是多少？`
- Agent 调用 `calculator` 得到结果，并写入短期记忆。

2) `刚才的结果加10是多少？`
- Agent 召回短期记忆中的上次结果，再进行下一步计算。

3) `这个计算方法叫什么？`
- Agent 给出解释，并把该问答写入长期记忆（method_explanation）。

## 设计要点

- 抽象与实现分离
  - Agent 仅依赖 `MemoryManager`，不依赖具体存储后端。
- 召回顺序
  - 先短期（会话上下文），再长期（可复用知识）。
  - 短期使用 hybrid 召回：相关命中 + 最近上下文，降低历史污染。
- 可观测性
  - 运行日志会打印 short/long recall、action、observation 等关键信息。
- 长期记忆文件
  - 默认写入：`logs/memory/long_term_memory.jsonl`
- 进阶护栏
  - 短期记忆增加字符预算（`max_chars`）防止 prompt 膨胀。
  - 长期记忆默认去重，减少重复写入。
