#!/usr/bin/env python3
"""
Langfuse 集成使用示例

这个示例展示了如何在项目中使用集成了 Langfuse 观测功能的 LLMCompletionCall 类。
"""

import os
from utils.call_llm_api import LLMCompletionCall

def basic_example():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建 LLM 客户端
    llm_client = LLMCompletionCall()
    
    # 检查 Langfuse 状态
    status = llm_client.get_langfuse_status()
    print(f"Langfuse 状态: {status}")
    
    # 简单调用
    response = llm_client.call_api("请用一句话介绍人工智能")
    print(f"LLM 响应: {response}")
    
    # 手动刷新 Langfuse 数据
    llm_client.flush_langfuse()

def advanced_example():
    """高级使用示例"""
    print("\n=== 高级使用示例 ===")
    
    llm_client = LLMCompletionCall()
    
    # 创建自定义 trace
    trace = llm_client.create_trace(
        name="文档分析任务",
        session_id="demo_session_001",
        user_id="demo_user",
        metadata={
            "task_type": "document_analysis",
            "priority": "high",
            "source": "demo_script"
        }
    )
    
    if trace:
        print("已创建 Langfuse trace")
        
        # 记录输入处理步骤
        trace.span(
            name="输入预处理",
            input={"raw_document": "这是一份关于人工智能的技术文档"},
            output={"processed_document": "预处理后的文档内容"}
        )
        
        # 调用 LLM 进行分析
        analysis_prompt = """
        请分析以下文档内容，提取关键信息：
        1. 主要主题
        2. 关键技术点
        3. 应用场景
        
        文档内容：这是一份关于人工智能的技术文档，介绍了机器学习、深度学习等技术的应用。
        """
        
        response = llm_client.call_api(
            content=analysis_prompt,
            session_id="demo_session_001",
            user_id="demo_user",
            metadata={"step": "document_analysis"}
        )
        
        print(f"分析结果: {response}")
        
        # 记录后处理步骤
        trace.span(
            name="结果后处理",
            input={"analysis_result": response},
            output={"final_summary": "分析完成，已提取关键信息"}
        )
        
        # 更新 trace 状态
        trace.update(status="completed")
    
    # 刷新数据
    llm_client.flush_langfuse()

def batch_processing_example():
    """批量处理示例"""
    print("\n=== 批量处理示例 ===")
    
    llm_client = LLMCompletionCall()
    
    # 模拟批量处理任务
    documents = [
        "人工智能在医疗领域的应用",
        "机器学习算法的发展历程", 
        "深度学习在图像识别中的突破"
    ]
    
    for i, doc in enumerate(documents):
        print(f"处理文档 {i+1}: {doc}")
        
        response = llm_client.call_api(
            content=f"请简要总结以下主题：{doc}",
            session_id=f"batch_session_{i}",
            user_id="batch_user",
            metadata={
                "batch_id": "batch_001",
                "document_index": i,
                "total_documents": len(documents)
            }
        )
        
        print(f"总结: {response}\n")
    
    # 批量刷新
    llm_client.flush_langfuse()

def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    # 创建禁用 Langfuse 的客户端用于测试
    llm_client = LLMCompletionCall(enable_langfuse=False)
    
    try:
        # 这里可能会因为 API 密钥等问题导致错误
        response = llm_client.call_api("测试错误处理")
        print(f"成功响应: {response}")
    except Exception as e:
        print(f"捕获到错误: {e}")
        # 在实际应用中，这里会记录到 Langfuse

if __name__ == "__main__":
    print("Langfuse 集成示例")
    print("注意：运行此示例前请确保已正确配置 Langfuse 环境变量")
    print("=" * 50)
    
    # 检查环境变量
    required_vars = ["LLM_API_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"警告：缺少环境变量: {missing_vars}")
        print("请配置 .env 文件或设置环境变量")
        print("示例将使用禁用 Langfuse 的模式运行")
    
    try:
        basic_example()
        advanced_example()
        batch_processing_example()
        error_handling_example()
        
        print("\n示例运行完成！")
        print("请访问 Langfuse 仪表板查看观测数据")
        
    except Exception as e:
        print(f"示例运行出错: {e}")
        print("请检查配置和网络连接")
