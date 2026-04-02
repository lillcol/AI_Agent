"""Stage 00 教程示例：最小可运行 LLM 调用（DeepSeek）。

这个文件的目标非常明确：用最少代码演示一次完整的大模型调用流程。

你会看到的核心步骤：
1) 读取配置（base_url / api_key）
2) 组织 Chat Completions 请求体（system + user）
3) 发起 HTTP POST 请求
4) 提取并输出模型返回文本

该示例故意保持“单轮、无工具、无记忆”，便于初学者先掌握最基础调用链。
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib import request

if __package__ is None or __package__ == "":
    # 兼容“直接运行文件”的场景：
    # python src/ai_agent/learning/stage_00_foundation/react_hello_world.py
    #
    # 正常情况下，推荐使用模块方式运行（PYTHONPATH=src python -m ...）。
    # 但教程读者常常会直接运行 .py 文件，这里手动把 src 加入 sys.path，
    # 避免出现 `ModuleNotFoundError: No module named 'ai_agent'`。
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ai_agent.config.settings import settings


@dataclass
class DeepSeekClient:
    """最小 DeepSeek 客户端（仅保留教程需要的字段）。"""

    # 模型服务基础地址，例如：https://api.deepseek.com
    base_url: str
    # API Key（从 private.local.yaml 读取，不应提交到 Git）
    api_key: str
    # 默认模型名称，可按需替换
    model: str = "deepseek-chat"
    # 请求超时时间（秒）
    timeout: int = 60

    def chat(self, user_query: str) -> str:
        """发送一次用户问题，返回模型文本答案。"""
        # system_prompt 用于控制输出风格：
        # - 简洁
        # - 直接给答案
        # - 不暴露推理过程
        system_prompt = (
            "你是一个简洁助手。"
            "请直接给出结果，语言尽量简洁。"
            "不要输出思考过程、推理步骤或中间分析。"
        )

        # Chat Completions 最小请求体：
        # - model: 使用的模型
        # - temperature=0: 让输出更稳定、可复现
        # - messages: 对话上下文（system + user）
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
        }

        # DeepSeek Chat Completions 端点。
        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"

        # 用 urllib 构造标准 HTTP POST 请求。
        # data 需要是 bytes，所以先 json.dumps 再 encode("utf-8")。
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        # 执行请求并解析响应 JSON。
        with request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        # DeepSeek 返回格式里，最终文本在：
        # choices[0].message.content
        return body["choices"][0]["message"]["content"].strip()


def main() -> None:
    # 1) 从统一配置入口读取 DeepSeek 配置
    # settings 会自动合并 public.yaml + private.local.yaml。
    deepseek_cfg = settings.services.get("deepseek", {})
    base_url = deepseek_cfg.get("base_url")
    api_key = deepseek_cfg.get("api_key")

    # 2) 读取用户输入
    # 优先命令行参数，方便脚本化调用：
    # python .../react_hello_world.py "3的5次方等于多少？"
    # 若没传参数，则进入交互输入模式。
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("请输入问题（例如：3的5次方等于多少？）: ").strip()

    # 3) 构造客户端，执行单轮调用，打印结果
    client = DeepSeekClient(base_url=base_url, api_key=api_key)
    answer = client.chat(query)
    print(answer)


if __name__ == "__main__":
    # 作为脚本运行时，从这里进入。
    main()
