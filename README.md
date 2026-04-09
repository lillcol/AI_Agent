# AI Agent Learning Scaffold (Python)

一个用于从零学习 AI Agent 开发的极简、可长期维护项目骨架。

## 项目目标

- 保持结构清晰、模块化，便于按学习进度逐步扩展。
- 仅提供基础工程能力：配置、日志、目录分层、代码规范。
- 不包含任何业务逻辑与具体 Agent 实现。

## 目录结构

```text
AI_Agent/
├── .env.example
├── .gitignore
├── .editorconfig
├── pyproject.toml
├── requirements.txt
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── configs/
│   ├── public.yaml
│   └── private.example.yaml
├── logs/
│   └── .gitkeep
└── src/
    └── ai_agent/
        ├── __init__.py
        ├── config/
        │   ├── __init__.py
        │   └── settings.py
        ├── core/
        │   ├── __init__.py
        │   ├── agent/
        │   │   └── __init__.py
        │   ├── llm/
        │   │   ├── __init__.py
        │   │   ├── clients.py
        │   │   └── factory.py
        │   ├── memory/
        │   │   └── __init__.py
        │   └── rag/
        │       └── __init__.py
        ├── frameworks/
        │   ├── __init__.py
        │   ├── langchain/
        │   │   └── __init__.py
        │   └── langgraph/
        │       └── __init__.py
        ├── learning/
        │   ├── __init__.py
        │   ├── README.md
        │   ├── stage_00_foundation/
        │   │   ├── __init__.py
        │   │   ├── README.md
        │   │   └── react_hello_world.py
        │   ├── stage_01_native_llm/
        │   │   ├── README.md
        │   │   └── weather_info_demo.py
        │   ├── stage_02_tools_function_calling/
        │   │   └── README.md
        │   ├── stage_03_react_agent/
        │   │   └── README.md
        │   ├── stage_04_memory/
        │   │   └── README.md
        │   ├── stage_05_rag/
        │   │   └── README.md
        │   ├── stage_06_framework_integrations/
        │   │   └── README.md
        │   ├── stage_07_multi_agent/
        │   │   └── README.md
        │   └── stage_08_evaluation_observability/
        │       └── README.md
        ├── tools/
        │   └── __init__.py
        └── utils/
            ├── __init__.py
            └── logger.py
```

## 模块功能说明

- `.env.example`：环境变量模板，用于统一管理密钥、运行环境与基础参数。
- `.gitignore`：Git 忽略规则，避免提交缓存、虚拟环境、日志与敏感配置。
- `.editorconfig`：跨编辑器统一缩进、换行、编码风格，减少格式差异。
- `pyproject.toml`：Python 项目基础配置与代码规范配置（如 Ruff）。
- `requirements.txt`：项目依赖清单（学习阶段保持最小依赖）。
- `CONTRIBUTING.md`：协作提交约定，帮助长期维护项目风格。
- `LICENSE`：开源协议（MIT）。
- `configs/public.yaml`：公共配置（非敏感，可提交 GitHub）。
- `configs/private.example.yaml`：私有配置模板（敏感信息只写到本地私有文件）。
- `logs/`：日志文件目录，运行时输出日志（示例为 `app.log`）。
- `src/ai_agent/`：主源码包根目录，承载所有核心模块。

- `src/ai_agent/config/`：配置层，负责加载与集中管理环境变量和运行配置。
  - `settings.py`：统一配置入口，提供全局可读取的配置对象。

- `src/ai_agent/core/`：核心能力层，放与具体框架无关的 Agent 核心抽象。
  - `core/llm/`：模型调用抽象层；客户端定义在 `core/llm/clients.py`，初始化入口在 `core/llm/factory.py`。
  - `core/agent/`：Agent 行为编排层，后续用于 ReAct、Function Calling 等流程。
  - `core/memory/`：记忆层，后续扩展短期/长期记忆与存储接口。
  - `core/rag/`：RAG 层，后续扩展检索、重排序、上下文拼装流程。

- `src/ai_agent/tools/`：工具层，后续扩展工具协议、注册中心、工具执行适配。
- `src/ai_agent/utils/`：通用工具层，放跨模块复用的基础能力。
  - `logger.py`：日志初始化工具，统一日志格式、级别与输出通道。

- `src/ai_agent/frameworks/`：框架适配层，隔离第三方框架与核心逻辑。
  - `frameworks/langchain/`：LangChain 相关适配与桥接代码入口。
  - `frameworks/langgraph/`：LangGraph 相关适配与图编排桥接入口。
- `src/ai_agent/learning/`：阶段化学习入口，按 Stage 拆分学习任务。

## 快速开始

1. 创建并激活虚拟环境
2. 安装依赖：`pip install -r requirements.txt`
3. 复制环境变量模板：`cp .env.example .env`
4. 私有配置模板复制：`cp configs/private.example.yaml configs/private.local.yaml`
5. 在 `configs/private.local.yaml` 填入你自己的 API Key（不要提交）

## 学习入口（按阶段）

- 总入口：`src/ai_agent/learning/README.md`
- Stage 00：`src/ai_agent/learning/stage_00_foundation/README.md`
- Stage 01：`src/ai_agent/learning/stage_01_native_llm/README.md`
- Stage 02：`src/ai_agent/learning/stage_02_tools_function_calling/README.md`
- Stage 03：`src/ai_agent/learning/stage_03_react_agent/README.md`
- Stage 04：`src/ai_agent/learning/stage_04_memory/README.md`
- Stage 05：`src/ai_agent/learning/stage_05_rag/README.md`
- Stage 06：`src/ai_agent/learning/stage_06_framework_integrations/README.md`
- Stage 07：`src/ai_agent/learning/stage_07_multi_agent/README.md`
- Stage 08：`src/ai_agent/learning/stage_08_evaluation_observability/README.md`

Stage 00 runnable demo:

- DeepSeek hello world:
  `PYTHONPATH=src python -m ai_agent.learning.stage_00_foundation.react_hello_world "3的5次方等于多少？"`

Stage 01 runnable demo:

- Weather summary demo (AMap + DeepSeek):
  `python src/ai_agent/learning/stage_01_native_llm/weather_info_demo.py 广州`

## 配置安全约定（公共/私有）

- 可提交：`.env.example`、`configs/public.yaml`、`configs/private.example.yaml`
- 不可提交：`.env`、`.env.*`、`configs/private.yaml`、`configs/private.local.yaml`
- 原则：密钥、token、数据库密码等仅放本地私有配置文件

## API 配置说明（当前已预置）

- `Minimax`
  - URL：`https://api.minimax.chat/v1`（在 `configs/public.yaml`）
  - KEY：`services.minimax.api_key`（在 `configs/private.local.yaml`）
- `DeepSeek`
  - URL：`https://api.deepseek.com`（在 `configs/public.yaml`）
  - KEY：`services.deepseek.api_key`（在 `configs/private.local.yaml`）
- `高德天气`
  - URL：`https://restapi.amap.com/v3/weather`（在 `configs/public.yaml`）
  - KEY：`services.amap_weather.api_key`（在 `configs/private.local.yaml`）

配置读取入口已统一在 `src/ai_agent/config/settings.py`，后续代码可通过 `settings.services` 获取。

## 后续扩展建议

- `core/llm`：原生 LLM 封装、模型路由、重试策略
- `core/agent`：ReAct、Function Calling、任务调度
- `core/memory`：短期/长期记忆管理
- `core/rag`：检索、向量库、重排序
- `frameworks/`：LangChain / LangGraph 适配层
- `tools/`：工具注册与工具协议

## 学习路线与里程碑（不含实现代码）

### Milestone 0: 工程基线（已完成）

- 目标：确保目录、配置、日志、环境变量机制可用。
- 目录重点：`config/`、`utils/`、`logs/`
- 产出建议：保持当前空架构，不新增业务逻辑。

### Milestone 1: 原生 LLM 调用封装

- 目标：建立最小模型调用抽象，屏蔽不同模型供应商差异。
- 建议新增位置：
  - `core/llm/`：如 `base.py`、`client.py`、`schemas.py`
  - `config/settings.py`：补充模型相关配置项
- 学习要点：请求参数规范化、超时与重试、错误分类。

### Milestone 2: 工具系统与 Function Calling

- 目标：统一工具协议与注册机制，为 Agent 调用工具做准备。
- 建议新增位置：
  - `tools/`：如 `base.py`、`registry.py`
  - `core/agent/`：如 `tool_executor.py`（仅编排层）
- 学习要点：工具输入输出 Schema、工具异常处理、可观测日志。

### Milestone 3: ReAct Agent 核心循环

- 目标：建立最小“思考-行动-观察”循环框架。
- 建议新增位置：
  - `core/agent/`：如 `react_loop.py`、`state.py`
  - `core/llm/`：补充对话上下文接口
- 学习要点：状态管理、终止条件、循环保护（最大步数）。

### Milestone 4: 记忆系统（短期/长期）

- 目标：把会话上下文与长期记忆解耦，形成可替换存储层。
- 建议新增位置：
  - `core/memory/`：如 `short_term.py`、`long_term.py`、`store_base.py`
  - `core/agent/`：接入记忆读写接口
- 学习要点：记忆裁剪策略、召回时机、持久化边界。

### Milestone 5: RAG 最小闭环

- 目标：实现“查询->检索->重排序->注入上下文”的标准链路。
- 建议新增位置：
  - `core/rag/`：如 `retriever.py`、`reranker.py`、`pipeline.py`
  - `core/llm/`：支持上下文注入策略
- 学习要点：分块策略、召回质量评估、上下文窗口控制。

### Milestone 6: 框架集成层（LangChain / LangGraph）

- 目标：在不污染核心模块的前提下增加框架适配能力。
- 建议新增位置：
  - `frameworks/langchain/`：放适配器、桥接层
  - `frameworks/langgraph/`：放图节点与编排适配器
- 学习要点：核心逻辑与框架 API 隔离，避免强耦合。

### Milestone 7: 多智能体协作

- 目标：引入角色分工、路由与任务分发机制。
- 建议新增位置：
  - `core/agent/`：如 `orchestrator.py`、`router.py`
  - `core/memory/`：扩展共享记忆接口
- 学习要点：代理间通信协议、冲突处理、协作可观测性。

### Milestone 8: 评估与可观测

- 目标：建立稳定迭代闭环，支持回归验证。
- 建议新增位置：
  - `utils/`：如 `tracing.py`、`metrics.py`
  - 项目根目录：`tests/`（后续按阶段加入）
- 学习要点：日志关联 ID、离线评估集、关键指标跟踪。

## 每阶段统一检查清单

- 配置是否只放在 `config/`，避免散落常量
- 日志是否包含关键上下文（request_id、step、tool_name）
- 核心能力是否先抽象接口再加实现
- 新增依赖是否最小化且记录在 `requirements.txt`
- 模块命名是否保持单一职责、可替换、可测试
