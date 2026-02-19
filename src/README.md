# 旅游产品智能客服 AI - MVP原型

> **任务**: T4 - MVP原型开发与Demo  
> **交付物**: `src/` 可运行代码  
> **负责人**: 析理  
> **日期**: 2026-02-19

## 快速启动

```bash
cd src
pip install -r requirements.txt
python api/main.py
```

访问:
- 网页聊天: http://localhost:8000/web/chat.html
- 管理后台: http://localhost:8000/admin/dashboard.html
- API文档: http://localhost:8000/docs

## 功能特性

- ✅ 基础对话 (RAG检索 + LLM生成)
- ✅ 多轮上下文记忆
- ✅ 意图识别 (紧急/预订/咨询)
- ✅ 人工介入标记
- ✅ 知识库管理 (增删改查)
- ✅ 对话历史查看

## 技术栈

- FastAPI + SQLite
- DeepSeek API (via ZenMux)
- QMD 向量检索
- 纯前端 HTML/JS
