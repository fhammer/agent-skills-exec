"""
用户画像管理器 - User Profile Manager

管理用户偏好、历史和画像信息。
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .types import UserProfile, UserPreference, InteractionSummary


class UserProfileManager:
    """用户画像管理器"""

    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化用户画像管理器

        Args:
            storage_path: 用户数据存储路径
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self._profiles: Dict[str, UserProfile] = {}
        self._load_all_profiles()

    def _load_all_profiles(self):
        """加载所有用户画像"""
        if not self.storage_path or not self.storage_path.exists():
            return

        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    profile = self._dict_to_profile(data)
                    self._profiles[profile.user_id] = profile
            except Exception as e:
                print(f"Error loading profile from {file_path}: {e}")

    def _save_profile(self, profile: UserProfile):
        """保存用户画像到文件"""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)
        file_path = self.storage_path / f"{profile.user_id}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._profile_to_dict(profile), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving profile: {e}")

    def _dict_to_profile(self, data: Dict[str, Any]) -> UserProfile:
        """将字典转换为UserProfile"""
        return UserProfile(
            user_id=data.get("user_id", ""),
            preferences=data.get("preferences", {}),
            browse_history=data.get("browse_history", []),
            purchase_history=data.get("purchase_history", []),
            interaction_count=data.get("interaction_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            last_active=datetime.fromisoformat(data["last_active"]) if "last_active" in data else datetime.now()
        )

    def _profile_to_dict(self, profile: UserProfile) -> Dict[str, Any]:
        """将UserProfile转换为字典"""
        return {
            "user_id": profile.user_id,
            "preferences": profile.preferences,
            "browse_history": profile.browse_history,
            "purchase_history": profile.purchase_history,
            "interaction_count": profile.interaction_count,
            "created_at": profile.created_at.isoformat(),
            "last_active": profile.last_active.isoformat() if profile.last_active else None
        }

    def get_profile(self, user_id: str, create_if_missing: bool = True) -> Optional[UserProfile]:
        """
        获取用户画像

        Args:
            user_id: 用户ID
            create_if_missing: 如果不存在是否创建新画像

        Returns:
            UserProfile对象或None
        """
        if user_id in self._profiles:
            return self._profiles[user_id]

        if create_if_missing:
            profile = UserProfile(user_id=user_id)
            self._profiles[user_id] = profile
            self._save_profile(profile)
            return profile

        return None

    def update_preference(self, user_id: str, key: str, value: Any, confidence: float = 1.0):
        """
        更新用户偏好

        Args:
            user_id: 用户ID
            key: 偏好键
            value: 偏好值
            confidence: 置信度
        """
        profile = self.get_profile(user_id)
        if not profile:
            return

        profile.preferences[key] = {
            "value": value,
            "confidence": confidence,
            "updated_at": datetime.now().isoformat()
        }
        profile.last_active = datetime.now()

        self._save_profile(profile)

    def record_browse(self, user_id: str, product_id: str):
        """记录浏览历史"""
        profile = self.get_profile(user_id)
        if not profile:
            return

        # 避免重复记录
        if product_id not in profile.browse_history:
            profile.browse_history.append(product_id)
            # 限制历史记录数量
            if len(profile.browse_history) > 100:
                profile.browse_history = profile.browse_history[-100:]

        profile.interaction_count += 1
        profile.last_active = datetime.now()

        self._save_profile(profile)

    def record_purchase(self, user_id: str, product_id: str):
        """记录购买历史"""
        profile = self.get_profile(user_id)
        if not profile:
            return

        if product_id not in profile.purchase_history:
            profile.purchase_history.append(product_id)

        profile.last_active = datetime.now()
        self._save_profile(profile)

    def get_favorite_categories(self, user_id: str, top_n: int = 3) -> List[str]:
        """获取用户最喜欢的类别"""
        profile = self.get_profile(user_id, create_if_missing=False)
        if not profile:
            return []

        # 从偏好中获取
        categories = profile.preferences.get("favorite_categories", {}).get("value", [])
        if isinstance(categories, list):
            return categories[:top_n]

        return []

    def get_preferred_price_range(self, user_id: str) -> Optional[tuple]:
        """获取用户偏好的价格范围"""
        profile = self.get_profile(user_id, create_if_missing=False)
        if not profile:
            return None

        price_range = profile.preferences.get("price_range", {}).get("value")
        if price_range and isinstance(price_range, (list, tuple)) and len(price_range) == 2:
            return tuple(price_range)

        return None
