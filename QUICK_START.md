# 快速开始指南

## 🚀 验证所有模块

```bash
# 运行验证脚本
python3 << 'EOF'
from agent.core import BaseSkill, SkillRegistry, ContextManager
from agent.intelligence import IntentClassifier, SlotFiller, SemanticLayer
from agent.memory import WorkingMemory, UserProfile, MemoryManager
from examples.smart_shopping_assistant import ShoppingAssistant

print("✅ 所有模块导入成功!")
EOF
```

## 🧪 运行测试

```bash
# 安装依赖
pip install -r requirements.txt

# 运行单元测试
pytest tests/ -v

# 运行特定测试
pytest tests/core/test_base_skill.py -v
pytest tests/intelligence/test_intent_classifier.py -v
pytest tests/memory/test_working_memory.py -v
```

## 🤖 运行智能购物助手

```bash
# 方式1: 作为模块运行
python -c "
from examples.smart_shopping_assistant.assistant import ShoppingAssistant
assistant = ShoppingAssistant()
print('✅ 购物助手初始化成功!')
print(f'配置: {assistant.config}')
"

# 方式2: 交互式Demo (如果存在)
python examples/smart_shopping_assistant/demo.py

# 方式3: 在代码中使用
python << 'EOF'
import asyncio
from examples.smart_shopping_assistant.assistant import ShoppingAssistant

async def test_assistant():
    assistant = ShoppingAssistant()

    # 测试自然语言理解
    response = await assistant.chat(
        user_input="我想买一款轻一点的笔记本电脑",
        user_id="test_user",
        session_id="test_session"
    )

    print(f"助手回复: {response.text}")
    print(f"置信度: {response.confidence}")

asyncio.run(test_assistant())
EOF
```

## 📁 项目结构速览

```
agent-skills-exec/
├── agent/
│   ├── core/                  # 核心架构
│   │   ├── interfaces.py      # 接口定义
│   │   ├── base_skill.py      # 抽象基类
│   │   ├── skill_registry.py  # 注册表
│   │   └── context_manager.py # 上下文管理
│   ├── intelligence/          # 智能增强
│   │   ├── intent_classifier.py  # 意图分类
│   │   ├── slot_filler.py        # 槽位填充
│   │   └── semantic_layer.py     # 语义层
│   └── memory/                # 记忆系统
│       ├── working_memory.py   # 工作记忆
│       ├── user_profile.py       # 用户画像
│       └── memory_manager.py     # 记忆管理
├── examples/
│   └── smart_shopping_assistant/  # 智能购物助手
│       ├── assistant.py           # 主类
│       ├── nlp_understanding.py   # NLP理解
│       ├── sentiment_analyzer.py  # 情感分析
│       ├── recommendation_engine.py # 推荐引擎
│       ├── conversation_manager.py  # 对话管理
│       └── ... (共13个文件)
├── tests/
│   ├── core/                 # 核心测试
│   ├── intelligence/         # 智能模块测试
│   ├── memory/               # 记忆系统测试
│   └── ...
└── docs/                     # 文档

设计文档:
├── ARCHITECTURE_REFACTOR_DESIGN.md      # 架构重构设计
├── INTELLIGENCE_ENHANCEMENT_DESIGN.md   # 智能增强设计
├── ENGINEERING_ENHANCEMENT_DESIGN.md    # 工程化设计
├── MVP_IMPLEMENTATION_PLAN.md           # MVP实施计划
├── CODE_QUALITY_REPORT.md               # 代码质量报告
└── ... (共8份设计文档，约160KB)
```

## 🐛 故障排除

### 问题1: 导入错误
```bash
# 如果出现 ImportError，请确保在正确的目录下运行
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 问题2: 依赖缺失
```bash
# 安装所有依赖
pip install -r requirements.txt

# 如果 requirements.txt 不存在，安装核心依赖
pip install pydantic typing-extensions
```

### 问题3: 测试失败
```bash
# 运行特定测试以查看详细错误
pytest tests/core/test_base_skill.py -v --tb=short

# 跳过失败的测试继续执行
pytest tests/ -v --ignore=tests/failing/
```

## 📞 获取帮助

如需进一步协助：

1. **查看设计文档**: `*_DESIGN.md` 文件
2. **阅读代码注释**: 所有模块都有详细文档字符串
3. **运行测试**: `pytest tests/ -v` 查看示例用法
4. **查看示例**: `examples/` 目录

---

**快速开始时间**: 5分钟
**完整测试时间**: 10-15分钟
**文档阅读时间**: 30分钟

祝您使用愉快！🚀
