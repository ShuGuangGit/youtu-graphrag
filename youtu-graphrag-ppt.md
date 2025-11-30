---
marp: true
theme: gaia
size: 4:3
paginate: true
---

<!-- _class: lead -->

![bg left:35%](assets/logo.svg)

# Youtu-GraphRAG  
## 垂直统一的图增强复杂推理新范式

*🚀 以最小 Schema 干预，实现跨域无缝迁移*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/Paper-Latest-blue.svg)](Youtu-GraphRAG.pdf)
[![WeChat](https://img.shields.io/badge/Community-WeChat-32CD32)](assets/wechat_qr.png)
[![Discord](https://img.shields.io/badge/Community-Discord-8A2BE2)](https://discord.gg/QjqhkHQVVM)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-Tencent-blue.svg)](https://deepwiki.com/TencentCloudADP/youtu-graphrag)
[![Stars](https://img.shields.io/github/stars/TencentCloudADP/youtu-graphrag?style=social)](https://github.com/TencentCloudADP/youtu-graphrag)

[🔖 English](README.md) • [🔖 日本語](README-JA.md) • [⭐ 贡献](#contribution) • [📊 基准](https://huggingface.co/datasets/Youtu-Graph/AnonyRAG) • [🚀 快速开始](#quickstart)

---

## 🎯 项目简介

**Youtu-GraphRAG** 是一个基于图 Schema 的垂直统一图增强推理范式，将整个 GraphRAG 框架集成为一个以智能体为核心的有机整体。

> 在图 Schema 最小人为干预下，实现跨领域无缝迁移

![bg right:30%](assets/logo.png)

---

## 🎨 三大落地场景

- 🔗 **多跳推理与总结**  
  解决需多步推理的复杂问题

- 📚 **知识密集型任务**  
  依赖大量结构化/私域知识的问题

- 🌐 **跨域扩展能力**  
  轻松适配学术论文、企业知识库等场景

---

## 🏗️ 框架架构

![w:95%](assets/framework.png)

*Youtu-GraphRAG 框架概览*

---

## 📲 交互式体验界面

![w:48%](assets/graph_demo.png) ![w:48%](assets/retrieval_demo.png)

> 演示视频：[https://youtu.be/fVUsgClHqwc](https://youtu.be/fVUsgClHqwc)

---

<a id="contribution"></a>

## 🚀 六大核心创新

1. **Schema 引导的层次化知识树构建**  
2. **结构语义双重感知的社区检测**  
3. **智能迭代检索（IRCoT）**  
4. **落地级构建与用户友好体验**  
5. **公平匿名数据集 AnonyRAG**  
6. **统一配置管理**

---

### 🏗️ 1. Schema 引导的层次化知识树构建

- 🌱 **种子图 Schema**：约束实体、关系、属性类型  
- 📈 **可扩展 Schema 演进**：动态适应新领域  
- 🏢 **四层架构**：
  - 属性层（实体属性）
  - 关系层（三元组）
  - 关键词层（索引）
  - 社区层（层次化结构）
- ⚡ **快速适配企业场景**

---

### 🌳 2. 结构语义双重感知的社区检测

- 🔬 融合拓扑 + 语义，优于 Leiden/Louvain  
- 📊 支持自顶向下过滤 & 自底向上推理  
- 📝 LLM 增强社区摘要 → 高阶知识抽象

![w:60%](assets/comm.png)

---

### 🤖 3. 智能迭代检索（IRCoT）

- 🎯 **Schema 感知的问题分解** → 并行子查询  
- 🔄 **迭代反思机制** → 深度推理

![w:50%](assets/agent.png)

---

### 🧠 4. 落地级构建与用户友好体验

- 🎯 更低 Token，更高精度  
- 🤹‍♀️ `output/graphs/` 支持 Neo4j 可视化  
- ⚡ 并行处理子问题  
- 🤔 提供推理轨迹，增强可解释性  
- 📊 企业级扩展：新领域接入成本极低

---

### 📈 5. 公平匿名数据集：AnonyRAG

- 🔗 [Hugging Face 链接](https://huggingface.co/datasets/Youtu-Graph/AnonyRAG)
- ✅ 防止预训练知识泄露  
- ✅ 真实检索性能测试  
- ✅ 中英双语支持

---

### ⚙️ 6. 统一配置管理

- 🎛️ 单一 YAML 文件管理所有组件  
- 🔧 运行时动态调整参数  
- 🌍 多环境无缝迁移  
- 🔄 向后兼容

---

## 📊 实验表现

> 在 GraphRAG-Bench、HotpotQA、MuSiQue 等 6 个基准上验证

- **33.6% Token 成本降低**
- **16.62% 精度提升**
- 显著推动帕累托前沿

![w:90%](assets/performance.png)

![w:52%](assets/pareto.png) ![w:34%](assets/radar.png)

---

## 📁 项目结构

```
youtu-graphrag/
├── 📁 config/                     # 配置系统
│   ├── base_config.yaml           # 主配置文件
│   ├── config_loader.py           # 配置加载器
│   └── __init__.py                # 配置模块接口
│
├── 📁 data/                       # 数据目录
│
├── 📁 models/                     # 核心模型
│   ├── 📁 constructor/            # 知识图谱构建模块
│   │   └── kt_gen.py              # KTBuilder - 层次化图构建器
│   ├── 📁 retriever/              # 检索模块
│   │   ├── enhanced_kt_retriever.py  # KTRetriever - 主检索器
│   │   ├── agentic_decomposer.py     # 复杂查询解耦
│   └── └── faiss_filter.py           # DualFAISSRetriever - FAISS 检索器
│
├── 📁 utils/                      # 工具模块
│   ├── tree_comm.py               # 社区检测算法
│   ├── call_llm_api.py            # 大语言模型 API 调用
│   ├── eval.py                    # 评估工具
│   └── graph_processor.py         # 图处理工具
│
├── 📁 schemas/                    # 种子 Schema 定义
├── 📁 assets/                     # 静态资源（图片、图表等）
│
├── 📁 output/                     # 输出目录
│   ├── graphs/                    # 构建完成的知识图谱
│   ├── chunks/                    # 文本分块信息
│   └── logs/                      # 运行日志
│
├── 📁 retriever/                  # 检索缓存
│
├── main.py                       # 🎯 主程序入口
├── setup_env.sh                  # 安装 web 依赖库
├── start.sh                      # 启动 web 服务
├── requirements.txt              # 依赖包列表
└── README.md                     # 项目文档

```

---

### 💻 代码贡献

1. 🍴 Fork 本项目到您的账户
2. 🌿 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 💾 提交您的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 📤 推送到远程分支 (`git push origin feature/AmazingFeature`)
5. 🔄 提交 Pull Request

---

### 🔧 扩展开发指南

- **🌱 新种子 Schema 开发**：贡献高质量的种子图 Schema 设计和数据处理逻辑
- **📊 自定义数据集集成**：在图 Schema 最小人为干预的前提下，集成新的数据集
- **🎯 领域特定应用**：展示特定领域最佳实践案例

---