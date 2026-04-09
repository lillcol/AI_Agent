# Stage 01 - Native LLM

目标：建立最小原生 LLM 调用抽象。

建议关注：

- 请求与响应数据结构
- 超时、重试、错误处理
- 模型参数统一入口

## Weather Info Demo

本阶段提供一个“外部 API + 原生 LLM”的端到端示例：

- 文件：`src/ai_agent/learning/stage_01_native_llm/weather_info_demo.py`
- 数据源：高德天气 API（`services.amap_weather.*`）
- 模型：DeepSeek（`services.deepseek.*`）
- 流程：获取天气 JSON -> 交给 DeepSeek 生成简洁自然语言总结
- 抽象复用：天气 HTTP 调用统一复用 `src/ai_agent/core/integrations/amap_weather_client.py`

运行方式：

```bash
# 默认城市（北京）
python src/ai_agent/learning/stage_01_native_llm/weather_info_demo.py
```

```bash
# 指定城市
python src/ai_agent/learning/stage_01_native_llm/weather_info_demo.py 广州
```
