"""模特模板管理服务"""
import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from backend.utils.image_compressor import compress_image

logger = logging.getLogger(__name__)


@dataclass
class TemplateInfo:
    """模板信息"""
    id: str
    name: str
    thumbnail_url: str
    created_at: str


class TemplateService:
    """模特模板管理服务"""

    def __init__(self):
        """初始化模板服务"""
        # 模板存储目录
        self.templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "templates"
        )
        os.makedirs(self.templates_dir, exist_ok=True)

        # 索引文件
        self.index_file = os.path.join(self.templates_dir, "index.json")
        self._init_index()

        logger.info(f"TemplateService 初始化完成: templates_dir={self.templates_dir}")

    def _init_index(self):
        """初始化索引文件"""
        if not os.path.exists(self.index_file):
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump({"templates": []}, f, ensure_ascii=False, indent=2)

    def _load_index(self) -> Dict:
        """加载索引"""
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"templates": []}

    def _save_index(self, index: Dict):
        """保存索引"""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _get_template_dir(self, template_id: str) -> str:
        """获取模板目录路径"""
        return os.path.join(self.templates_dir, template_id)

    def _get_image_path(self, template_id: str) -> str:
        """获取模板图片路径"""
        return os.path.join(self._get_template_dir(template_id), "image.png")

    def _get_thumbnail_path(self, template_id: str) -> str:
        """获取缩略图路径"""
        return os.path.join(self._get_template_dir(template_id), "thumbnail.png")

    def save_template(
        self,
        name: str,
        image: bytes,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        保存模板

        Args:
            name: 模板名称
            image: 图片二进制数据
            metadata: 可选的元数据

        Returns:
            模板ID
        """
        template_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        logger.info(f"保存模板: id={template_id}, name={name}")

        # 创建模板目录
        template_dir = self._get_template_dir(template_id)
        os.makedirs(template_dir, exist_ok=True)

        # 保存原图
        image_path = self._get_image_path(template_id)
        with open(image_path, "wb") as f:
            f.write(image)

        # 生成并保存缩略图
        thumbnail_data = compress_image(image, max_size_kb=50)
        thumbnail_path = self._get_thumbnail_path(template_id)
        with open(thumbnail_path, "wb") as f:
            f.write(thumbnail_data)

        # 更新索引
        index = self._load_index()
        template_entry = {
            "id": template_id,
            "name": name,
            "created_at": now,
            "metadata": metadata or {}
        }
        index["templates"].insert(0, template_entry)
        self._save_index(index)

        logger.info(f"模板保存成功: id={template_id}")
        return template_id

    def list_templates(self) -> List[TemplateInfo]:
        """
        列出所有模板

        Returns:
            模板信息列表
        """
        index = self._load_index()
        templates = []

        for entry in index.get("templates", []):
            template_id = entry["id"]
            # 验证模板文件存在
            if os.path.exists(self._get_image_path(template_id)):
                templates.append(TemplateInfo(
                    id=template_id,
                    name=entry["name"],
                    thumbnail_url=f"/api/templates/{template_id}/thumbnail",
                    created_at=entry["created_at"]
                ))

        return templates

    def get_template(self, template_id: str) -> Optional[bytes]:
        """
        获取模板图片

        Args:
            template_id: 模板ID

        Returns:
            图片二进制数据，如果不存在则返回None
        """
        image_path = self._get_image_path(template_id)

        if not os.path.exists(image_path):
            logger.warning(f"模板不存在: id={template_id}")
            return None

        with open(image_path, "rb") as f:
            return f.read()

    def get_template_thumbnail(self, template_id: str) -> Optional[bytes]:
        """
        获取模板缩略图

        Args:
            template_id: 模板ID

        Returns:
            缩略图二进制数据，如果不存在则返回None
        """
        thumbnail_path = self._get_thumbnail_path(template_id)

        if not os.path.exists(thumbnail_path):
            # 尝试返回原图
            return self.get_template(template_id)

        with open(thumbnail_path, "rb") as f:
            return f.read()

    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模板信息

        Args:
            template_id: 模板ID

        Returns:
            模板信息字典，如果不存在则返回None
        """
        index = self._load_index()

        for entry in index.get("templates", []):
            if entry["id"] == template_id:
                # 验证文件存在
                if os.path.exists(self._get_image_path(template_id)):
                    return entry
                break

        return None

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            是否删除成功
        """
        logger.info(f"删除模板: id={template_id}")

        # 检查模板是否存在
        index = self._load_index()
        template_exists = any(
            entry["id"] == template_id
            for entry in index.get("templates", [])
        )

        if not template_exists:
            logger.warning(f"模板不存在: id={template_id}")
            return False

        # 删除模板目录
        template_dir = self._get_template_dir(template_id)
        if os.path.exists(template_dir):
            try:
                import shutil
                shutil.rmtree(template_dir)
                logger.debug(f"已删除模板目录: {template_dir}")
            except Exception as e:
                logger.error(f"删除模板目录失败: {template_dir}, {e}")
                return False

        # 更新索引
        index["templates"] = [
            entry for entry in index["templates"]
            if entry["id"] != template_id
        ]
        self._save_index(index)

        logger.info(f"模板删除成功: id={template_id}")
        return True

    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        更新模板信息

        Args:
            template_id: 模板ID
            name: 新名称（可选）
            metadata: 新元数据（可选）

        Returns:
            是否更新成功
        """
        logger.info(f"更新模板: id={template_id}, name={name}")

        index = self._load_index()

        for entry in index.get("templates", []):
            if entry["id"] == template_id:
                # 验证文件存在
                if not os.path.exists(self._get_image_path(template_id)):
                    logger.warning(f"模板文件不存在: id={template_id}")
                    return False

                # 更新字段
                if name is not None:
                    entry["name"] = name
                if metadata is not None:
                    entry["metadata"] = metadata

                self._save_index(index)
                logger.info(f"模板更新成功: id={template_id}")
                return True

        logger.warning(f"模板不存在: id={template_id}")
        return False


# 全局服务实例
_service_instance = None


def get_template_service() -> TemplateService:
    """
    获取模板服务实例

    Returns:
        TemplateService 实例
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = TemplateService()
    return _service_instance


def reset_template_service():
    """重置全局服务实例"""
    global _service_instance
    _service_instance = None
