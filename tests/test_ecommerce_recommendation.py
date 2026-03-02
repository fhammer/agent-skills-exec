"""电商推荐Skill测试"""

import pytest
import asyncio
from skills.ecommerce_recommendation.executor import (
    EcommerceRecommendationExecutor,
    DemandAnalyzer,
    ProductSearcher,
    RecommendationRanker
)
from skills.ecommerce_recommendation.schema import (
    UserIntent,
    DialogueState
)


class TestDemandAnalyzer:
    """需求分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return DemandAnalyzer()

    @pytest.mark.asyncio
    async def test_extract_category_phone(self, analyzer):
        """测试提取手机类别"""
        result = await analyzer.analyze("我想买个手机", {})
        assert result.category == "手机"

    @pytest.mark.asyncio
    async def test_extract_price_range(self, analyzer):
        """测试提取价格区间"""
        result = await analyzer.analyze("我想买个2000-3000的手机", {})
        price_constraint = next(
            (c for c in result.constraints if c.type == "price_range"),
            None
        )
        assert price_constraint is not None
        assert price_constraint.value["min"] == 2000
        assert price_constraint.value["max"] == 3000

    @pytest.mark.asyncio
    async def test_detect_intent_recommendation(self, analyzer):
        """测试检测推荐意图"""
        result = await analyzer.analyze("给我推荐一款手机", {})
        assert result.intent == UserIntent.RECOMMENDATION_REQUEST

    @pytest.mark.asyncio
    async def test_extract_brand_xiaomi(self, analyzer):
        """测试提取小米品牌"""
        result = await analyzer.analyze("我想买个小米手机", {})
        brand_constraint = next(
            (c for c in result.constraints if c.type == "brand"),
            None
        )
        assert brand_constraint is not None
        assert "小米" in brand_constraint.value

    @pytest.mark.asyncio
    async def test_extract_use_case_gaming(self, analyzer):
        """测试提取游戏用途"""
        result = await analyzer.analyze("平时玩游戏比较多", {})
        use_case_constraint = next(
            (c for c in result.constraints if c.type == "use_case"),
            None
        )
        assert use_case_constraint is not None
        assert use_case_constraint.value == "游戏"


class TestProductSearcher:
    """商品搜索器测试"""

    @pytest.fixture
    def searcher(self):
        return ProductSearcher()

    @pytest.fixture
    def sample_demand(self):
        from skills.ecommerce_recommendation.schema import DemandAnalysis, Constraint
        return DemandAnalysis(
            intent=UserIntent.RECOMMENDATION_REQUEST,
            category="手机",
            constraints=[
                Constraint(
                    type="price_range",
                    value={"min": 2000, "max": 3000}
                )
            ],
            missing_info=[]
        )

    @pytest.mark.asyncio
    async def test_search_returns_products(self, searcher, sample_demand):
        """测试搜索返回商品"""
        result = await searcher.search(sample_demand)
        assert "products" in result
        assert len(result["products"]) > 0

    @pytest.mark.asyncio
    async def test_search_filters_by_price(self, searcher, sample_demand):
        """测试价格过滤"""
        result = await searcher.search(sample_demand)
        products = result["products"]
        for product in products:
            assert 2000 <= product.price <= 3000


class TestRecommendationRanker:
    """推荐排序器测试"""

    @pytest.fixture
    def ranker(self):
        return RecommendationRanker()

    @pytest.fixture
    def sample_products(self):
        from skills.ecommerce_recommendation.schema import Product
        return [
            Product(
                product_id="p_001",
                name="Redmi K70",
                brand="小米",
                price=2499,
                category="手机",
                rating=4.7,
                sales=50000,
                attributes={"processor": "骁龙8 Gen2"}
            ),
            Product(
                product_id="p_002",
                name="iQOO Neo9",
                brand="iQOO",
                price=2299,
                category="手机",
                rating=4.6,
                sales=30000,
                attributes={"processor": "骁龙8 Gen2"}
            )
        ]

    @pytest.mark.asyncio
    async def test_rank_returns_order(self, ranker, sample_products):
        """测试排序返回有序结果"""
        from skills.ecommerce_recommendation.schema import DemandAnalysis, Constraint
        demand = DemandAnalysis(
            intent=UserIntent.RECOMMENDATION_REQUEST,
            category="手机",
            constraints=[],
            missing_info=[]
        )

        results = await ranker.rank(sample_products, demand, None)
        assert len(results) == 2
        assert results[0].rank == 1
        assert results[0].total_score >= results[1].total_score


class TestEcommerceRecommendationExecutor:
    """电商推荐执行器集成测试"""

    @pytest.fixture
    def executor(self):
        return EcommerceRecommendationExecutor()

    @pytest.mark.asyncio
    async def test_full_flow_recommendation(self, executor):
        """测试完整推荐流程"""
        result = await executor.execute(
            user_input="我想买个2000-3000的手机，平时玩游戏比较多",
            user_id="test_user_123"
        )

        assert result is not None
        assert result.dialogue_state == DialogueState.RECOMMENDATION_READY
        assert len(result.recommendations) > 0
        assert result.response_text
        print("\n=== 推荐结果 ===")
        print(result.response_text)

    @pytest.mark.asyncio
    async def test_clarification_response(self, executor):
        """测试澄清响应"""
        result = await executor.execute(
            user_input="我想买个好东西"
        )

        assert result.dialogue_state == DialogueState.AWAITING_CLARIFICATION
        assert "请补充" in result.response_text or "请问" in result.response_text

    @pytest.mark.asyncio
    async def test_product_comparison(self, executor):
        """测试商品对比"""
        result = await executor.compare_products(
            product_names=["Redmi K70", "iQOO Neo9"],
            user_id="test_user_123"
        )

        assert result is not None
        assert len(result.products) == 2
        assert result.comparison_points
        assert result.recommendation
        print("\n=== 对比结果 ===")
        print(f"推荐: {result.recommendation}")


def test_manual_example():
    """手动测试示例"""
    import asyncio

    async def run():
        executor = EcommerceRecommendationExecutor()

        # 测试1: 明确需求
        print("\n=== 测试1: 明确需求 ===")
        result1 = await executor.execute(
            user_input="我想买个2000-3000的手机，平时玩游戏比较多",
            user_id="user_001"
        )
        print(result1.response_text)

        # 测试2: 模糊需求
        print("\n=== 测试2: 模糊需求 ===")
        result2 = await executor.execute(
            user_input="我想买个好东西"
        )
        print(result2.response_text)

        # 测试3: 商品对比
        print("\n=== 测试3: 商品对比 ===")
        result3 = await executor.compare_products(
            product_names=["Redmi K70", "iQOO Neo9"]
        )
        print(result3.recommendation)

    asyncio.run(run())


if __name__ == "__main__":
    test_manual_example()
