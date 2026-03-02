# 测试执行指南

**版本**: 1.0.0
**日期**: 2026-03-02
**作者**: AI 测试工程师

---

## 目录

1. [环境准备](#环境准备)
2. [测试执行](#测试执行)
3. [测试报告](#测试报告)
4. [CI/CD集成](#cicd集成)
5. [故障排查](#故障排查)

---

## 环境准备

### 1. 安装依赖

```bash
# 安装测试依赖
pip install -e ".[test]"

# 或手动安装
pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-html
pip install httpx psycopg2-binary redis
```

### 2. 启动测试环境

```bash
# 使用 Docker Compose 启动测试数据库
docker-compose -f docker-compose.test.yml up -d

# 验证连接
psql postgresql://test_user:test_pass@localhost:5433/agent_framework_test
redis-cli -h localhost -p 6380 ping
```

### 3. 环境变量配置

```bash
# 创建 .env.test 文件
cat > .env.test << EOF
DATABASE_URL=postgresql://test_user:test_pass@localhost:5433/agent_framework_test
REDIS_URL=redis://localhost:6380
TEST_MODE=true
LLM_API_KEY=test_key
EOF

# 加载环境变量
source .env.test
```

---

## 测试执行

### 快速开始

```bash
# 运行所有测试
python run_tests.py

# 运行特定类型测试
python run_tests.py --type unit       # 单元测试
python run_tests.py --type integration # 集成测试
python run_tests.py --type e2e        # 端到端测试

# 生成覆盖率报告
python run_tests.py --coverage

# 并行执行（4个worker）
python run_tests.py --parallel 4

# HTML报告
python run_tests.py --report test-report.html
```

### 直接使用 pytest

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/tenant/test_tenant.py

# 运行特定测试类
pytest tests/api/test_api.py::TestAPIAuthentication

# 运行特定测试方法
pytest tests/api/test_api.py::TestAPIAuthentication::test_api_without_credentials

# 使用标记运行
pytest -m unit              # 仅单元测试
pytest -m integration       # 仅集成测试
pytest -m e2e               # 仅端到端测试
pytest -m "not slow"        # 排除慢速测试
pytest -m "tenant or api"   # 租户或API测试
```

### 性能测试

```bash
# 使用 Locust 运行性能测试
locust -f tests/performance/test_load.py

# Headless 模式
locust -f tests/performance/test_load.py --headless --users 100 --spawn-rate 10 --run-time 60s

# 特定用户类型
locust -f tests/performance/test_load.py AgentUser
locust -f tests/performance/test_load.py RecommendationUser
```

---

## 测试报告

### 覆盖率报告

```bash
# 生成 HTML 覆盖率报告
pytest --cov=. --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### HTML 测试报告

```bash
# 生成 HTML 报告
pytest --html=report.html --self-contained-html

# 查看报告
open report.html
```

### JUnit XML 报告

```bash
# 生成 JUnit XML（用于 CI/CD）
pytest --junitxml=results.xml
```

---

## CI/CD 集成

### GitHub Actions 示例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: agent_framework_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[test]"

      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml --junitxml=results.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 故障排查

### 常见问题

#### 1. 数据库连接失败

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案**:
```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 重启数据库
docker-compose -f docker-compose.test.yml restart postgres_test
```

#### 2. Redis 连接失败

```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解决方案**:
```bash
# 检查 Redis 是否运行
redis-cli -h localhost -p 6380 ping

# 重启 Redis
docker-compose -f docker-compose.test.yml restart redis_test
```

#### 3. 异步测试失败

```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**解决方案**:
```bash
# 确保安装了 pytest-asyncio
pip install pytest-asyncio

# 检查 pytest.ini 中的 asyncio-mode 配置
```

#### 4. 导入错误

```
ModuleNotFoundError: No module named 'agent'
```

**解决方案**:
```bash
# 使用可编辑模式安装
pip install -e .

# 或将项目根目录添加到 PYTHONPATH
export PYTHONPATH=/path/to/project:$PYTHONPATH
```

### 调试测试

```bash
# 使用 pdb 调试
pytest --pdb

# 在失败时进入调试器
pytest --pdb --trace

# 显示详细输出
pytest -vv -s

# 只运行上次失败的测试
pytest --lf

# 先运行上次失败的，然后运行其他
pytest --ff
```

---

## 测试最佳实践

1. **隔离性**: 每个测试应该独立运行，不依赖其他测试
2. **可重复性**: 测试结果应该是确定性的，多次运行应该得到相同结果
3. **快速性**: 单元测试应该快速执行（< 1秒）
4. **清晰性**: 测试名称应该清楚描述测试内容
5. **维护性**: 测试代码应该和生产代码一样高质量

---

**文档作者**: AI 测试工程师
**最后更新**: 2026-03-02
**版本**: 1.0.0
