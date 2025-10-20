import os
import time
import json
import requests
import re
from typing import Optional, Dict, Any

from openai import OpenAI, AzureOpenAI
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.openai import openai
from langfuse import observe

from utils.logger import logger
from utils.session_manager import ensure_session

load_dotenv()

class LLMCompletionCall:
    def __init__(self, enable_langfuse: bool = True):
        self.llm_model = os.getenv("LLM_MODEL", "deepseek-chat")
        self.llm_base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        if not self.llm_api_key:
            raise ValueError("LLM API key not provided")

        # Langfuse 配置
        self.enable_langfuse = enable_langfuse and self._is_langfuse_configured()
        self.langfuse = None
        if self.enable_langfuse:
            self.langfuse = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            )
            logger.info("Langfuse 观测已启用")

        self.openai_provider = os.getenv("OPENAI_PROVIDER", "openai").lower()
        if self.openai_provider == "azure":
            self.api_version = os.getenv("API_VERSION", "2025-01-01-preview")
            if self.enable_langfuse:
                # 使用 Langfuse 包装的 Azure OpenAI 客户端
                self.client = openai.AzureOpenAI(
                    azure_endpoint=self.llm_base_url,
                    api_key=self.llm_api_key,
                    api_version=self.api_version,
                )
            else:
                self.client = AzureOpenAI(
                    azure_endpoint=self.llm_base_url,
                    api_key=self.llm_api_key,
                    api_version=self.api_version,
                )
        else:
            if self.enable_langfuse:
                # 使用 Langfuse 包装的 OpenAI 客户端
                self.client = openai.OpenAI(
                    base_url=self.llm_base_url,
                    api_key=self.llm_api_key
                )
            else:
                self.client = OpenAI(base_url=self.llm_base_url, api_key = self.llm_api_key)

    def _is_langfuse_configured(self) -> bool:
        """检查 Langfuse 配置是否完整"""
        required_keys = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
        return all(os.getenv(key) for key in required_keys)

    def call_api(self, content: str, session_id: Optional[str] = None,
                 user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Call API to generate text with retry mechanism and Langfuse observability.

        Args:
            content: Prompt content
            session_id: Optional session ID for tracking (如果为None，将自动使用当前线程的会话ID)
            user_id: Optional user ID for tracking (如果为None，将自动使用当前线程的用户ID)
            metadata: Optional metadata for tracking

        Returns:
            Generated text response
        """

        # 确保当前线程有会话
        current_session = ensure_session()

        # 如果没有提供 session_id 或 user_id，使用当前线程的会话信息
        if session_id is None:
            session_id = current_session.session_id
        if user_id is None:
            user_id = current_session.user_id

        # 合并元数据
        current_metadata = current_session.metadata.copy()
        if metadata:
            current_metadata.update(metadata)

        logger.info(f"LLM api calling. enable_langfuse: {self.enable_langfuse}")
        logger.info(f"LLM api calling. session.session_id: {session_id}")
        logger.info(f"LLM api calling. session.user_id: {user_id}")
        
        # 使用装饰器方式记录 Langfuse 观测
        if self.enable_langfuse and self.langfuse:
            return self._call_api_with_langfuse(content, session_id, user_id, current_metadata)
        else:
            return self._call_api_simple(content)
    
    def _call_api_simple(self, content: str) -> str:
        """简单的 API 调用，不使用 Langfuse"""
        try:
            completion = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": content}],
                temperature=0.3
            )
            raw = completion.choices[0].message.content or ""
            return self._clean_llm_content(raw)
        except Exception as e:
            logger.error(f"LLM api calling failed. Error: {e}")
            raise e
    
    @observe(as_type="generation")
    def _call_api_with_langfuse(self, content: str, session_id: str, user_id: str, metadata: Dict[str, Any]) -> str:
        """使用 Langfuse 装饰器观测的 API 调用"""
        try:
            self.langfuse.update_current_trace(session_id=session_id)
            self.langfuse.update_current_trace(user_id=user_id)
            self.langfuse.update_current_trace(metadata=metadata)

            completion = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": content}],
                temperature=0.3
            )
            raw = completion.choices[0].message.content or ""
            clean_completion = self._clean_llm_content(raw)
            return clean_completion
            
        except Exception as e:
            logger.error(f"LLM api calling failed. Error: {e}")
            raise e

    def _clean_llm_content(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        t = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        t = re.sub(r"[\u200B-\u200D\uFEFF]", "", t)
        fence_re = re.compile(r"^\s*```(?:\s*\w+)?\s*\n(?P<body>[\s\S]*?)\n\s*```\s*$", re.MULTILINE)
        m = fence_re.match(t)
        if m:
            t = m.group("body").strip()
        else:
            if t.startswith("```") and t.endswith("```") and len(t) >= 6:
                t = t[3:-3].strip()

        if t.lower().startswith("json\n"):
            t = t.split("\n", 1)[1].strip()

        return t
    
    def create_trace(self, name: str, session_id: Optional[str] = None, 
                    user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        创建一个 Langfuse trace 用于更复杂的观测场景
        
        Args:
            name: Trace 名称
            session_id: 会话 ID
            user_id: 用户 ID
            metadata: 元数据
            
        Returns:
            Langfuse trace 对象
        """
        if not self.enable_langfuse or not self.langfuse:
            return None
            
        return self.langfuse.trace(
            name=name,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {}
        )
    
    def flush_langfuse(self):
        """手动刷新 Langfuse 数据"""
        if self.enable_langfuse and self.langfuse:
            self.langfuse.flush()
    
    def get_langfuse_status(self) -> Dict[str, Any]:
        """获取 Langfuse 配置状态"""
        return {
            "enabled": self.enable_langfuse,
            "configured": self._is_langfuse_configured(),
            "client_initialized": self.langfuse is not None
        }