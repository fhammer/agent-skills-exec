"""
智能购物助手主类 - Shopping Assistant

集成所有模块，提供统一的智能购物助手功能。
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .types import (
    AssistantResponse, UserProfile, Product, SearchCriteria,
    IntentType, ResponseTone, ConversationSession,
    SuggestedAction, SentimentResult, SemanticUnderstandingResult
)
from .nlp_understanding import NLPUnderstanding
from .sentiment_analyzer import SentimentAnalyzer
from .product_database import ProductDatabase
from .user_profile_manager import UserProfileManager
from .conversation_manager import ConversationManager
from .recommendation_engine import RecommendationEngine


@dataclass
class AssistantConfig:
    """助手配置"""
    enable_personalization: bool = True
    enable_sentiment_analysis: bool = True
    enable_proactive_recommendation: bool = True
    max_products_in_response: int = 5
    response_tone: ResponseTone = ResponseTone.FRIENDLY
    min_confidence_threshold: float = 0.5


class ShoppingAssistant:
    """
    智能购物助手

    集成自然语言理解、情感分析、个性化推荐等功能，
    提供智能化的购物体验。
    """

    def __init__(
        self,
        config: Optional[AssistantConfig] = None,
        product_db: Optional[ProductDatabase] = None,
        user_profile_manager: Optional[UserProfileManager] = None
    ):
        """
        初始化购物助手

        Args:
            config: 助手配置
            product_db: 商品数据库
            user_profile_manager: 用户画像管理器
        """
        self.config = config or AssistantConfig()
        self.product_db = product_db or ProductDatabase()
        self.user_profile_manager = user_profile_manager or UserProfileManager()

        # 初始化各模块
        self.nlp = NLPUnderstanding()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.conversation_manager = ConversationManager()
        self.recommendation_engine = RecommendationEngine(self.product_db)

    async def chat(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AssistantResponse:
        """
        处理用户消息并返回响应

        Args:
            user_input: 用户输入文本
            user_id: 用户ID（可选）
            session_id: 会话ID（可选）

        Returns:
            助手响应
        """
        start_time = time.time()

        try:
            # 1. 获取或创建会话
            session_id = self.conversation_manager.get_or_create_session(session_id, user_id)
            session = self.conversation_manager.get_session(session_id)

            # 2. 获取用户画像
            user_profile = None
            if user_id and self.config.enable_personalization:
                user_profile = self.user_profile_manager.get_profile(user_id)

            # 3. 自然语言理解
            nlp_result = self.nlp.understand(user_input, session.context if session else None)

            # 4. 情感分析
            sentiment_result = None
            if self.config.enable_sentiment_analysis:
                sentiment_result = self.sentiment_analyzer.analyze(
                    user_input,
                    context={"history": self._get_conversation_history(session_id)}
                )

            # 5. 确定响应策略
            response_tone = self._determine_response_tone(nlp_result, sentiment_result)

            # 6. 处理意图
            response = self._process_intent(
                nlp_result=nlp_result,
                user_profile=user_profile,
                sentiment_result=sentiment_result,
                response_tone=response_tone,
                session_id=session_id
            )

            # 7. 记录对话
            self.conversation_manager.add_turn(
                session_id=session_id,
                user_input=user_input,
                assistant_response=response.text,
                intent=nlp_result.intent.primary_intent if nlp_result.intent else None,
                products_shown=[p.id for p in response.products] if response.products else []
            )

            # 8. 更新用户画像
            if user_profile:
                self._update_user_profile_from_interaction(
                    user_profile, user_input, response, nlp_result
                )

            # 9. 添加元数据
            response.response_time_ms = int((time.time() - start_time) * 1000)
            response.metadata.update({
                "session_id": session_id,
                "intent": nlp_result.intent.primary_intent.value if nlp_result.intent else None,
                "sentiment": sentiment_result.label.value if sentiment_result else None,
            })

            return response

        except Exception as e:
            # 错误处理
            return AssistantResponse(
                text=f"抱歉，处理您的请求时出现了一些问题。请稍后再试或换个方式描述您的需求。",
                confidence=0.0,
                metadata={"error": str(e)}
            )

    def _process_intent(
        self,
        nlp_result: SemanticUnderstandingResult,
        user_profile: Optional[UserProfile],
        sentiment_result: Optional[SentimentResult],
        response_tone: ResponseTone,
        session_id: str
    ) -> AssistantResponse:
        """处理用户意图"""
        intent = nlp_result.intent.primary_intent if nlp_result.intent else IntentType.GENERAL_QUERY

        # 根据意图类型处理
        if intent == IntentType.PRODUCT_SEARCH:
            return self._handle_product_search(
                nlp_result, user_profile, response_tone
            )
        elif intent == IntentType.RECOMMENDATION:
            return self._handle_recommendation_request(
                nlp_result, user_profile, response_tone
            )
        elif intent == IntentType.COMPARISON:
            return self._handle_comparison(
                nlp_result, user_profile
            )
        elif intent == IntentType.GREETING:
            return self._handle_greeting(user_profile)
        elif intent == IntentType.PRICE_INQUIRY:
            return self._handle_price_inquiry(nlp_result)
        else:
            return self._handle_general_query(nlp_result, session_id)

    def _handle_product_search(
        self,
        nlp_result: SemanticUnderstandingResult,
        user_profile: Optional[UserProfile],
        response_tone: ResponseTone
    ) -> AssistantResponse:
        """处理商品搜索"""
        slots = nlp_result.slots

        # 构建搜索条件
        criteria = SearchCriteria(
            keywords=slots.get("keywords"),
            category=slots.get("category"),
            brands=slots.get("brand"),
            min_price=slots.get("price", {}).get("min") if isinstance(slots.get("price"), dict) else None,
            max_price=slots.get("price", {}).get("max") if isinstance(slots.get("price"), dict) else None,
            features=slots.get("features"),
            color=slots.get("color")
        )

        # 如果没有明确条件，尝试从用户画像推断
        if user_profile and not criteria.keywords and not criteria.category:
            fav_categories = user_profile.preferences.get("favorite_categories", {}).get("value", [])
            if fav_categories:
                criteria.category = fav_categories[0]

        # 执行搜索
        results = self.product_db.search(criteria, limit=20)

        # 生成个性化推荐
        recommendations = self.recommendation_engine.recommend(
            user_profile=user_profile,
            criteria=criteria,
            limit=self.config.max_products_in_response
        )

        # 生成响应文本
        products = [r.product for r in recommendations]
        response_text = self._generate_product_listing(
            products, response_tone, criteria
        )

        # 生成建议操作
        suggested_actions = self._generate_suggested_actions(products, IntentType.PRODUCT_SEARCH)

        return AssistantResponse(
            text=response_text,
            products=products,
            suggested_actions=suggested_actions,
            is_personalized=user_profile is not None,
            confidence=nlp_result.confidence
        )

    def _handle_recommendation_request(
        self,
        nlp_result: SemanticUnderstandingResult,
        user_profile: Optional[UserProfile],
        response_tone: ResponseTone
    ) -> AssistantResponse:
        """处理推荐请求"""
        slots = nlp_result.slots

        # 构建搜索条件（可能包含在槽位中）
        criteria = SearchCriteria(
            category=slots.get("category"),
            brands=slots.get("brand"),
        )

        # 生成个性化推荐
        recommendations = self.recommendation_engine.recommend(
            user_profile=user_profile,
            criteria=criteria,
            limit=self.config.max_products_in_response
        )

        products = [r.product for r in recommendations]

        # 生成个性化响应
        if user_profile and user_profile.interaction_count > 0:
            greeting = f"根据您之前的偏好，我为您精选了以下推荐：\n\n"
        else:
            greeting = "根据您的需求，我为您推荐以下商品：\n\n"

        product_descriptions = []
        for i, rec in enumerate(recommendations, 1):
            desc = f"{i}. **{rec.product.name}** - ￥{rec.product.price}"
            if rec.product.rating >= 4.5:
                desc += f" ⭐{rec.product.rating}"
            if rec.reasons:
                desc += f"\n   💡 {rec.reasons[0]}"
            product_descriptions.append(desc)

        response_text = greeting + "\n\n".join(product_descriptions)

        if user_profile:
            response_text += "\n\n这些推荐是基于您的偏好生成的。想查看其他类型的商品吗？"

        suggested_actions = [
            SuggestedAction("view_details", "查看详情", "了解商品详细信息"),
            SuggestedAction("filter_price", "按价格筛选", "进一步筛选价格区间"),
            SuggestedAction("more_recommendations", "更多推荐", "查看更多推荐商品"),
        ]

        return AssistantResponse(
            text=response_text,
            products=products,
            suggested_actions=suggested_actions,
            is_personalized=user_profile is not None,
            confidence=nlp_result.confidence
        )

    def _handle_comparison(
        self,
        nlp_result: SemanticUnderstandingResult,
        user_profile: Optional[UserProfile]
    ) -> AssistantResponse:
        """处理商品对比请求"""
        slots = nlp_result.slots

        # 从输入中提取商品名称（简化实现）
        # 实际实现可能需要更复杂的实体提取
        product_names = slots.get("product_names", [])

        if len(product_names) < 2:
            return AssistantResponse(
                text="对比商品需要至少两款商品。请告诉我您想对比哪两款商品？",
                suggested_actions=[
                    SuggestedAction("search_products", "搜索商品", "先搜索想对比的商品")
                ]
            )

        # 查找商品
        products = []
        for name in product_names[:2]:
            product = self.product_db.get_by_name(name)
            if product:
                products.append(product)

        if len(products) < 2:
            return AssistantResponse(
                text="抱歉，我只找到了其中一款商品的信息。您可以尝试提供更准确的商品名称。"
            )

        # 生成对比表格
        comparison_text = self._generate_comparison_table(products[0], products[1])

        # 生成对比总结
        summary = self._generate_comparison_summary(products[0], products[1])

        response_text = f"这是**{products[0].name}**和**{products[1].name}**的详细对比：\n\n{comparison_text}\n\n{summary}"

        suggested_actions = [
            SuggestedAction("view_details", f"查看{products[0].name}详情", ""),
            SuggestedAction("view_details", f"查看{products[1].name}详情", ""),
            SuggestedAction("add_to_cart", "加入购物车", ""),
        ]

        return AssistantResponse(
            text=response_text,
            products=products,
            suggested_actions=suggested_actions,
            comparison_data={
                "product_a": products[0],
                "product_b": products[1],
                "recommendation": self._determine_winner(products[0], products[1])
            }
        )

    def _handle_greeting(self, user_profile: Optional[UserProfile]) -> AssistantResponse:
        """处理问候意图"""
        if user_profile and user_profile.interaction_count > 0:
            # 回访用户
            greeting = f"欢迎回来！很高兴再次为您服务。"

            # 根据历史推荐
            if user_profile.browse_history:
                recent_category = None
                for product_id in reversed(user_profile.browse_history[-5:]):
                    product = self.product_db.get_by_id(product_id)
                    if product:
                        recent_category = product.category
                        break

                if recent_category:
                    greeting += f"我们最近上了一些新的{recent_category}，您可能会感兴趣。"
        else:
            # 新用户
            greeting = """您好！我是您的智能购物助手，很高兴为您服务！

我可以帮您：
• 搜索和推荐商品
• 对比不同产品
• 解答购物相关问题
• 根据您的需求提供个性化建议

请问有什么可以帮您的吗？"""

        # 获取热门商品作为示例
        popular_products = self.product_db.get_popular_products(3)

        suggested_actions = [
            SuggestedAction("browse_categories", "浏览分类", "查看商品分类目录"),
            SuggestedAction("view_popular", "热门商品", "查看当前热销商品"),
            SuggestedAction("start_search", "搜索商品", "开始搜索特定商品"),
        ]

        return AssistantResponse(
            text=greeting,
            products=popular_products,
            suggested_actions=suggested_actions,
            is_personalized=user_profile is not None
        )

    def _handle_price_inquiry(self, nlp_result: SemanticUnderstandingResult) -> AssistantResponse:
        """处理价格查询"""
        slots = nlp_result.slots
        product_name = slots.get("product_name")

        if not product_name:
            # 询问用户想了解哪款商品的价格
            popular_products = self.product_db.get_popular_products(5)
            product_list = "\n".join([f"• {p.name} - ￥{p.price}" for p in popular_products])

            return AssistantResponse(
                text=f"请问您想了解哪款商品的价格？以下是一些热门商品：\n\n{product_list}\n\n请告诉我具体商品名称。",
                products=popular_products
            )

        # 查找商品
        product = self.product_db.get_by_name(product_name)

        if not product:
            return AssistantResponse(
                text=f'抱歉，没有找到"{product_name}"的价格信息。请检查商品名称是否正确，或者我可以帮您搜索类似商品。',
                suggested_actions=[
                    SuggestedAction("search_similar", "搜索类似商品", ""),
                    SuggestedAction("browse_categories", "浏览分类", "")
                ]
            )

        # 生成价格信息响应
        discount = product.get_discount()
        price_info = f"**{product.name}** 的价格信息：\n\n"
        price_info += f"💰 当前价格：￥{product.price}"

        if product.original_price:
            price_info += f" (原价 ￥{product.original_price})"
            if discount:
                price_info += f"\n🎉 优惠力度：{discount}%"

        price_info += f"\n⭐ 用户评分：{product.rating}/5.0 ({product.review_count}条评价)"

        if product.stock > 0:
            price_info += f"\n📦 库存状态：有货"
        else:
            price_info += f"\n📦 库存状态：暂时缺货"

        # 推荐相关商品
        similar_products = self.product_db.get_similar_products(product, limit=3)

        suggested_actions = [
            SuggestedAction("view_details", "查看详情", f"了解{product.name}的详细信息"),
            SuggestedAction("add_to_cart", "加入购物车", ""),
            SuggestedAction("compare_products", "对比商品", ""),
        ]

        return AssistantResponse(
            text=price_info,
            products=[product] + similar_products,
            suggested_actions=suggested_actions
        )

    def _handle_general_query(
        self,
        nlp_result: SemanticUnderstandingResult,
        session_id: str
    ) -> AssistantResponse:
        """处理一般查询"""
        user_input = nlp_result.raw_input

        # 获取对话历史以提供更连贯的响应
        history = self.conversation_manager.get_recent_history(session_id, 3)

        # 简单的通用响应生成
        response_text = self._generate_general_response(user_input, history)

        # 根据对话历史推荐可能感兴趣的内容
        suggested_actions = [
            SuggestedAction("popular_products", "热门商品", "查看当前热销商品"),
            SuggestedAction("categories", "商品分类", "浏览所有商品分类"),
            SuggestedAction("help", "帮助", "了解我能为您做什么"),
        ]

        return AssistantResponse(
            text=response_text,
            suggested_actions=suggested_actions,
            confidence=nlp_result.confidence
        )

    def _generate_general_response(
        self,
        user_input: str,
        history: List[ConversationTurn]
    ) -> str:
        """生成通用响应"""
        # 简单的关键词匹配来生成响应
        user_input_lower = user_input.lower()

        if any(word in user_input_lower for word in ["谢谢", "感谢", "thank"]):
            return "不客气！很高兴能帮到您。如果还有其他问题，随时告诉我。"

        if any(word in user_input_lower for word in ["再见", "bye", "拜拜"]):
            return "感谢您的咨询！祝您购物愉快，期待下次为您服务！"

        if any(word in user_input_lower for word in ["帮助", "help", "怎么用"]):
            return """我很乐意帮助您！我可以为您提供以下服务：

• 商品搜索和推荐
• 商品对比和评测
• 价格查询和优惠信息
• 购物流程指导

请直接告诉我您想了解什么，我会尽力帮助您！"""

        # 默认响应
        if history:
            return "我明白了。还有其他我可以帮您的吗？比如搜索特定商品、查看推荐或比较不同产品。"

        return """您好！我是您的智能购物助手，很高兴为您服务！

我可以帮您：
• 搜索商品和获取推荐
• 对比不同产品
• 查询价格和优惠信息
• 解答购物相关问题

请问今天有什么可以帮您的吗？"""

    def _determine_response_tone(
        self,
        nlp_result: SemanticUnderstandingResult,
        sentiment_result: Optional[SentimentResult]
    ) -> ResponseTone:
        """确定响应语气"""
        if sentiment_result:
            return self.sentiment_analyzer.get_recommended_tone(sentiment_result)

        if nlp_result.intent and nlp_result.intent.primary_intent == IntentType.GREETING:
            return ResponseTone.FRIENDLY

        return self.config.response_tone

    def _get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取对话历史"""
        turns = self.conversation_manager.get_recent_history(session_id, 10)
        return [
            {"user": t.user_input, "assistant": t.assistant_response}
            for t in turns
        ]

    def _update_user_profile_from_interaction(
        self,
        user_profile: UserProfile,
        user_input: str,
        response: AssistantResponse,
        nlp_result: SemanticUnderstandingResult
    ):
        """从交互中更新用户画像"""
        # 记录浏览历史
        for product in response.products:
            self.user_profile_manager.record_browse(user_profile.user_id, product.id)

        # 更新偏好
        slots = nlp_result.slots
        if "category" in slots:
            current_categories = user_profile.preferences.favorite_categories
            if slots["category"] not in current_categories:
                current_categories.append(slots["category"])
                self.user_profile_manager.update_preference(
                    user_profile.user_id,
                    "favorite_categories",
                    current_categories
                )

    # 辅助方法
    def _generate_product_listing(
        self,
        products: List[Product],
        tone: ResponseTone,
        criteria: SearchCriteria
    ) -> str:
        """生成商品列表展示"""
        if not products:
            return self._generate_no_results_response(criteria, tone)

        # 根据语气选择开场白
        if tone == ResponseTone.ENTHUSIASTIC:
            intro = "太棒了！我为您找到了一些超棒的商品！"
        elif tone == ResponseTone.EMPATHETIC:
            intro = "我理解您的需求，这些商品可能适合您："
        else:
            category = criteria.category or "商品"
            intro = f"根据您的需求，我找到以下{category}："

        # 生成商品列表
        product_descriptions = []
        for i, product in enumerate(products[:5], 1):
            desc = f"{i}. **{product.name}** - ￥{product.price}"
            if product.rating >= 4.5:
                desc += f" ⭐{product.rating}"
            if product.get_discount():
                desc += f" (省{product.get_discount()}%)"
            product_descriptions.append(desc)

        response = intro + "\n\n" + "\n\n".join(product_descriptions)

        if len(products) > 5:
            response += f"\n\n...还有 {len(products) - 5} 款类似商品。"

        response += "\n\n您想了解哪款商品的详细信息？或者您有其他需求吗？"

        return response

    def _generate_no_results_response(
        self,
        criteria: SearchCriteria,
        tone: ResponseTone
    ) -> str:
        """生成无结果时的响应"""
        if tone == ResponseTone.EMPATHETIC:
            base = "很抱歉没有找到完全符合您要求的商品。"
        else:
            base = "抱歉，没有找到符合条件的商品。"

        suggestions = []

        if criteria.min_price is not None and criteria.max_price is not None:
            suggestions.append(
                f"尝试扩大价格范围（当前：￥{criteria.min_price}-￥{criteria.max_price}）"
            )

        if criteria.brands:
            suggestions.append(f"尝试其他品牌（当前：{', '.join(criteria.brands)}）")

        if criteria.features:
            suggestions.append("减少一些非必需的功能要求")

        if not suggestions:
            suggestions.append("尝试使用更通用的关键词")
            suggestions.append("告诉我您的需求，我可以主动为您推荐")

        response = base + "\n\n您可以尝试以下方式：\n"
        response += "\n".join(f"• {s}" for s in suggestions)

        return response

    def _generate_suggested_actions(
        self,
        products: List[Product],
        intent: IntentType
    ) -> List[SuggestedAction]:
        """生成建议操作"""
        actions = []

        if intent == IntentType.PRODUCT_SEARCH:
            actions.extend([
                SuggestedAction("filter_by_price", "按价格筛选", "进一步筛选价格区间"),
                SuggestedAction("filter_by_brand", "按品牌筛选", "选择特定品牌"),
            ])

        if len(products) >= 2:
            actions.append(SuggestedAction("compare_products", "对比商品", "详细对比选中的商品"))

        actions.extend([
            SuggestedAction("view_details", "查看详情", "查看商品详细信息"),
            SuggestedAction("add_to_cart", "加入购物车", "将商品加入购物车"),
        ])

        return actions[:6]

    def _generate_comparison_table(
        self,
        product_a: Product,
        product_b: Product
    ) -> str:
        """生成对比表格"""
        rows = [
            f"| 维度 | {product_a.name} | {product_b.name} |",
            f"|------|{'-'*len(product_a.name)}|{'-'*len(product_b.name)}|",
            f"| 价格 | ￥{product_a.price} | ￥{product_b.price} |",
            f"| 品牌 | {product_a.brand} | {product_b.brand} |",
            f"| 评分 | {product_a.rating}/5 | {product_b.rating}/5 |",
        ]

        # 添加主要规格对比
        if product_a.specs and product_b.specs:
            for key in set(list(product_a.specs.keys())[:3] + list(product_b.specs.keys())[:3]):
                val_a = product_a.specs.get(key, "-")
                val_b = product_b.specs.get(key, "-")
                rows.append(f"| {key} | {val_a} | {val_b} |")

        return "\n".join(rows)

    def _generate_comparison_summary(
        self,
        product_a: Product,
        product_b: Product
    ) -> str:
        """生成对比总结"""
        differences = []

        # 价格比较
        if product_a.price < product_b.price:
            diff_percent = int((product_b.price - product_a.price) / product_b.price * 100)
            differences.append(f"**{product_a.name}**比**{product_b.name}**便宜约{diff_percent}%，更适合预算有限的用户。")
        elif product_b.price < product_a.price:
            diff_percent = int((product_a.price - product_b.price) / product_a.price * 100)
            differences.append(f"**{product_b.name}**比**{product_a.name}**便宜约{diff_percent}%，性价比更高。")

        # 评分比较
        if product_a.rating > product_b.rating:
            differences.append(f"**{product_a.name}**的用户评分更高，用户满意度更好。")
        elif product_b.rating > product_a.rating:
            differences.append(f"**{product_b.name}**的用户评分更高，口碑更好。")

        summary = "\n\n**购买建议**：\n"
        if differences:
            summary += "\n".join(f"• {d}" for d in differences)
        else:
            summary += "• 两款商品各有特色，建议您根据个人偏好选择。"

        # 添加行动号召
        winner = self._determine_winner(product_a, product_b)
        if winner:
            summary += f"\n\n综合来看，**{winner.name}**可能更适合大多数用户。您想了解更多详情吗？"

        return summary

    def _determine_winner(self, product_a: Product, product_b: Product) -> Optional[Product]:
        """确定胜出者"""
        score_a = 0
        score_b = 0

        # 价格评分（越低越好）
        if product_a.price < product_b.price:
            score_a += 1
        elif product_b.price < product_a.price:
            score_b += 1

        # 评分（越高越好）
        if product_a.rating > product_b.rating:
            score_a += 1
        elif product_b.rating > product_a.rating:
            score_b += 1

        if score_a > score_b:
            return product_a
        elif score_b > score_a:
            return product_b
        return None

    # 其他辅助方法...
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.conversation_manager.get_context_summary(session_id)

    def clear_user_session(self, session_id: str):
        """清除用户会话"""
        self.conversation_manager.clear_session(session_id)
