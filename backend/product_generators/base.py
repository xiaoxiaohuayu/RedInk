"""产品图生成器抽象基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class BackgroundType(str, Enum):
    """背景类型枚举"""
    PRESET = "preset"
    CUSTOM = "custom"
    DESCRIPTION = "description"
    ORIGINAL = "original"


class PlacementPosition(str, Enum):
    """商品位置枚举"""
    AUTO = "auto"
    LEFT_HAND = "left_hand"
    RIGHT_HAND = "right_hand"
    SHOULDER = "shoulder"
    CHEST = "chest"
    WAIST = "waist"


@dataclass
class BackgroundConfig:
    """背景配置"""
    type: str = "original"  # preset, custom, description, original
    preset: Optional[str] = None  # 街拍、室内、商场、户外、纯色
    custom_image: Optional[bytes] = None
    description: Optional[str] = None


@dataclass
class PlacementConfig:
    """商品位置配置"""
    position: str = "auto"  # auto, left_hand, right_hand, shoulder, chest, waist
    custom_instruction: Optional[str] = None


@dataclass
class ProductPhotoRequest:
    """产品图生成请求"""
    model_image: bytes
    product_images: List[bytes]
    prompt: str = ""
    aspect_ratio: str = "3:4"
    style: str = "自然"
    background: Optional[BackgroundConfig] = None
    placement: Optional[PlacementConfig] = None
    pose: Optional[str] = None
    variations: int = 1


    def __post_init__(self):
        """验证请求参数"""
        if not self.model_image:
            raise ValueError("模特图不能为空")
        if not self.product_images:
            raise ValueError("商品图不能为空")
        # 限制最大变体数量为4
        if self.variations > 4:
            self.variations = 4
        if self.variations < 1:
            self.variations = 1


@dataclass
class ProductPhotoResult:
    """产品图生成结果"""
    success: bool
    image_data: Optional[bytes] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProductPhotoGeneratorBase(ABC):
    """产品图生成器抽象基类"""

    # 供应商名称
    PROVIDER_NAME: str = "base"

    # 供应商支持的功能标志
    SUPPORTS_BACKGROUND_CHANGE: bool = False
    SUPPORTS_POSE_CHANGE: bool = False
    SUPPORTS_MULTI_PRODUCT: bool = False
    SUPPORTS_INPAINTING: bool = False

    def __init__(self, config: Dict[str, Any]):
        """
        初始化生成器

        Args:
            config: 配置字典
        """
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')

    @abstractmethod
    def generate(self, request: ProductPhotoRequest) -> ProductPhotoResult:
        """
        生成产品图

        Args:
            request: 产品图生成请求

        Returns:
            产品图生成结果
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            配置是否有效
        """
        pass

    def supports_feature(self, feature: str) -> bool:
        """
        检查是否支持某功能

        Args:
            feature: 功能名称

        Returns:
            是否支持该功能
        """
        feature_map = {
            'background_change': self.SUPPORTS_BACKGROUND_CHANGE,
            'pose_change': self.SUPPORTS_POSE_CHANGE,
            'multi_product': self.SUPPORTS_MULTI_PRODUCT,
            'inpainting': self.SUPPORTS_INPAINTING,
        }
        return feature_map.get(feature, False)

    def get_supported_features(self) -> Dict[str, bool]:
        """
        获取所有支持的功能

        Returns:
            功能支持情况字典
        """
        return {
            'background_change': self.SUPPORTS_BACKGROUND_CHANGE,
            'pose_change': self.SUPPORTS_POSE_CHANGE,
            'multi_product': self.SUPPORTS_MULTI_PRODUCT,
            'inpainting': self.SUPPORTS_INPAINTING,
        }

    def get_supported_aspect_ratios(self) -> List[str]:
        """
        获取支持的宽高比

        Returns:
            支持的宽高比列表
        """
        return self.config.get('supported_aspect_ratios', ['1:1', '3:4', '4:3', '16:9', '9:16'])

    def get_provider_info(self) -> Dict[str, Any]:
        """
        获取供应商信息

        Returns:
            供应商信息字典
        """
        return {
            'name': self.PROVIDER_NAME,
            'features': self.get_supported_features(),
            'aspect_ratios': self.get_supported_aspect_ratios(),
        }
