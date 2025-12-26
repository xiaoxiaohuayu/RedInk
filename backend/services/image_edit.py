"""图片编辑服务"""
import os
import json
import uuid
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class EditSession:
    """编辑会话"""
    id: str
    task_id: str
    image_index: int
    original_image_path: str
    current_image_path: str
    history: List[str] = field(default_factory=list)  # 历史图片路径列表
    history_index: int = 0  # 当前在历史中的位置
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ImageEditService:
    """图片编辑服务"""

    MAX_HISTORY_STEPS = 10

    def __init__(self):
        """初始化编辑服务"""
        # 编辑会话存储目录
        self.edit_sessions_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "edit_sessions"
        )
        os.makedirs(self.edit_sessions_dir, exist_ok=True)

        # 历史记录根目录（用于读取原始图片）
        self.history_root_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "history"
        )

        # 内存中的会话缓存
        self._sessions: Dict[str, EditSession] = {}

        logger.info(f"ImageEditService 初始化完成: edit_sessions_dir={self.edit_sessions_dir}")

    def _get_session_dir(self, session_id: str) -> str:
        """获取会话目录路径"""
        return os.path.join(self.edit_sessions_dir, session_id)

    def _get_session_meta_path(self, session_id: str) -> str:
        """获取会话元数据文件路径"""
        return os.path.join(self._get_session_dir(session_id), "meta.json")

    def _save_session_meta(self, session: EditSession):
        """保存会话元数据"""
        meta_path = self._get_session_meta_path(session.id)
        session.updated_at = datetime.now().isoformat()
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(asdict(session), f, ensure_ascii=False, indent=2)

    def _load_session_meta(self, session_id: str) -> Optional[EditSession]:
        """加载会话元数据"""
        meta_path = self._get_session_meta_path(session_id)
        if not os.path.exists(meta_path):
            return None
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return EditSession(**data)
        except Exception as e:
            logger.error(f"加载会话元数据失败: {session_id}, {e}")
            return None

    def _get_session(self, session_id: str) -> Optional[EditSession]:
        """获取会话（优先从缓存获取）"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        session = self._load_session_meta(session_id)
        if session:
            self._sessions[session_id] = session
        return session

    def create_edit_session(
        self,
        task_id: str,
        image_index: int = 0
    ) -> Optional[str]:
        """
        创建编辑会话

        Args:
            task_id: 产品图生成任务ID
            image_index: 要编辑的图片索引

        Returns:
            会话ID，如果创建失败则返回None
        """
        logger.info(f"创建编辑会话: task_id={task_id}, image_index={image_index}")

        # 查找原始图片
        task_dir = os.path.join(self.history_root_dir, task_id)
        if not os.path.exists(task_dir):
            logger.error(f"任务目录不存在: {task_dir}")
            return None

        # 查找图片文件
        image_filename = f"{image_index}.png"
        original_image_path = os.path.join(task_dir, image_filename)

        if not os.path.exists(original_image_path):
            logger.error(f"图片不存在: {original_image_path}")
            return None

        # 生成会话ID
        session_id = str(uuid.uuid4())

        # 创建会话目录
        session_dir = self._get_session_dir(session_id)
        os.makedirs(session_dir, exist_ok=True)

        # 复制原始图片到会话目录
        session_original_path = os.path.join(session_dir, "original.png")
        shutil.copy2(original_image_path, session_original_path)

        # 创建当前编辑图片（初始为原始图片的副本）
        current_image_path = os.path.join(session_dir, "current.png")
        shutil.copy2(original_image_path, current_image_path)

        # 创建会话对象
        session = EditSession(
            id=session_id,
            task_id=task_id,
            image_index=image_index,
            original_image_path=session_original_path,
            current_image_path=current_image_path,
            history=[session_original_path],  # 初始历史包含原始图片
            history_index=0,
        )

        # 保存会话
        self._sessions[session_id] = session
        self._save_session_meta(session)

        logger.info(f"编辑会话创建成功: session_id={session_id}")
        return session_id

    def apply_edit(
        self,
        session_id: str,
        instruction: str,
        mask: Optional[bytes] = None
    ) -> Optional[bytes]:
        """
        应用编辑指令

        Args:
            session_id: 会话ID
            instruction: 编辑指令（如 "把包包往左移一点", "调亮一些"）
            mask: 可选的蒙版数据（用于局部编辑）

        Returns:
            编辑后的图片数据，如果失败则返回None
        """
        session = self._get_session(session_id)
        if session is None:
            logger.error(f"会话不存在: {session_id}")
            return None

        logger.info(f"应用编辑: session_id={session_id}, instruction={instruction}")

        # 读取当前图片
        if not os.path.exists(session.current_image_path):
            logger.error(f"当前图片不存在: {session.current_image_path}")
            return None

        with open(session.current_image_path, "rb") as f:
            current_image_data = f.read()

        # TODO: 调用 AI 编辑 API 进行实际编辑
        # 目前返回原图作为占位实现
        # 实际实现需要：
        # 1. 解析 instruction 确定编辑类型
        # 2. 如果有 mask，应用局部编辑
        # 3. 调用相应的 AI API 进行编辑
        edited_image_data = current_image_data

        # 保存编辑后的图片
        # 如果当前不在历史末尾，需要截断后续历史
        if session.history_index < len(session.history) - 1:
            # 删除后续历史文件
            for i in range(session.history_index + 1, len(session.history)):
                old_path = session.history[i]
                if os.path.exists(old_path) and old_path != session.original_image_path:
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        logger.warning(f"删除历史文件失败: {old_path}, {e}")
            session.history = session.history[:session.history_index + 1]

        # 生成新的历史文件名
        history_index = len(session.history)
        new_image_path = os.path.join(
            self._get_session_dir(session_id),
            f"edit_{history_index}.png"
        )

        # 保存编辑后的图片
        with open(new_image_path, "wb") as f:
            f.write(edited_image_data)

        # 更新当前图片
        with open(session.current_image_path, "wb") as f:
            f.write(edited_image_data)

        # 添加到历史
        session.history.append(new_image_path)
        session.history_index = len(session.history) - 1

        # 限制历史步数
        if len(session.history) > self.MAX_HISTORY_STEPS:
            # 删除最早的历史（保留原始图片）
            oldest_path = session.history[1]  # 索引0是原始图片
            if os.path.exists(oldest_path):
                try:
                    os.remove(oldest_path)
                except Exception as e:
                    logger.warning(f"删除旧历史文件失败: {oldest_path}, {e}")
            session.history = [session.history[0]] + session.history[2:]
            session.history_index = len(session.history) - 1

        # 保存会话
        self._save_session_meta(session)

        logger.info(f"编辑应用成功: session_id={session_id}, history_index={session.history_index}")
        return edited_image_data

    def undo(self, session_id: str) -> Optional[bytes]:
        """
        撤销编辑

        Args:
            session_id: 会话ID

        Returns:
            撤销后的图片数据，如果无法撤销则返回None
        """
        session = self._get_session(session_id)
        if session is None:
            logger.error(f"会话不存在: {session_id}")
            return None

        if session.history_index <= 0:
            logger.warning(f"无法撤销，已在最早状态: session_id={session_id}")
            return None

        logger.info(f"撤销编辑: session_id={session_id}, current_index={session.history_index}")

        # 移动到上一个历史状态
        session.history_index -= 1
        previous_path = session.history[session.history_index]

        if not os.path.exists(previous_path):
            logger.error(f"历史图片不存在: {previous_path}")
            return None

        # 读取历史图片
        with open(previous_path, "rb") as f:
            image_data = f.read()

        # 更新当前图片
        with open(session.current_image_path, "wb") as f:
            f.write(image_data)

        # 保存会话
        self._save_session_meta(session)

        logger.info(f"撤销成功: session_id={session_id}, new_index={session.history_index}")
        return image_data

    def redo(self, session_id: str) -> Optional[bytes]:
        """
        重做编辑

        Args:
            session_id: 会话ID

        Returns:
            重做后的图片数据，如果无法重做则返回None
        """
        session = self._get_session(session_id)
        if session is None:
            logger.error(f"会话不存在: {session_id}")
            return None

        if session.history_index >= len(session.history) - 1:
            logger.warning(f"无法重做，已在最新状态: session_id={session_id}")
            return None

        logger.info(f"重做编辑: session_id={session_id}, current_index={session.history_index}")

        # 移动到下一个历史状态
        session.history_index += 1
        next_path = session.history[session.history_index]

        if not os.path.exists(next_path):
            logger.error(f"历史图片不存在: {next_path}")
            return None

        # 读取历史图片
        with open(next_path, "rb") as f:
            image_data = f.read()

        # 更新当前图片
        with open(session.current_image_path, "wb") as f:
            f.write(image_data)

        # 保存会话
        self._save_session_meta(session)

        logger.info(f"重做成功: session_id={session_id}, new_index={session.history_index}")
        return image_data

    def save_edit(self, session_id: str) -> Optional[str]:
        """
        保存编辑结果

        Args:
            session_id: 会话ID

        Returns:
            保存后的图片路径，如果失败则返回None
        """
        session = self._get_session(session_id)
        if session is None:
            logger.error(f"会话不存在: {session_id}")
            return None

        logger.info(f"保存编辑: session_id={session_id}")

        # 读取当前编辑图片
        if not os.path.exists(session.current_image_path):
            logger.error(f"当前图片不存在: {session.current_image_path}")
            return None

        with open(session.current_image_path, "rb") as f:
            edited_image_data = f.read()

        # 保存到原始任务目录，作为新版本
        task_dir = os.path.join(self.history_root_dir, session.task_id)
        if not os.path.exists(task_dir):
            logger.error(f"任务目录不存在: {task_dir}")
            return None

        # 生成新版本文件名
        # 格式: {原索引}_edited_{时间戳}_{uuid}.png
        # 使用时间戳+UUID确保唯一性
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_suffix = uuid.uuid4().hex[:8]
        new_filename = f"{session.image_index}_edited_{timestamp}_{unique_suffix}.png"
        new_image_path = os.path.join(task_dir, new_filename)

        # 保存编辑后的图片
        with open(new_image_path, "wb") as f:
            f.write(edited_image_data)

        logger.info(f"编辑保存成功: session_id={session_id}, path={new_image_path}")

        # 清理会话
        self._cleanup_session(session_id)

        return new_image_path

    def cancel_edit(self, session_id: str) -> bool:
        """
        取消编辑

        Args:
            session_id: 会话ID

        Returns:
            是否成功取消
        """
        session = self._get_session(session_id)
        if session is None:
            logger.warning(f"会话不存在: {session_id}")
            return False

        logger.info(f"取消编辑: session_id={session_id}")

        # 清理会话
        return self._cleanup_session(session_id)

    def _cleanup_session(self, session_id: str) -> bool:
        """
        清理会话资源

        Args:
            session_id: 会话ID

        Returns:
            是否成功清理
        """
        # 从缓存中移除
        if session_id in self._sessions:
            del self._sessions[session_id]

        # 删除会话目录
        session_dir = self._get_session_dir(session_id)
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                logger.info(f"会话目录已删除: {session_dir}")
                return True
            except Exception as e:
                logger.error(f"删除会话目录失败: {session_dir}, {e}")
                return False

        return True

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典，如果不存在则返回None
        """
        session = self._get_session(session_id)
        if session is None:
            return None

        return {
            "id": session.id,
            "task_id": session.task_id,
            "image_index": session.image_index,
            "can_undo": session.history_index > 0,
            "can_redo": session.history_index < len(session.history) - 1,
            "history_length": len(session.history),
            "history_index": session.history_index,
            "current_image_url": f"/api/edit/session/{session_id}/current",
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }

    def get_current_image(self, session_id: str) -> Optional[bytes]:
        """
        获取当前编辑图片

        Args:
            session_id: 会话ID

        Returns:
            图片数据，如果不存在则返回None
        """
        session = self._get_session(session_id)
        if session is None:
            return None

        if not os.path.exists(session.current_image_path):
            return None

        with open(session.current_image_path, "rb") as f:
            return f.read()

    def get_original_image(self, session_id: str) -> Optional[bytes]:
        """
        获取原始图片

        Args:
            session_id: 会话ID

        Returns:
            图片数据，如果不存在则返回None
        """
        session = self._get_session(session_id)
        if session is None:
            return None

        if not os.path.exists(session.original_image_path):
            return None

        with open(session.original_image_path, "rb") as f:
            return f.read()


# 全局服务实例
_service_instance = None


def get_image_edit_service() -> ImageEditService:
    """
    获取图片编辑服务实例

    Returns:
        ImageEditService 实例
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = ImageEditService()
    return _service_instance


def reset_image_edit_service():
    """重置全局服务实例"""
    global _service_instance
    _service_instance = None
