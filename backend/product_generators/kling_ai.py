"""Kling AI 产品图生成器

通过 Kling AI API 实现模特图与商品图的合成。
支持多种商品类型、背景变换、姿势调整等高级功能。
"""
import logging
import time
import random
import base64
from functools import wraps
from typing import Dict, Any, List, Optional
import requests

from .base import (
    ProductPhotoGeneratorBase,
    ProductPhotoRequest,
    ProductPhotoResult,
    BackgroundConfig,
    PlacementConfig,
)

logger = logging.getLogger(__name__)


def retry_on_error(max_retries: int = 3, base_delay: float = 2.0):
    """错误自动重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    
                    if "429" in error_str or "rate" in error_str.lower():
                        if attempt < max_retries - 1:
                            wait_time = (base_delay ** (attempt + 1)) + random.uniform(0, 1)
                            logger.warning(
                                f"遇到速率限制，{wait_time:.1f}秒后重试 "
                                f"(尝试 {attempt + 2}/{max_retries})"
                            )
                            time.sleep(wait_time)
                            continue
                    
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (attempt + 1)
                        logger.warning(
                            f"请求失败: {error_str[:100]}，{wait_time}秒后重试"
                        )
                        time.sleep(wait_time)
                        continue
                    raise
            
            raise last_error
        return wrapper
    return decorator


def encode_image_to_base64(image_data: bytes) -> str:
    """将图片数据编码为 base64 字符串"""
    return base64.b64encode(image_data).decode('utf-8')


def decode_base64_image(base64_str: str) -> bytes:
    """解码 base64 图片数据"""
    if base64_str.startswith('data:'):
        parts = base64_str.split(',', 1)
        if len(parts) == 2:
            base64_str = parts[1]
    return base64.b64decode(base64_str)


class KlingAIGenerator(ProductPhotoGeneratorBase):
    """
    Kling AI 产品图生成器
    
    通过 Kling AI API 实现高质量的产品图合成。
    支持多种商品类型、背景变换、姿势调整等功能。
    """
    
    PROVIDER_NAME = "kling_ai"
    
    # 功能支持标志 - Kling AI 支持丰富的功能
    SUPPORTS_BACKGROUND_CHANGE = True
    SUPPORTS_POSE_CHANGE = True
    SUPPORTS_MULTI_PRODUCT = True
    SUPPORTS_INPAINTING = False
    
    # 支持的质量等级
    SUPPORTED_QUALITY = ['standard', 'high', 'ultra']
    
    # 商品类型映射
    PRODUCT_TYPE_MAP = {
        'clothing': 'wear',
        'footwear': 'wear',
        'accessory': 'hold',
        'bag': 'hold',
        'watch': 'wear',
        'toy': 'hold',
        'default': 'auto',
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化生成器
        
        Args:
            config: 配置字典，包含:
                - api_key: API 密钥
                - base_url: API 基础 URL
                - model: 模型名称
                - quality: 质量等级 (standard, high, ultra)
        """
        super().__init__(config)
        
        logger.debug("初始化 KlingAIGenerator...")
        
        if not self.api_key:
            raise ValueError(
                "Kling AI API Key 未配置。\n"
                "解决方案：在 product_photo_providers.yaml 中配置 api_key"
            )
        
        if not self.base_url:
            raise ValueError(
                "Kling AI API Base URL 未配置。\n"
                "解决方案：在 product_photo_providers.yaml 中配置 base_url"
            )
        
        self.base_url = self.base_url.rstrip('/')
        self.model = config.get('model', 'kling-v1')
        self.quality = config.get('quality', 'high')
        
        if self.quality not in self.SUPPORTED_QUALITY:
            logger.warning(
                f"不支持的质量等级: {self.quality}，使用默认值 high"
            )
            self.quality = 'high'
        
        # 从配置中读取功能支持标志
        self.SUPPORTS_BACKGROUND_CHANGE = config.get(
            'supports_background_change', True
        )
        self.SUPPORTS_POSE_CHANGE = config.get(
            'supports_pose_change', True
        )
        self.SUPPORTS_MULTI_PRODUCT = config.get(
            'supports_multi_product', True
        )
        
        self.timeout = config.get('timeout', 180)
        
        logger.info(
            f"KlingAIGenerator 初始化完成: "
            f"base_url={self.base_url}, model={self.model}, quality={self.quality}"
        )
    
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        return bool(self.api_key and self.base_url and self.model)
    
    def generate(self, request: ProductPhotoRequest) -> ProductPhotoResult:
        """
        生成产品图
        
        Args:
            request: 产品图生成请求
            
        Returns:
            产品图生成结果
        """
        try:
            # 构建请求
            payload = self._build_payload(request)
            
            # 调用 API
            image_data = self._call_api(payload)
            
            return ProductPhotoResult(
                success=True,
                image_data=image_data,
                metadata={
                    'provider': self.PROVIDER_NAME,
                    'model': self.model,
                    'quality': self.quality,
                    'output_format': 'png',
                }
            )
            
        except ValueError as e:
            logger.error(f"输入验证失败: {e}")
            return ProductPhotoResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"产品图生成失败: {e}")
            return ProductPhotoResult(
                success=False,
                error=f"生成失败: {str(e)}"
            )
    
    def _build_payload(self, request: ProductPhotoRequest) -> Dict[str, Any]:
        """构建 API 请求载荷"""
        payload = {
            "model": self.model,
            "model_image": encode_image_to_base64(request.model_image),
            "product_images": [
                encode_image_to_base64(img) for img in request.product_images
            ],
            "quality": self.quality,
        }
        
        # 添加提示词
        prompt_parts = []
        if request.prompt:
            prompt_parts.append(request.prompt)
        
        # 添加风格
        if request.style and request.style != "自然":
            prompt_parts.append(f"{request.style}风格")
        
        if prompt_parts:
            payload["prompt"] = "，".join(prompt_parts)
        
        # 添加宽高比
        if request.aspect_ratio:
            payload["aspect_ratio"] = request.aspect_ratio
        
        # 添加背景配置
        if request.background:
            payload["background"] = self._build_background_config(request.background)
        
        # 添加位置配置
        if request.placement:
            payload["placement"] = self._build_placement_config(request.placement)
        
        # 添加姿势
        if request.pose:
            payload["pose"] = request.pose
        
        return payload
    
    def _build_background_config(self, bg: BackgroundConfig) -> Dict[str, Any]:
        """构建背景配置"""
        config = {"type": bg.type}
        
        if bg.type == "preset" and bg.preset:
            config["preset"] = bg.preset
        elif bg.type == "custom" and bg.custom_image:
            config["custom_image"] = encode_image_to_base64(bg.custom_image)
        elif bg.type == "description" and bg.description:
            config["description"] = bg.description
        
        return config
    
    def _build_placement_config(self, pl: PlacementConfig) -> Dict[str, Any]:
        """构建位置配置"""
        config = {"position": pl.position}
        
        if pl.custom_instruction:
            config["custom_instruction"] = pl.custom_instruction
        
        return config
    
    @retry_on_error(max_retries=3, base_delay=2.0)
    def _call_api(self, payload: Dict[str, Any]) -> bytes:
        """
        调用 Kling AI API
        
        Args:
            payload: 请求载荷
            
        Returns:
            生成的图片二进制数据
        """
        url = f"{self.base_url}/v1/images/product-photo"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"调用 Kling AI API: {url}")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            self._handle_api_error(response)
        
        result = response.json()
        return self._extract_image_from_response(result)
    
    def _handle_api_error(self, response: requests.Response) -> None:
        """处理 API 错误响应"""
        status_code = response.status_code
        error_detail = response.text[:500]
        
        if status_code == 401:
            raise ValueError(
                "Kling AI API Key 认证失败\n\n"
                "可能原因:\n"
                "1. API Key 无效或已过期\n"
                "2. API Key 格式错误\n\n"
                "解决方案: 检查 product_photo_providers.yaml 中的 api_key 配置"
            )
        elif status_code == 429:
            raise Exception(
                "API 配额或速率限制\n\n"
                "解决方案:\n"
                "1. 稍后再试\n"
                "2. 检查 API 配额使用情况"
            )
        elif status_code == 400:
            raise ValueError(
                f"请求参数错误\n\n"
                f"错误详情: {error_detail}\n\n"
                "可能原因:\n"
                "1. 图片格式不支持\n"
                "2. 图片尺寸不符合要求\n"
                "3. 参数配置错误"
            )
        else:
            raise Exception(
                f"API 请求失败 (状态码: {status_code})\n\n"
                f"错误详情: {error_detail}"
            )
    
    def _extract_image_from_response(self, result: Dict[str, Any]) -> bytes:
        """从 API 响应中提取图片数据"""
        # Kling AI API 响应格式
        if "data" in result and len(result["data"]) > 0:
            image_info = result["data"][0]
            
            if "b64_json" in image_info:
                return decode_base64_image(image_info["b64_json"])
            
            if "url" in image_info:
                return self._download_image(image_info["url"])
        
        # 备用格式
        if "image" in result:
            return decode_base64_image(result["image"])
        
        if "url" in result:
            return self._download_image(result["url"])
        
        if "output" in result:
            output = result["output"]
            if isinstance(output, str):
                if output.startswith('http'):
                    return self._download_image(output)
                return decode_base64_image(output)
            if isinstance(output, dict):
                if "url" in output:
                    return self._download_image(output["url"])
                if "image" in output:
                    return decode_base64_image(output["image"])
        
        raise ValueError(
            "无法从 API 响应中提取图片数据\n\n"
            f"响应内容: {str(result)[:500]}"
        )
    
    def _download_image(self, url: str) -> bytes:
        """下载图片"""
        logger.info(f"下载图片: {url[:100]}...")
        
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                logger.info(f"图片下载成功: {len(response.content)} bytes")
                return response.content
            else:
                raise Exception(f"下载图片失败: HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            raise Exception("下载图片超时，请重试")
        except Exception as e:
            raise Exception(f"下载图片失败: {str(e)}")

