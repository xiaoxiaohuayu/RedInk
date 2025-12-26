"""产品图生成器模块"""

from .base import (
    ProductPhotoGeneratorBase,
    ProductPhotoRequest,
    ProductPhotoResult,
    BackgroundConfig,
    PlacementConfig,
)
from .factory import ProductPhotoGeneratorFactory
from .openai_compatible import OpenAICompatibleProductGenerator
from .kolors_virtual_tryon import KolorsVirtualTryonGenerator
from .kling_ai import KlingAIGenerator
from .stable_diffusion import StableDiffusionGenerator

# 注册生成器
ProductPhotoGeneratorFactory.register(
    'openai_compatible',
    OpenAICompatibleProductGenerator
)
ProductPhotoGeneratorFactory.register(
    'kolors_virtual_tryon',
    KolorsVirtualTryonGenerator
)
ProductPhotoGeneratorFactory.register(
    'kling_ai',
    KlingAIGenerator
)
ProductPhotoGeneratorFactory.register(
    'stable_diffusion',
    StableDiffusionGenerator
)

__all__ = [
    'ProductPhotoGeneratorBase',
    'ProductPhotoRequest',
    'ProductPhotoResult',
    'BackgroundConfig',
    'PlacementConfig',
    'ProductPhotoGeneratorFactory',
    'OpenAICompatibleProductGenerator',
    'KolorsVirtualTryonGenerator',
    'KlingAIGenerator',
    'StableDiffusionGenerator',
]
