"""产品图生成器工厂"""
from typing import Dict, Any, Type
from .base import ProductPhotoGeneratorBase


class ProductPhotoGeneratorFactory:
    """产品图生成器工厂类"""

    # 注册的生成器类型
    GENERATORS: Dict[str, Type[ProductPhotoGeneratorBase]] = {}

    @classmethod
    def register(cls, name: str, generator_class: Type[ProductPhotoGeneratorBase]) -> None:
        """
        注册生成器

        Args:
            name: 生成器名称
            generator_class: 生成器类

        Raises:
            TypeError: 如果生成器类不是 ProductPhotoGeneratorBase 的子类
        """
        if not issubclass(generator_class, ProductPhotoGeneratorBase):
            raise TypeError(
                f"注册失败：生成器类必须继承自 ProductPhotoGeneratorBase。\n"
                f"提供的类: {generator_class.__name__}\n"
                f"基类: ProductPhotoGeneratorBase"
            )
        cls.GENERATORS[name] = generator_class

    @classmethod
    def create(cls, provider: str, config: Dict[str, Any]) -> ProductPhotoGeneratorBase:
        """
        创建生成器实例

        Args:
            provider: 服务商类型
            config: 配置字典

        Returns:
            产品图生成器实例

        Raises:
            ValueError: 不支持的服务商类型
        """
        if provider not in cls.GENERATORS:
            available = ', '.join(cls.GENERATORS.keys()) if cls.GENERATORS else '无'
            raise ValueError(
                f"不支持的产品图生成供应商: {provider}\n"
                f"支持的供应商类型: {available}\n"
                "解决方案：\n"
                "1. 检查 product_photo_providers.yaml 中的 active_provider 配置\n"
                "2. 确认 provider.type 字段是否正确\n"
                "3. 确保对应的生成器已注册"
            )

        generator_class = cls.GENERATORS[provider]
        return generator_class(config)

    @classmethod
    def get_available_providers(cls) -> Dict[str, Dict[str, Any]]:
        """
        获取所有可用的供应商及其功能

        Returns:
            供应商信息字典
        """
        providers = {}
        for name, generator_class in cls.GENERATORS.items():
            providers[name] = {
                'name': name,
                'display_name': getattr(generator_class, 'PROVIDER_NAME', name),
                'features': {
                    'background_change': generator_class.SUPPORTS_BACKGROUND_CHANGE,
                    'pose_change': generator_class.SUPPORTS_POSE_CHANGE,
                    'multi_product': generator_class.SUPPORTS_MULTI_PRODUCT,
                    'inpainting': generator_class.SUPPORTS_INPAINTING,
                }
            }
        return providers

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        检查生成器是否已注册

        Args:
            name: 生成器名称

        Returns:
            是否已注册
        """
        return name in cls.GENERATORS

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        注销生成器

        Args:
            name: 生成器名称

        Returns:
            是否成功注销
        """
        if name in cls.GENERATORS:
            del cls.GENERATORS[name]
            return True
        return False
