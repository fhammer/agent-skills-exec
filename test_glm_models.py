#!/usr/bin/env python3
"""
测试智谱可用的模型列表
"""

import os
from anthropic import Anthropic

api_key = "e2a6227dc48843e58d0600d4597a6810.37LhMInDNwKlpMMY"
base_url = "https://open.bigmodel.cn/api/anthropic"

# 可能的 GLM-4.7 模型名称变体
models_to_try = [
    "glm-4.7",
    "glm-4-7",
    "glm-47",
    "glm-4-plus",
    "glm-4-pro",
    "glm-4-turbo",
    "glm-4-max",
    "glm-4",
    "glm-4-flash",
]

print("测试智谱可用的模型...\n")

client = Anthropic(api_key=api_key, base_url=base_url)

for model in models_to_try:
    try:
        response = client.messages.create(
            model=model,
            max_tokens=50,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"✓ {model}: 可用 - 回复: {response.content[0].text[:30]}")
    except Exception as e:
        error_msg = str(e)
        if "1113" in error_msg:
            print(f"✗ {model}: 余额不足")
        elif "404" in error_msg or "400" in error_msg or "not found" in error_msg.lower():
            print(f"✗ {model}: 模型不存在")
        else:
            print(f"✗ {model}: {error_msg[:50]}")
