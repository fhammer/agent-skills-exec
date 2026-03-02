"""Tests for Planner module."""

import pytest
from unittest.mock import Mock, MagicMock
from agent.planner import PlannerError
from agent.planner import Planner
from agent.llm_client import LLMClient


class TestPlanner:
    """Test Planner functionality."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = Mock(spec=LLMClient)
        return client

    @pytest.fixture
    def planner(self, mock_llm_client):
        """Create a Planner instance."""
        return Planner(mock_llm_client, confidence_threshold=0.7)

    def test_planner_initialization(self, planner):
        """Test planner initializes correctly."""
        assert planner.llm is not None
        assert planner.confidence_threshold == 0.7

    def test_generate_plan_with_high_confidence(self, planner, mock_llm_client):
        """Test plan generation when confidence is high."""
        # Mock LLM response with high confidence
        mock_llm_client.invoke = MagicMock(return_value='{"intent": "test_intent", "steps": [{"skill": "test_skill", "sub_task": "test task", "confidence": 0.9}]}')

        available_skills = {
            "test_skill": type('Skill', (object,), {'description': 'Test Skill', 'triggers': [], 'tags': []})()
        }

        plan = planner.generate_plan("test input", available_skills)

        assert plan is not None
        assert len(plan.steps) == 1
        assert plan.steps[0]["skill"] == "test_skill"

    def test_generate_plan_with_low_confidence(self, planner, mock_llm_client):
        """Test plan generation when confidence is low."""
        # Mock LLM response with low confidence
        mock_llm_client.invoke = MagicMock(return_value='{"intent": "unclear", "steps": []}')

        available_skills = {
            "test_skill": type('Skill', (object,), {'description': 'Test Skill', 'triggers': [], 'tags': []})()
        }

        with pytest.raises(PlannerError):
            planner.generate_plan("unclear input", available_skills)

    def test_generate_plan_with_multiple_skills(self, planner, mock_llm_client):
        """Test plan generation with multiple skills."""
        mock_llm_client.invoke = MagicMock(return_value='{"intent": "complex_request", "steps": [{"skill": "skill1", "sub_task": "task 1", "confidence": 0.9}, {"skill": "skill2", "sub_task": "task 2", "confidence": 0.8}, {"skill": "skill3", "sub_task": "task 3", "confidence": 0.85}]}')

        available_skills = {
            "skill1": type('Skill', (object,), {'description': 'Skill 1', 'triggers': [], 'tags': []})(),
            "skill2": type('Skill', (object,), {'description': 'Skill 2', 'triggers': [], 'tags': []})(),
            "skill3": type('Skill', (object,), {'description': 'Skill 3', 'triggers': [], 'tags': []})()
        }

        plan = planner.generate_plan("complex request", available_skills)

        assert len(plan.steps) == 3

    def test_skill_selection_from_available(self, planner, mock_llm_client):
        """Test that only available skills are selected."""
        mock_llm_client.invoke = MagicMock(return_value={
            "plan": [
                {"skill": "available_skill", "sub_task": "test", "confidence": 0.9}
            ],
            "confidence": 0.9
        })

        available_skills = {
            "available_skill": type('Skill', (object,), {'description': 'Available Skill', 'triggers': [], 'tags': []})()
        }

        # Mock LLM response with available skill
        mock_llm_client.invoke = MagicMock(return_value='{"intent": "test_intent", "steps": [{"skill": "available_skill", "sub_task": "test task", "confidence": 0.85}]}')

        plan = planner.generate_plan("test", available_skills)

        assert len(plan.steps) == 1
        assert plan.steps[0]["skill"] == "available_skill"


class TestPlannerEcommerceScenarios:
    """Test Planner with e-commerce scenarios."""

    @pytest.fixture
    def ecommerce_planner(self):
        """Create planner for e-commerce testing."""
        mock_llm = Mock()
        planner = Planner(mock_llm, confidence_threshold=0.7)
        return planner

    def test_order_query_intent(self, ecommerce_planner):
        """Test planner identifies order query intent."""
        # Mock response for order query
        ecommerce_planner.llm.invoke = MagicMock(return_value='{"intent": "order_query", "steps": [{"skill": "order_query", "sub_task": "查询订单状态", "confidence": 0.95}]}')

        available_skills = {
            "order_query": type('Skill', (object,), {'description': '查询订单', 'triggers': [], 'tags': []})(),
            "product_recommend": type('Skill', (object,), {'description': '产品推荐', 'triggers': [], 'tags': []})(),
            "after_sales": type('Skill', (object,), {'description': '售后服务', 'triggers': [], 'tags': []})()
        }

        plan = ecommerce_planner.generate_plan("查一下我的订单", available_skills)

        assert len(plan.steps) == 1
        assert plan.steps[0]["skill"] == "order_query"

    def test_product_recommend_intent(self, ecommerce_planner):
        """Test planner identifies product recommendation intent."""
        ecommerce_planner.llm.invoke = MagicMock(return_value='{"intent": "product_recommendation", "steps": [{"skill": "demand_analysis", "sub_task": "分析用户需求", "confidence": 0.9}, {"skill": "product_search", "sub_task": "搜索商品", "confidence": 0.85}, {"skill": "recommendation_ranking", "sub_task": "排序推荐", "confidence": 0.85}]}')

        available_skills = {
            "demand_analysis": type('Skill', (object,), {'description': '需求分析', 'triggers': [], 'tags': []})(),
            "product_search": type('Skill', (object,), {'description': '产品搜索', 'triggers': [], 'tags': []})(),
            "recommendation_ranking": type('Skill', (object,), {'description': '推荐排序', 'triggers': [], 'tags': []})()
        }

        plan = ecommerce_planner.generate_plan("推荐一款手机", available_skills)

        assert len(plan.steps) == 3
        assert plan.steps[0]["skill"] == "demand_analysis"

    def test_return_request_intent(self, ecommerce_planner):
        """Test planner identifies return request intent."""
        ecommerce_planner.llm.invoke = MagicMock(return_value='{"intent": "return_request", "steps": [{"skill": "intent_classification", "sub_task": "分类退货意图", "confidence": 0.95}, {"skill": "policy_validation", "sub_task": "验证退货政策", "confidence": 0.9}, {"skill": "case_creation", "sub_task": "创建退货单", "confidence": 0.9}]}')

        available_skills = {
            "intent_classification": type('Skill', (object,), {'description': '意图分类', 'triggers': [], 'tags': []})(),
            "policy_validation": type('Skill', (object,), {'description': '政策验证', 'triggers': [], 'tags': []})(),
            "case_creation": type('Skill', (object,), {'description': '创建案例', 'triggers': [], 'tags': []})()
        }

        plan = ecommerce_planner.generate_plan("我想退货", available_skills)

        assert len(plan.steps) == 3
        assert plan.steps[0]["skill"] == "intent_classification"
