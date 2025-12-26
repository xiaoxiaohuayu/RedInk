"""OpenAI 兼容接口产品图生成器

通过 Chat Completions API 实现模特图与商品图的合成。
支持 GPT-4o、GPT-4-vision 等多模态模型。
"""
import logging
import time
import random
import base64
import re
import io
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

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = {'png', 'jpg', 'jpeg', 'webp'}

# 图片格式的 MIME 类型映射
MIME_TYPE_MAP = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'webp': 'image/webp',
}


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
                    
                    # 检查是否是速率限制错误
                    if "429" in error_str or "rate" in error_str.lower():
                        if attempt < max_retries - 1:
                            wait_time = (base_delay ** (attempt + 1)) + random.uniform(0, 1)
                            logger.warning(
                                f"遇到速率限制，{wait_time:.1f}秒后重试 "
                                f"(尝试 {attempt + 2}/{max_retries})"
                            )
                            time.sleep(wait_time)
                            continue
                    
                    # 其他错误
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


def validate_image_format(image_data: bytes) -> str:
    """
    验证图片格式并返回格式名称
    
    Args:
        image_data: 图片二进制数据
        
    Returns:
        图片格式名称 (png, jpg, webp)
        
    Raises:
        ValueError: 不支持的图片格式
    """
    if len(image_data) < 12:
        raise ValueError("图片数据太小，无法识别格式")
    
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if image_data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    
    # JPEG: FF D8 FF
    if image_data[:3] == b'\xff\xd8\xff':
        return 'jpg'
    
    # WebP: RIFF....WEBP
    if image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
        return 'webp'
    
    raise ValueError(
        "不支持的图片格式。\n"
        f"支持的格式: {', '.join(SUPPORTED_IMAGE_FORMATS)}\n"
        "请上传 PNG、JPG 或 WEBP 格式的图片"
    )


def encode_image_to_base64(image_data: bytes) -> str:
    """将图片数据编码为 base64 字符串"""
    return base64.b64encode(image_data).decode('utf-8')


def decode_base64_image(base64_str: str) -> bytes:
    """
    解码 base64 图片数据
    
    支持格式:
    - 纯 base64 字符串
    - data:image/xxx;base64,xxx 格式
    """
    # 移除 data URL 前缀
    if base64_str.startswith('data:'):
        # 格式: data:image/png;base64,xxxxx
        parts = base64_str.split(',', 1)
        if len(parts) == 2:
            base64_str = parts[1]
    
    return base64.b64decode(base64_str)


class OpenAICompatibleProductGenerator(ProductPhotoGeneratorBase):
    """
    OpenAI 兼容接口产品图生成器
    
    通过多模态 Chat Completions API 实现模特图与商品图的合成。
    支持 GPT-4o、GPT-4-vision、Claude 等多模态模型。
    """
    
    PROVIDER_NAME = "openai_compatible"
    
    # 功能支持标志 - 从配置中读取，默认值如下
    SUPPORTS_BACKGROUND_CHANGE = True
    SUPPORTS_POSE_CHANGE = True
    SUPPORTS_MULTI_PRODUCT = True
    SUPPORTS_INPAINTING = False
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化生成器
        
        Args:
            config: 配置字典，包含:
                - api_key: API 密钥
                - base_url: API 基础 URL
                - model: 模型名称
                - supports_*: 功能支持标志
        """
        super().__init__(config)
        
        logger.debug("初始化 OpenAICompatibleProductGenerator...")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI 兼容 API Key 未配置。\n"
                "解决方案：在 product_photo_providers.yaml 中配置 api_key"
            )
        
        if not self.base_url:
            raise ValueError(
                "OpenAI 兼容 API Base URL 未配置。\n"
                "解决方案：在 product_photo_providers.yaml 中配置 base_url"
            )
        
        # 规范化 base_url
        self.base_url = self.base_url.rstrip('/')
        if self.base_url.endswith('/v1'):
            self.base_url = self.base_url[:-3]
        
        # 模型配置
        self.model = config.get('model', 'gpt-4o')
        
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
        self.SUPPORTS_INPAINTING = config.get(
            'supports_inpainting', False
        )
        
        # 请求超时配置
        self.timeout = config.get('timeout', 180)
        
        logger.info(
            f"OpenAICompatibleProductGenerator 初始化完成: "
            f"base_url={self.base_url}, model={self.model}"
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
            # 验证输入图片格式
            self._validate_input_images(request)
            
            # 构建提示词
            prompt = self._build_prompt(request)
            
            # 构建消息内容
            messages = self._build_messages(request, prompt)
            
            # 调用 API
            image_data = self._call_api(messages)
            
            # 验证输出格式
            output_format = validate_image_format(image_data)
            
            return ProductPhotoResult(
                success=True,
                image_data=image_data,
                metadata={
                    'provider': self.PROVIDER_NAME,
                    'model': self.model,
                    'output_format': output_format,
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
    
    def _validate_input_images(self, request: ProductPhotoRequest) -> None:
        """验证输入图片格式"""
        # 验证模特图
        try:
            model_format = validate_image_format(request.model_image)
            logger.debug(f"模特图格式: {model_format}")
        except ValueError as e:
            raise ValueError(f"模特图格式错误: {e}")
        
        # 验证商品图
        for i, product_image in enumerate(request.product_images):
            try:
                product_format = validate_image_format(product_image)
                logger.debug(f"商品图 {i+1} 格式: {product_format}")
            except ValueError as e:
                raise ValueError(f"商品图 {i+1} 格式错误: {e}")
    
    def _build_prompt(self, request: ProductPhotoRequest) -> str:
        """
        构建生成提示词
        
        根据请求参数构建详细的提示词，指导模型生成产品图。
        """
        parts = []
        
        # 基础指令
        parts.append(
            "你是一个专业的产品图合成助手。请将提供的商品图片自然地合成到模特图片中，"
            "生成一张专业的产品展示图。"
        )
        
        # 商品数量说明
        num_products = len(request.product_images)
        if num_products == 1:
            parts.append("我提供了1张商品图片，请将它合成到模特身上。")
        else:
            parts.append(f"我提供了{num_products}张商品图片，请将它们合成到模特身上。")
        
        # 用户自定义提示词
        if request.prompt:
            parts.append(f"额外要求: {request.prompt}")
        
        # 风格要求
        if request.style and request.style != "自然":
            parts.append(f"风格要求: {request.style}风格")
        
        # 背景设置
        if request.background:
            bg = request.background
            if bg.type == "preset" and bg.preset:
                parts.append(f"背景场景: {bg.preset}")
            elif bg.type == "description" and bg.description:
                parts.append(f"背景描述: {bg.description}")
            elif bg.type == "original":
                parts.append("保持原始背景不变")
        
        # 商品位置
        if request.placement:
            pl = request.placement
            position_names = {
                'auto': '自动选择最佳位置',
                'left_hand': '左手',
                'right_hand': '右手',
                'shoulder': '肩上',
                'chest': '胸前',
                'waist': '腰间',
            }
            position_desc = position_names.get(pl.position, pl.position)
            parts.append(f"商品位置: {position_desc}")
            
            if pl.custom_instruction:
                parts.append(f"位置调整: {pl.custom_instruction}")
        
        # 姿势要求
        if request.pose:
            parts.append(f"模特姿势: {request.pose}")
        
        # 输出要求
        parts.append(
            "请生成一张高质量的合成图片，确保商品与模特自然融合，"
            "光影一致，比例协调。直接返回生成的图片。"
        )
        
        return "\n".join(parts)
    
    def _build_messages(
        self,
        request: ProductPhotoRequest,
        prompt: str
    ) -> List[Dict[str, Any]]:
        """
        构建 API 消息内容
        
        将文本提示词和图片组合成多模态消息格式。
        """
        content = []
        
        # 添加文本提示词
        content.append({
            "type": "text",
            "text": prompt
        })
        
        # 添加模特图
        model_format = validate_image_format(request.model_image)
        model_base64 = encode_image_to_base64(request.model_image)
        mime_type = MIME_TYPE_MAP.get(model_format, 'image/png')
        
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{model_base64}",
                "detail": "high"
            }
        })
        
        # 添加商品图
        for i, product_image in enumerate(request.product_images):
            product_format = validate_image_format(product_image)
            product_base64 = encode_image_to_base64(product_image)
            mime_type = MIME_TYPE_MAP.get(product_format, 'image/png')
            
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{product_base64}",
                    "detail": "high"
                }
            })
        
        # 添加自定义背景图（如果有）
        if (request.background and 
            request.background.type == "custom" and 
            request.background.custom_image):
            bg_format = validate_image_format(request.background.custom_image)
            bg_base64 = encode_image_to_base64(request.background.custom_image)
            mime_type = MIME_TYPE_MAP.get(bg_format, 'image/png')
            
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{bg_base64}",
                    "detail": "high"
                }
            })
        
        return [
            {
                "role": "user",
                "content": content
            }
        ]
    
    @retry_on_error(max_retries=3, base_delay=2.0)
    def _call_api(self, messages: List[Dict[str, Any]]) -> bytes:
        """
        调用 Chat Completions API
        
        Args:
            messages: 消息列表
            
        Returns:
            生成的图片二进制数据
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 1.0
        }
        
        logger.info(f"调用 Chat API: {url}, model={self.model}")
        
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
                "API Key 认证失败\n\n"
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
                "2. 图片尺寸过大\n"
                "3. 模型不支持多模态输入"
            )
        else:
            raise Exception(
                f"API 请求失败 (状态码: {status_code})\n\n"
                f"错误详情: {error_detail}"
            )
    
    def _extract_image_from_response(self, result: Dict[str, Any]) -> bytes:
        """
        从 API 响应中提取图片数据
        
        支持多种返回格式:
        1. Markdown 图片链接: ![xxx](url)
        2. Base64 data URL: data:image/xxx;base64,xxx
        3. 纯图片 URL
        """
        if "choices" not in result or len(result["choices"]) == 0:
            raise ValueError(
                "API 未返回有效响应\n\n"
                f"响应内容: {str(result)[:500]}"
            )
        
        choice = result["choices"][0]
        if "message" not in choice or "content" not in choice["message"]:
            raise ValueError(
                "API 响应格式错误\n\n"
                f"响应内容: {str(choice)[:500]}"
            )
        
        content = choice["message"]["content"]
        
        if not isinstance(content, str):
            raise ValueError(
                "API 响应内容格式错误\n\n"
                f"内容类型: {type(content)}"
            )
        
        # 1. 尝试解析 Markdown 图片链接
        image_urls = self._extract_markdown_image_urls(content)
        if image_urls:
            logger.info(f"从 Markdown 提取到 {len(image_urls)} 张图片")
            return self._download_image(image_urls[0])
        
        # 2. 尝试解析 Base64 data URL
        if "data:image" in content:
            logger.info("检测到 Base64 图片数据")
            # 提取 data URL
            match = re.search(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', content)
            if match:
                data_url = match.group(0)
                return decode_base64_image(data_url)
        
        # 3. 尝试作为纯 URL 处理
        url_match = re.search(r'https?://[^\s\)\"\']+', content)
        if url_match:
            url = url_match.group(0)
            logger.info(f"检测到图片 URL: {url[:100]}")
            return self._download_image(url)
        
        raise ValueError(
            "无法从 API 响应中提取图片数据\n\n"
            f"响应内容: {content[:500]}\n\n"
            "可能原因:\n"
            "1. 该模型不支持图片生成\n"
            "2. 响应格式与预期不符\n"
            "3. 提示词被安全过滤"
        )
    
    def _extract_markdown_image_urls(self, content: str) -> List[str]:
        """从 Markdown 内容中提取图片 URL"""
        pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
        urls = re.findall(pattern, content)
        return urls
    
    def _download_image(self, url: str) -> bytes:
        """下载图片并返回二进制数据"""
        logger.info(f"下载图片: {url[:100]}...")
        
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                # 验证下载的内容是有效图片
                validate_image_format(response.content)
                logger.info(f"图片下载成功: {len(response.content)} bytes")
                return response.content
            else:
                raise Exception(f"下载图片失败: HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            raise Exception("下载图片超时，请重试")
        except ValueError as e:
            raise ValueError(f"下载的内容不是有效图片: {e}")
        except Exception as e:
            raise Exception(f"下载图片失败: {str(e)}")
