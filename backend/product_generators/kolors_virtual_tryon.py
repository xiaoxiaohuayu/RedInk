"""可灵虚拟换装 API 产品图生成器

通过可灵 (Kolors) Virtual Try-on API 实现模特图与服装图的合成。
专注于服装换装场景，支持上半身、下半身和全身换装。
"""
import logging
import time
import random
import base64
from functools import wraps
from typing import Dict, Any, Optional
import requests

from .base import (
    ProductPhotoGeneratorBase,
    ProductPhotoRequest,
    ProductPhotoResult,
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


class KolorsVirtualTryonGenerator(ProductPhotoGeneratorBase):
    """
    可灵虚拟换装生成器
    
    通过可灵 Virtual Try-on API 实现服装换装。
    支持上半身、下半身和全身换装模式。
    """
    
    PROVIDER_NAME = "kolors_virtual_tryon"
    
    # 功能支持标志 - 可灵换装专注于服装，不支持背景和姿势变换
    SUPPORTS_BACKGROUND_CHANGE = False
    SUPPORTS_POSE_CHANGE = False
    SUPPORTS_MULTI_PRODUCT = False  # 一次只能换一件
    SUPPORTS_INPAINTING = False
    
    # 支持的换装类别
    SUPPORTED_CATEGORIES = ['upper_body', 'lower_body', 'full_body']
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化生成器
        
        Args:
            config: 配置字典，包含:
                - api_key: API 密钥
                - base_url: API 基础 URL
                - model: 模型名称
                - category: 换装类别 (upper_body, lower_body, full_body)
        """
        super().__init__(config)
        
        logger.debug("初始化 KolorsVirtualTryonGenerator...")
        
        if not self.api_key:
            raise ValueError(
                "可灵 API Key 未配置。\n"
                "解决方案：在 product_photo_providers.yaml 中配置 api_key"
            )
        
        if not self.base_url:
            raise ValueError(
                "可灵 API Base URL 未配置。\n"
                "解决方案：在 product_photo_providers.yaml 中配置 base_url"
            )
        
        self.base_url = self.base_url.rstrip('/')
        self.model = config.get('model', 'kolors-virtual-try-on')
        self.category = config.get('category', 'upper_body')
        
        if self.category not in self.SUPPORTED_CATEGORIES:
            logger.warning(
                f"不支持的换装类别: {self.category}，使用默认值 upper_body"
            )
            self.category = 'upper_body'
        
        self.timeout = config.get('timeout', 180)
        
        logger.info(
            f"KolorsVirtualTryonGenerator 初始化完成: "
            f"base_url={self.base_url}, model={self.model}, category={self.category}"
        )
    
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        return bool(self.api_key and self.base_url and self.model)
    
    def generate(self, request: ProductPhotoRequest) -> ProductPhotoResult:
        """
        生成换装图
        
        Args:
            request: 产品图生成请求
            
        Returns:
            产品图生成结果
        """
        try:
            # 可灵换装只支持单件服装
            if len(request.product_images) > 1:
                logger.warning(
                    f"可灵换装只支持单件服装，将使用第一张商品图。"
                    f"提供了 {len(request.product_images)} 张图片"
                )
            
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
                    'category': self.category,
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
            logger.error(f"换装生成失败: {e}")
            return ProductPhotoResult(
                success=False,
                error=f"生成失败: {str(e)}"
            )
    
    def _build_payload(self, request: ProductPhotoRequest) -> Dict[str, Any]:
        """构建 API 请求载荷"""
        payload = {
            "model": self.model,
            "human_image": encode_image_to_base64(request.model_image),
            "cloth_image": encode_image_to_base64(request.product_images[0]),
            "category": self.category,
        }
        
        # 添加可选参数
        if request.prompt:
            payload["prompt"] = request.prompt
        
        return payload
    
    @retry_on_error(max_retries=3, base_delay=2.0)
    def _call_api(self, payload: Dict[str, Any]) -> bytes:
        """
        调用可灵换装 API
        
        Args:
            payload: 请求载荷
            
        Returns:
            生成的图片二进制数据
        """
        url = f"{self.base_url}/v1/images/kolors-virtual-try-on"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"调用可灵换装 API: {url}")
        
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
                "可灵 API Key 认证失败\n\n"
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
                "3. 服装类别与图片不匹配"
            )
        else:
            raise Exception(
                f"API 请求失败 (状态码: {status_code})\n\n"
                f"错误详情: {error_detail}"
            )
    
    def _extract_image_from_response(self, result: Dict[str, Any]) -> bytes:
        """从 API 响应中提取图片数据"""
        # 可灵 API 响应格式
        if "data" in result and len(result["data"]) > 0:
            image_info = result["data"][0]
            
            # 尝试获取 base64 数据
            if "b64_json" in image_info:
                return decode_base64_image(image_info["b64_json"])
            
            # 尝试获取 URL
            if "url" in image_info:
                return self._download_image(image_info["url"])
        
        # 备用格式
        if "image" in result:
            return decode_base64_image(result["image"])
        
        if "url" in result:
            return self._download_image(result["url"])
        
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

