"""
Travel CS AI - FastAPI Server
API服务实现
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import time

import config
from chat.engine import engine

app = FastAPI(
    title="Travel CS AI API",
    description="旅游产品智能客服系统 API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/web", StaticFiles(directory="web"), name="web")
app.mount("/admin", StaticFiles(directory="admin"), name="admin")


# ========== Pydantic Models ==========

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    confidence: float
    need_escalation: bool
    sources: Optional[dict] = None


class MessageItem(BaseModel):
    role: str
    content: str
    timestamp: str


class ProductCreate(BaseModel):
    name: str
    price: int
    duration: int
    destination: Optional[List[str]] = []
    highlights: Optional[List[str]] = []
    visa: Optional[str] = ""
    inclusions: Optional[List[str]] = []
    cancellation: Optional[str] = ""


class FAQCreate(BaseModel):
    question: str
    answer: str
    category: Optional[str] = "general"
    keywords: Optional[List[str]] = []


# ========== API Endpoints ==========

@app.get("/")
def root():
    """重定向到聊天界面"""
    return {
        "message": "Travel CS AI API",
        "docs": "/docs",
        "chat": "/web/chat.html",
        "admin": "/admin/dashboard.html"
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    发送消息并获取回复
    
    Example:
    ```bash
    curl -X POST http://localhost:8000/api/chat \\
      -H "Content-Type: application/json" \\
      -d '{"message": "巴厘岛多少钱？", "session_id": "user_001"}'
    ```
    """
    session_id = request.session_id or f"sess_{int(time.time() * 1000)}"
    
    result = engine.process(session_id, request.message)
    
    return ChatResponse(
        response=result['response'],
        session_id=session_id,
        intent=result['intent'],
        confidence=result['confidence'],
        need_escalation=result['need_escalation'],
        sources=result.get('sources')
    )


@app.get("/api/history/{session_id}")
def get_history(session_id: str):
    """获取会话历史"""
    conv = engine.get_conversation(session_id)
    if not conv:
        return {"session_id": session_id, "messages": []}
    
    return {
        "session_id": session_id,
        "state": conv.state,
        "messages": [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp}
            for m in conv.messages
        ]
    }


@app.get("/api/stats")
def get_stats():
    """获取系统统计"""
    return engine.get_stats()


# ========== Knowledge Base Management ==========

@app.get("/api/kb/products")
def list_products():
    """获取所有产品"""
    return list(engine.kb.products.values())


@app.get("/api/kb/products/search")
def search_products(q: str):
    """搜索产品"""
    results = engine.kb.search_products(q)
    return results


@app.post("/api/kb/products")
def create_product(product: ProductCreate):
    """创建新产品"""
    import uuid
    product_id = f"P{str(uuid.uuid4())[:6].upper()}"
    
    new_product = product.dict()
    new_product['id'] = product_id
    
    engine.kb.products[product_id] = new_product
    
    return {"id": product_id, "message": "Product created"}


@app.delete("/api/kb/products/{product_id}")
def delete_product(product_id: str):
    """删除产品"""
    if product_id in engine.kb.products:
        del engine.kb.products[product_id]
        return {"message": "Product deleted"}
    raise HTTPException(status_code=404, detail="Product not found")


@app.get("/api/kb/faqs")
def list_faqs():
    """获取所有FAQ"""
    return list(engine.kb.faqs.values())


@app.get("/api/kb/faqs/search")
def search_faqs(q: str):
    """搜索FAQ"""
    results = engine.kb.search_faqs(q)
    return results


@app.post("/api/kb/faqs")
def create_faq(faq: FAQCreate):
    """创建新FAQ"""
    import uuid
    faq_id = f"F{str(uuid.uuid4())[:6].upper()}"
    
    new_faq = faq.dict()
    new_faq['id'] = faq_id
    
    engine.kb.faqs[faq_id] = new_faq
    
    return {"id": faq_id, "message": "FAQ created"}


@app.delete("/api/kb/faqs/{faq_id}")
def delete_faq(faq_id: str):
    """删除FAQ"""
    if faq_id in engine.kb.faqs:
        del engine.kb.faqs[faq_id]
        return {"message": "FAQ deleted"}
    raise HTTPException(status_code=404, detail="FAQ not found")


# ========== Health & Monitoring ==========

@app.get("/health")
def health():
    """健康检查"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": int(time.time())
    }


@app.get("/api/config")
def get_config():
    """获取配置 (脱敏)"""
    return {
        "llm_model": config.LLM_MODEL,
        "llm_fallback": config.LLM_FALLBACK,
        "rag_top_k": config.RAG_TOP_K,
        "confidence_threshold": config.CONFIDENCE_THRESHOLD,
        "api_keys_configured": {
            "deepseek": bool(config.DEEPSEEK_API_KEY),
            "openai": bool(config.OPENAI_API_KEY)
        }
    }


# ========== Error Handlers ==========

@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return {
        "error": str(exc),
        "message": "Internal server error"
    }


# ========== Main ==========

if __name__ == "__main__":
    print("🚀 Starting Travel CS AI Server...")
    print(f"📱 Chat UI: http://{config.API_HOST}:{config.API_PORT}/web/chat.html")
    print(f"⚙️  Admin: http://{config.API_HOST}:{config.API_PORT}/admin/dashboard.html")
    print(f"📚 API Docs: http://{config.API_HOST}:{config.API_PORT}/docs")
    
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level="info"
    )
