# Stage 00 - Foundation

目标：完成工程基线，确保项目结构、配置与日志可用。

建议关注：

- 目录分层与职责边界
- 配置加载与环境变量约定
- 日志初始化与输出规范

## Hello World Agent

本阶段提供一个最基础 demo：用户输入问题，直接调用 DeepSeek 返回结果。

- 文件：`src/ai_agent/learning/stage_00_foundation/react_hello_world.py`
- 模型：DeepSeek（读取 `services.deepseek.base_url` 与 `services.deepseek.api_key`）
- 功能：不做本地工具和多轮流程，只做一次请求与一次响应
- 输出约束：使用简洁语言直接返回结果，不输出思考过程或推理步骤

运行方式：

```bash
# 推荐（模块方式）
PYTHONPATH=src python -m ai_agent.learning.stage_00_foundation.react_hello_world "3的5次方等于多少？"
```

或直接运行后交互输入：

```bash
python src/ai_agent/learning/stage_00_foundation/react_hello_world.py
```

## Stage Note

天气示例已迁移到 `stage_01_native_llm`，因为它更符合“原生 LLM 调用 + 外部 API 数据总结”的学习目标。
