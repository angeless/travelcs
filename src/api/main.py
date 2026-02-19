"""
旅游客服AI - FastAPI服务
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import uuid

import config
from chat.engine import engine

app = FastAPI(
    title="旅游客服AI API",
    description="旅游产品智能客服系统 MVP",
    version="0.1.0"
)

# 挂载静态文件
app.mount("/web", StaticFiles(directory="web"), name="web")
app.mount("/admin", StaticFiles(directory="admin"), name="admin")


# ========== 数据模型 ==========

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    confidence: float
    handoff: bool


class Message(BaseModel):
    role: str
    content: str
    timestamp: str


class KnowledgeItem(BaseModel):
    id: str
    type: str  # product / faq
    content: dict


# ========== API路由 ==========

@app.get("/", response_class=HTMLResponse)
def root():
    """首页重定向到聊天界面"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>旅游客服AI</title>
        <meta http-equiv="refresh" content="0;url=/web/chat.html">
    </head>
    <body>
        <p>正在跳转...</p>
        <a href="/web/chat.html">点击这里进入聊天界面</a>
    </body>
    </html>
    """


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """发送消息并获取回复"""
    # 生成session_id
    session_id = request.session_id or str(uuid.uuid4())[:8]
    
    # 处理消息
    result = engine.process(session_id, request.message)
    
    return ChatResponse(
        response=result["response"],
        session_id=session_id,
        intent=result["intent"],
        confidence=result["confidence"],
        handoff=result["handoff"]
    )


@app.get("/api/history/{session_id}", response_model=List[Message])
def get_history(session_id: str):
    """获取对话历史"""
    history = engine.get_history(session_id)
    return [Message(**msg) for msg in history]


@app.get("/api/stats")
def get_stats():
    """获取系统统计"""
    return engine.get_stats()


# ========== 知识库管理API ==========

@app.get("/api/kb/products")
def list_products():
    """获取产品列表"""
    return list(engine.kb.products.values())


@app.get("/api/kb/faqs")
def list_faqs():
    """获取FAQ列表"""
    return list(engine.kb.faqs.values())


@app.post("/api/kb/products")
def add_product(product: dict):
    """添加产品"""
    pid = product.get("id") or f"P{len(engine.kb.products)+1:03d}"
    product["id"] = pid
    engine.kb.products[pid] = product
    return {"success": True, "id": pid}


@app.post("/api/kb/faqs")
def add_faq(faq: dict):
    """添加FAQ"""
    fid = faq.get("id") or f"F{len(engine.kb.faqs)+1:03d}"
    faq["id"] = fid
    engine.kb.faqs[fid] = faq
    return {"success": True, "id": fid}


@app.delete("/api/kb/products/{product_id}")
def delete_product(product_id: str):
    """删除产品"""
    if product_id in engine.kb.products:
        del engine.kb.products[product_id]
        return {"success": True}
    raise HTTPException(status_code=404, detail="产品不存在")


@app.delete("/api/kb/faqs/{faq_id}")
def delete_faq(faq_id: str):
    """删除FAQ"""
    if faq_id in engine.kb.faqs:
        del engine.kb.faqs[faq_id]
        return {"success": True}
    raise HTTPException(status_code=404, detail="FAQ不存在")


# ========== 健康检查 ==========

@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok", "version": "0.1.0"}


# ========== 主函数 ==========

if __name__ == "__main__":
    import os
    os.makedirs("./data", exist_ok=True)
    
    print(f"🚀 启动旅游客服AI服务...")
    print(f"📱 网页聊天: http://{config.API_HOST}:{config.API_PORT}/web/chat.html")
    print(f"⚙️ 管理后台: http://{config.API_HOST}:{config.API_PORT}/admin/dashboard.html")
    print(f"📚 API文档: http://{config.API_HOST}:{config.API_PORT}/docs")
    
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
