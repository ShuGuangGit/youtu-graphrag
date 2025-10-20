"""
会话管理工具

提供多种 sessionId 生成和管理策略，用于 Langfuse 观测。
支持 threading.local() 实现线程级别的会话管理，确保 RAG 流程的完整串联。
"""

import uuid
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    user_id: Optional[str] = None
    created_at: float = None
    metadata: Dict[str, Any] = None
    rag_steps: list = None  # 记录 RAG 流程步骤
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.metadata is None:
            self.metadata = {}
        if self.rag_steps is None:
            self.rag_steps = []
    
    def add_rag_step(self, step_name: str, step_data: Dict[str, Any]):
        """添加 RAG 流程步骤"""
        step_info = {
            "step_name": step_name,
            "timestamp": time.time(),
            "data": step_data
        }
        self.rag_steps.append(step_info)
        self.metadata["rag_steps_count"] = len(self.rag_steps)
    
    def get_rag_flow_summary(self) -> Dict[str, Any]:
        """获取 RAG 流程摘要"""
        return {
            "session_id": self.session_id,
            "total_steps": len(self.rag_steps),
            "steps": [step["step_name"] for step in self.rag_steps],
            "duration": time.time() - self.created_at if self.rag_steps else 0
        }


class ThreadLocalSessionManager:
    """线程本地会话管理器"""
    
    def __init__(self):
        self._local = threading.local()
        self.active_sessions: Dict[str, SessionInfo] = {}
    
    @property
    def current_session(self) -> Optional[SessionInfo]:
        """获取当前线程的会话"""
        return getattr(self._local, 'current_session', None)
    
    @current_session.setter
    def current_session(self, session: Optional[SessionInfo]):
        """设置当前线程的会话"""
        self._local.current_session = session
    
    def get_current_session_id(self) -> Optional[str]:
        """获取当前线程的会话ID"""
        session = self.current_session
        return session.session_id if session else None
    
    def get_current_user_id(self) -> Optional[str]:
        """获取当前线程的用户ID"""
        session = self.current_session
        return session.user_id if session else None
    
    def get_current_metadata(self) -> Dict[str, Any]:
        """获取当前线程的元数据"""
        session = self.current_session
        return session.metadata if session else {}
    
    def ensure_session(self) -> SessionInfo:
        """确保当前线程有会话，如果没有则自动创建"""
        session = self.current_session
        if session is None:
            # 自动创建会话
            session = self._create_auto_session()
            self.current_session = session
        return session
    
    def _create_auto_session(self) -> SessionInfo:
        """自动创建会话"""
        session_id = self._generate_session_id("youtu-GraphRAG-user", "auto")
        session = SessionInfo(
            session_id=session_id,
            user_id="youtu-GraphRAG-user",
            metadata={"auto_created": True, "created_at": time.time()}
        )
        self.active_sessions[session_id] = session
        return session
    
    def _generate_session_id(self, user_id: str, session_type: str) -> str:
        """生成会话ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{session_type}_{user_id}_{timestamp}_{unique_id}"


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionInfo] = {}
        self.thread_manager = ThreadLocalSessionManager()
    
    def create_session(self,
                      user_id: str="youtu-GraphRAG-user",
                      session_type: str = "default",
                      metadata: Optional[Dict[str, Any]] = None) -> SessionInfo:
        """
        创建新会话
        
        Args:
            session_type: 会话类型
            metadata: 元数据
            
        Returns:
            SessionInfo 对象
        """
        user_id = "youtu-GraphRAG-user"
        # 生成会话ID
        session_id = self._generate_session_id(user_id, session_type)
        
        # 创建会话信息
        session_info = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # 存储会话
        self.active_sessions[session_id] = session_info
        
        return session_info
    
    def get_or_create_current_session(self) -> SessionInfo:
        """获取或创建当前线程的会话"""
        return self.thread_manager.ensure_session()
    
    def clear_current_session(self):
        """清除当前线程的会话"""
        current_session = self.thread_manager.current_session
        if current_session:
            # 从活跃会话中移除
            self.end_session(current_session.session_id)
            # 清除当前线程会话
            self.thread_manager.current_session = None
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        return self.active_sessions.get(session_id)
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]):
        """更新会话元数据"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].metadata.update(metadata)
    
    def end_session(self, session_id: str):
        """结束会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def _generate_session_id(self, user_id: Optional[str], session_type: str) -> str:
        """生成会话ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        if user_id:
            return f"{session_type}_{user_id}_{timestamp}_{unique_id}"
        else:
            return f"{session_type}_{timestamp}_{unique_id}"


# 全局会话管理器实例
session_manager = SessionManager()


# 便捷的全局函数
def get_current_session_id() -> Optional[str]:
    """获取当前线程的会话ID，如果没有则自动创建"""
    return session_manager.thread_manager.get_current_session_id()


def get_current_user_id() -> Optional[str]:
    """获取当前线程的用户ID"""
    return session_manager.thread_manager.get_current_user_id()


def get_current_metadata() -> Dict[str, Any]:
    """获取当前线程的元数据"""
    return session_manager.thread_manager.get_current_metadata()


def ensure_session() -> SessionInfo:
    """确保当前线程有会话，如果没有则自动创建"""
    return session_manager.get_or_create_current_session()


def clear_current_session():
    """清除当前线程的会话"""
    session_manager.clear_current_session()

# 便捷函数
def get_or_create_session(session_id: Optional[str] = None,
                         user_id: Optional[str] = None,
                         session_type: str = "default") -> SessionInfo:
    """
    获取现有会话或创建新会话
    
    Args:
        session_id: 现有会话ID（可选）
        user_id: 用户ID
        session_type: 会话类型
        
    Returns:
        SessionInfo 对象
    """
    if session_id and session_id in session_manager.active_sessions:
        return session_manager.get_session(session_id)
    else:
        return session_manager.create_session(
            user_id=user_id,
            session_type=session_type
        )
