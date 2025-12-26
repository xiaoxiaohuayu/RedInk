"""产品图生成服务"""
import logging
import os
import uuid
import time
from typing import Dict, Any, Generator, List, Optional
from dataclasses import dataclass, field

from backend.config import Config
from backend.product_generators.factory import ProductPhotoGeneratorFactory
from backend.product_generators.base import (
    ProductPhotoRequest,
    ProductPhotoResult,
    BackgroundConfig,
    PlacementConfig,
)
from backend.utils.image_compressor import compress_image

logger = logging.getLogger(__name__)


@dataclass
class ProductPhotoTask:
    """产品图生成任务"""
    id: str
    status: str  # pending, generating, completed, failed
    provider: str
    model_image: bytes
    product_images: List[bytes]
    config: Dict[str, Any] = field(default_factory=dict)
    results: List[str] = field(default_factory=list)
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)


class ProductPhotoService:
    """产品图生成服务类"""

    # 自动重试次数
    AUTO_RETRY_COUNT = 3

    def __init__(self, provider_name: str = None):
        """
        初始化产品图生成服务

        Args:
            provider_name: 服务商名称，如果为None则使用配置文件中的激活服务商
        """
        logger.debug("初始化 ProductPhotoService...")

        # 获取服务商配置
        if provider_name is None:
            provider_name = Config.get_active_product_photo_provider()

        logger.info(f"使用产品图服务商: {provider_name}")
        provider_config = Config.get_product_photo_provider_config(provider_name)

        # 创建生成器实例
        provider_type = provider_config.get('type', provider_name)
        logger.debug(f"创建产品图生成器: type={provider_type}")
        self.generator = ProductPhotoGeneratorFactory.create(provider_type, provider_config)

        # 保存配置信息
        self.provider_name = provider_name
        self.provider_config = provider_config

        # 历史记录根目录
        self.history_root_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "history"
        )
        os.makedirs(self.history_root_dir, exist_ok=True)

        # 当前任务的输出目录
        self.current_task_dir = None

        # 存储任务状态（用于重试）
        self._task_states: Dict[str, ProductPhotoTask] = {}

        logger.info(f"ProductPhotoService 初始化完成: provider={provider_name}, type={provider_type}")

    def _generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        return f"product_{uuid.uuid4().hex[:8]}"

    def _save_image(self, image_data: bytes, filename: str, task_dir: str = None) -> str:
        """
        保存图片到本地，同时生成缩略图

        Args:
            image_data: 图片二进制数据
            filename: 文件名
            task_dir: 任务目录（如果为None则使用当前任务目录）

        Returns:
            保存的文件路径
        """
        if task_dir is None:
            task_dir = self.current_task_dir

        if task_dir is None:
            raise ValueError("任务目录未设置")

        # 保存原图
        filepath = os.path.join(task_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image_data)

        # 生成缩略图（50KB左右）
        thumbnail_data = compress_image(image_data, max_size_kb=50)
        thumbnail_filename = f"thumb_{filename}"
        thumbnail_path = os.path.join(task_dir, thumbnail_filename)
        with open(thumbnail_path, "wb") as f:
            f.write(thumbnail_data)

        return filepath


    def generate_product_photo(
        self,
        model_image: bytes,
        product_images: List[bytes],
        prompt: str = "",
        aspect_ratio: str = "3:4",
        style: str = "自然",
        background: Optional[Dict[str, Any]] = None,
        placement: Optional[Dict[str, Any]] = None,
        pose: Optional[str] = None,
        variations: int = 1,
        task_id: str = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        生成产品图（生成器，支持 SSE 流式返回）

        Args:
            model_image: 模特图二进制数据
            product_images: 商品图二进制数据列表
            prompt: 用户自定义提示词
            aspect_ratio: 宽高比
            style: 风格
            background: 背景配置
            placement: 商品位置配置
            pose: 姿势
            variations: 生成变体数量（最多4张）
            task_id: 任务ID（可选，如果不提供则自动生成）

        Yields:
            进度事件字典
        """
        if task_id is None:
            task_id = self._generate_task_id()

        logger.info(f"开始产品图生成任务: task_id={task_id}, variations={variations}")

        # 创建任务专属目录
        self.current_task_dir = os.path.join(self.history_root_dir, task_id)
        os.makedirs(self.current_task_dir, exist_ok=True)
        logger.debug(f"任务目录: {self.current_task_dir}")

        # 压缩图片以减少内存占用
        compressed_model_image = compress_image(model_image, max_size_kb=500)
        compressed_product_images = [
            compress_image(img, max_size_kb=500) for img in product_images
        ]

        # 构建背景配置
        bg_config = None
        if background:
            bg_config = BackgroundConfig(
                type=background.get('type', 'original'),
                preset=background.get('preset'),
                custom_image=background.get('custom_image'),
                description=background.get('description'),
            )

        # 构建位置配置
        pl_config = None
        if placement:
            pl_config = PlacementConfig(
                position=placement.get('position', 'auto'),
                custom_instruction=placement.get('custom_instruction'),
            )

        # 初始化任务状态
        task = ProductPhotoTask(
            id=task_id,
            status="pending",
            provider=self.provider_name,
            model_image=compressed_model_image,
            product_images=compressed_product_images,
            config={
                'prompt': prompt,
                'aspect_ratio': aspect_ratio,
                'style': style,
                'background': background,
                'placement': placement,
                'pose': pose,
                'variations': variations,
            }
        )
        self._task_states[task_id] = task

        # 限制变体数量
        variations = min(variations, 4)
        if variations < 1:
            variations = 1

        generated_images = []
        failed_count = 0

        # 发送任务开始事件
        yield {
            "event": "start",
            "data": {
                "task_id": task_id,
                "total": variations,
                "message": f"开始生成 {variations} 张产品图..."
            }
        }

        task.status = "generating"

        # 生成每个变体
        for i in range(variations):
            # 发送进度事件
            yield {
                "event": "progress",
                "data": {
                    "index": i,
                    "status": "generating",
                    "message": f"正在生成第 {i + 1}/{variations} 张图片...",
                    "current": i + 1,
                    "total": variations
                }
            }

            # 构建请求
            request = ProductPhotoRequest(
                model_image=compressed_model_image,
                product_images=compressed_product_images,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                style=style,
                background=bg_config,
                placement=pl_config,
                pose=pose,
                variations=1,  # 每次只生成一张
            )

            # 尝试生成（带重试）
            result = self._generate_with_retry(request)

            if result.success and result.image_data:
                # 保存图片
                filename = f"{i}.png"
                self._save_image(result.image_data, filename)
                generated_images.append(filename)
                task.results.append(filename)

                yield {
                    "event": "complete",
                    "data": {
                        "index": i,
                        "status": "done",
                        "image_url": f"/api/product-photo/images/{task_id}/{filename}",
                        "current": i + 1,
                        "total": variations
                    }
                }
            else:
                failed_count += 1
                error_msg = result.error or "未知错误"

                yield {
                    "event": "error",
                    "data": {
                        "index": i,
                        "status": "error",
                        "message": error_msg,
                        "retryable": True,
                        "current": i + 1,
                        "total": variations
                    }
                }

        # 更新任务状态
        if failed_count == 0:
            task.status = "completed"
        elif failed_count == variations:
            task.status = "failed"
        else:
            task.status = "partial"

        # 发送完成事件
        yield {
            "event": "finish",
            "data": {
                "success": failed_count == 0,
                "task_id": task_id,
                "images": [f"/api/product-photo/images/{task_id}/{f}" for f in generated_images],
                "total": variations,
                "completed": len(generated_images),
                "failed": failed_count
            }
        }


    def _generate_with_retry(
        self,
        request: ProductPhotoRequest,
        max_retries: int = None
    ) -> ProductPhotoResult:
        """
        带重试的生成方法

        Args:
            request: 生成请求
            max_retries: 最大重试次数

        Returns:
            生成结果
        """
        if max_retries is None:
            max_retries = self.AUTO_RETRY_COUNT

        last_error = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"生成尝试 {attempt + 1}/{max_retries}")
                result = self.generator.generate(request)

                if result.success:
                    return result

                # 生成失败但没有抛出异常
                last_error = result.error
                logger.warning(f"生成失败 (尝试 {attempt + 1}/{max_retries}): {last_error}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.debug(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

            except Exception as e:
                last_error = str(e)
                logger.warning(f"生成异常 (尝试 {attempt + 1}/{max_retries}): {last_error}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)

        return ProductPhotoResult(
            success=False,
            error=last_error or "超过最大重试次数"
        )

    def retry_generation(
        self,
        task_id: str,
        index: int = 0
    ) -> Generator[Dict[str, Any], None, None]:
        """
        重试生成失败的图片

        Args:
            task_id: 任务ID
            index: 要重试的图片索引

        Yields:
            进度事件字典
        """
        # 获取任务状态
        task = self._task_states.get(task_id)

        if task is None:
            yield {
                "event": "error",
                "data": {
                    "status": "error",
                    "message": f"任务不存在: {task_id}",
                    "retryable": False
                }
            }
            return

        logger.info(f"重试产品图生成: task_id={task_id}, index={index}")

        # 设置任务目录
        self.current_task_dir = os.path.join(self.history_root_dir, task_id)
        os.makedirs(self.current_task_dir, exist_ok=True)

        # 发送重试开始事件
        yield {
            "event": "retry_start",
            "data": {
                "task_id": task_id,
                "index": index,
                "message": f"开始重试第 {index + 1} 张图片..."
            }
        }

        # 从任务状态中获取配置
        config = task.config

        # 构建背景配置
        bg_config = None
        if config.get('background'):
            bg = config['background']
            bg_config = BackgroundConfig(
                type=bg.get('type', 'original'),
                preset=bg.get('preset'),
                custom_image=bg.get('custom_image'),
                description=bg.get('description'),
            )

        # 构建位置配置
        pl_config = None
        if config.get('placement'):
            pl = config['placement']
            pl_config = PlacementConfig(
                position=pl.get('position', 'auto'),
                custom_instruction=pl.get('custom_instruction'),
            )

        # 构建请求（复用已保存的图片数据）
        request = ProductPhotoRequest(
            model_image=task.model_image,
            product_images=task.product_images,
            prompt=config.get('prompt', ''),
            aspect_ratio=config.get('aspect_ratio', '3:4'),
            style=config.get('style', '自然'),
            background=bg_config,
            placement=pl_config,
            pose=config.get('pose'),
            variations=1,
        )

        # 发送进度事件
        yield {
            "event": "progress",
            "data": {
                "index": index,
                "status": "generating",
                "message": "正在重新生成..."
            }
        }

        # 尝试生成
        result = self._generate_with_retry(request)

        if result.success and result.image_data:
            # 保存图片
            filename = f"{index}.png"
            self._save_image(result.image_data, filename)

            # 更新任务结果
            if filename not in task.results:
                task.results.append(filename)

            # 检查是否所有图片都已生成
            expected_count = config.get('variations', 1)
            if len(task.results) >= expected_count:
                task.status = "completed"
            else:
                task.status = "partial"

            yield {
                "event": "complete",
                "data": {
                    "index": index,
                    "status": "done",
                    "image_url": f"/api/product-photo/images/{task_id}/{filename}"
                }
            }

            yield {
                "event": "retry_finish",
                "data": {
                    "success": True,
                    "task_id": task_id,
                    "index": index
                }
            }
        else:
            error_msg = result.error or "未知错误"
            task.error = error_msg

            yield {
                "event": "error",
                "data": {
                    "index": index,
                    "status": "error",
                    "message": error_msg,
                    "retryable": True
                }
            }

            yield {
                "event": "retry_finish",
                "data": {
                    "success": False,
                    "task_id": task_id,
                    "index": index,
                    "error": error_msg
                }
            }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典，如果任务不存在则返回None
        """
        task = self._task_states.get(task_id)

        if task is None:
            # 尝试从文件系统恢复任务状态
            task_dir = os.path.join(self.history_root_dir, task_id)
            if os.path.exists(task_dir):
                # 扫描已生成的图片
                images = []
                for filename in os.listdir(task_dir):
                    if filename.endswith('.png') and not filename.startswith('thumb_'):
                        images.append(filename)
                images.sort(key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 999)

                return {
                    "task_id": task_id,
                    "status": "completed" if images else "unknown",
                    "images": [f"/api/product-photo/images/{task_id}/{f}" for f in images],
                    "completed": len(images)
                }
            return None

        return {
            "task_id": task.id,
            "status": task.status,
            "provider": task.provider,
            "images": [f"/api/product-photo/images/{task_id}/{f}" for f in task.results],
            "completed": len(task.results),
            "total": task.config.get('variations', 1),
            "error": task.error
        }

    def get_image_path(self, task_id: str, filename: str) -> Optional[str]:
        """
        获取图片完整路径

        Args:
            task_id: 任务ID
            filename: 文件名

        Returns:
            完整路径，如果文件不存在则返回None
        """
        task_dir = os.path.join(self.history_root_dir, task_id)
        filepath = os.path.join(task_dir, filename)

        if os.path.exists(filepath):
            return filepath
        return None

    def cleanup_task(self, task_id: str) -> bool:
        """
        清理任务状态（释放内存）

        Args:
            task_id: 任务ID

        Returns:
            是否成功清理
        """
        if task_id in self._task_states:
            del self._task_states[task_id]
            logger.info(f"已清理任务状态: {task_id}")
            return True
        return False

    def get_providers(self) -> Dict[str, Any]:
        """
        获取所有可用的产品图生成供应商

        Returns:
            供应商信息字典
        """
        return ProductPhotoGeneratorFactory.get_available_providers()


# 全局服务实例
_service_instance = None


def get_product_photo_service(provider_name: str = None) -> ProductPhotoService:
    """
    获取产品图生成服务实例

    Args:
        provider_name: 服务商名称（可选）

    Returns:
        ProductPhotoService 实例
    """
    global _service_instance

    # 如果指定了服务商，创建新实例
    if provider_name is not None:
        return ProductPhotoService(provider_name)

    # 否则使用全局实例
    if _service_instance is None:
        _service_instance = ProductPhotoService()

    return _service_instance


def reset_product_photo_service():
    """重置全局服务实例（配置更新后调用）"""
    global _service_instance
    _service_instance = None
