"""Stable Diffusion Inpainting 产品图生成器

通过 Stable Diffusion Inpainting API 实现模特图与商品图的合成。
支持精确的局部编辑和背景替换功能。
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
    BackgroundConfig,
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


class StableDiffusionGenerator(ProductPhotoGeneratorBase):
    """
    Stable Diffusion Inpainting 产品图生成器
    
    通过 Stable Diffusion Inpainting API 实现精确的图片编辑。
    支持背景替换、局部修改等功能。
    """
    
    PROVIDER_NAME = "stable_diffusion"
    
    # 功能支持标志 - SD Inpainting 专注于局部编辑
    SUPPORTS_BACKGROUND_CHANGE = True
    SUPPORTS_POSE_CHANGE = False
    SUPPORTS_MULTI_PRODUCT = False
    SUPPORTS_INPAINTING = True
    
    # 默认生成参数
    DEFAULT_CFG_SCALE = 7
    DEFAULT_STEPS = 30
    DEFAULT_SAMPLER = "K_EULER_ANCESTRAL"
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化生成器
        
        Args:
            config: 配置字典，包含:
                - api_key: API 密钥
                - base_url: API 基础 URL
                - model: 模型名称
                - cfg_scale: CFG 引导强度
                - steps: 采样步数
                - sampler: 采样器
        """
        super().__init__(config)
        
        logger.debug("初始化 StableDiffusionGenerator...")
        
        if not self.api_key:
            raise ValueError(
                "Stable Diffusion API Key 未配置。\n"
                "解决方案：在 product_photo_providers.yaml 中配置 api_key"
            )
        
        if not self.base_url:
            raise ValueError(
                "Stable Diffusion API Base URL 未配置。\n"
                "解决方案：在 product_photo_providers.yaml 中配置 base_url"
            )
        
        self.base_url = self.base_url.rstrip('/')
        self.model = config.get('model', 'stable-diffusion-xl-1024-v1-0')
        
        # 生成参数
        self.cfg_scale = config.get('cfg_scale', self.DEFAULT_CFG_SCALE)
        self.steps = config.get('steps', self.DEFAULT_STEPS)
        self.sampler = config.get('sampler', self.DEFAULT_SAMPLER)
        
        # 从配置中读取功能支持标志
        self.SUPPORTS_BACKGROUND_CHANGE = config.get(
            'supports_background_change', True
        )
        self.SUPPORTS_INPAINTING = config.get(
            'supports_inpainting', True
        )
        
        self.timeout = config.get('timeout', 180)
        
        logger.info(
            f"StableDiffusionGenerator 初始化完成: "
            f"base_url={self.base_url}, model={self.model}, "
            f"cfg_scale={self.cfg_scale}, steps={self.steps}"
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
            # SD Inpainting 一次只处理一张商品图
            if len(request.product_images) > 1:
                logger.warning(
                    f"Stable Diffusion Inpainting 一次只支持一张商品图，将使用第一张。"
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
                    'cfg_scale': self.cfg_scale,
                    'steps': self.steps,
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
        # 构建提示词
        prompt = self._build_prompt(request)
        
        payload = {
            "init_image": encode_image_to_base64(request.model_image),
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1.0
                }
            ],
            "cfg_scale": self.cfg_scale,
            "steps": self.steps,
            "sampler": self.sampler,
        }
        
        # 添加商品图作为参考
        if request.product_images:
            payload["style_image"] = encode_image_to_base64(request.product_images[0])
        
        # 添加宽高比对应的尺寸
        width, height = self._parse_aspect_ratio(request.aspect_ratio)
        payload["width"] = width
        payload["height"] = height
        
        return payload
    
    def _build_prompt(self, request: ProductPhotoRequest) -> str:
        """构建生成提示词"""
        parts = []
        
        # 基础描述
        parts.append("professional product photography")
        parts.append("model wearing or holding product")
        parts.append("high quality")
        parts.append("detailed")
        
        # 用户提示词
        if request.prompt:
            parts.append(request.prompt)
        
        # 风格
        if request.style and request.style != "自然":
            style_map = {
                "简约": "minimalist style",
                "时尚": "fashion style",
                "复古": "vintage style",
                "街头": "street style",
                "高端": "luxury high-end style",
            }
            style_en = style_map.get(request.style, request.style)
            parts.append(style_en)
        
        # 背景
        if request.background:
            bg = request.background
            if bg.type == "preset" and bg.preset:
                bg_map = {
                    "街拍": "street photography background",
                    "室内": "indoor studio background",
                    "商场": "shopping mall background",
                    "户外": "outdoor natural background",
                    "纯色": "solid color background",
                }
                bg_en = bg_map.get(bg.preset, bg.preset)
                parts.append(bg_en)
            elif bg.type == "description" and bg.description:
                parts.append(f"background: {bg.description}")
        
        # 位置
        if request.placement:
            pl = request.placement
            position_map = {
                "left_hand": "product in left hand",
                "right_hand": "product in right hand",
                "shoulder": "product on shoulder",
                "chest": "product on chest",
                "waist": "product at waist",
            }
            if pl.position in position_map:
                parts.append(position_map[pl.position])
            if pl.custom_instruction:
                parts.append(pl.custom_instruction)
        
        return ", ".join(parts)
    
    def _parse_aspect_ratio(self, aspect_ratio: str) -> tuple:
        """解析宽高比并返回对应的尺寸"""
        ratio_map = {
            "1:1": (1024, 1024),
            "3:4": (768, 1024),
            "4:3": (1024, 768),
            "16:9": (1024, 576),
            "9:16": (576, 1024),
        }
        return ratio_map.get(aspect_ratio, (768, 1024))
    
    @retry_on_error(max_retries=3, base_delay=2.0)
    def _call_api(self, payload: Dict[str, Any]) -> bytes:
        """
        调用 Stable Diffusion API
        
        Args:
            payload: 请求载荷
            
        Returns:
            生成的图片二进制数据
        """
        url = f"{self.base_url}/v1/generation/{self.model}/image-to-image"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        logger.info(f"调用 Stable Diffusion API: {url}")
        
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
                "Stable Diffusion API Key 认证失败\n\n"
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
                "3. 提示词被安全过滤"
            )
        else:
            raise Exception(
                f"API 请求失败 (状态码: {status_code})\n\n"
                f"错误详情: {error_detail}"
            )
    
    def _extract_image_from_response(self, result: Dict[str, Any]) -> bytes:
        """从 API 响应中提取图片数据"""
        # Stability AI API 响应格式
        if "artifacts" in result and len(result["artifacts"]) > 0:
            artifact = result["artifacts"][0]
            
            if "base64" in artifact:
                return decode_base64_image(artifact["base64"])
            
            if "url" in artifact:
                return self._download_image(artifact["url"])
        
        # 备用格式
        if "images" in result and len(result["images"]) > 0:
            image_data = result["images"][0]
            if isinstance(image_data, str):
                return decode_base64_image(image_data)
            if isinstance(image_data, dict):
                if "base64" in image_data:
                    return decode_base64_image(image_data["base64"])
                if "url" in image_data:
                    return self._download_image(image_data["url"])
        
        if "image" in result:
            return decode_base64_image(result["image"])
        
        if "output" in result:
            output = result["output"]
            if isinstance(output, str):
                if output.startswith('http'):
                    return self._download_image(output)
                return decode_base64_image(output)
        
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
    
    def inpaint(
        self,
        image: bytes,
        mask: bytes,
        prompt: str,
        negative_prompt: str = ""
    ) -> ProductPhotoResult:
        """
        执行 Inpainting 操作
        
        Args:
            image: 原始图片
            mask: 蒙版图片（白色区域将被修改）
            prompt: 生成提示词
            negative_prompt: 负面提示词
            
        Returns:
            生成结果
        """
        try:
            payload = {
                "init_image": encode_image_to_base64(image),
                "mask_image": encode_image_to_base64(mask),
                "text_prompts": [
                    {"text": prompt, "weight": 1.0}
                ],
                "cfg_scale": self.cfg_scale,
                "steps": self.steps,
                "sampler": self.sampler,
            }
            
            if negative_prompt:
                payload["text_prompts"].append({
                    "text": negative_prompt,
                    "weight": -1.0
                })
            
            image_data = self._call_inpaint_api(payload)
            
            return ProductPhotoResult(
                success=True,
                image_data=image_data,
                metadata={
                    'provider': self.PROVIDER_NAME,
                    'model': self.model,
                    'operation': 'inpaint',
                    'output_format': 'png',
                }
            )
            
        except Exception as e:
            logger.error(f"Inpainting 失败: {e}")
            return ProductPhotoResult(
                success=False,
                error=f"Inpainting 失败: {str(e)}"
            )
    
    @retry_on_error(max_retries=3, base_delay=2.0)
    def _call_inpaint_api(self, payload: Dict[str, Any]) -> bytes:
        """调用 Inpainting API"""
        url = f"{self.base_url}/v1/generation/{self.model}/image-to-image/masking"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        logger.info(f"调用 Stable Diffusion Inpainting API: {url}")
        
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

