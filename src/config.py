"""
旅游客服AI - 配置文件
"""
import os

# API配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# LLM配置 (使用ZenMux)
ZENMUX_URL = os.getenv("ZENMUX_URL", "https://api.zenmux.com/v1")
ZENMUX_API_KEY = os.getenv("ZENMUX_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
LLM_FALLBACK = os.getenv("LLM_FALLBACK", "google/gemini-3-flash-preview")

# 数据库配置
DB_PATH = os.getenv("DB_PATH", "./data/travel_cs.db")

# 知识库配置
KNOWLEDGE_BASE_DIR = os.getenv("KB_DIR", "./data/knowledge")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RETRIEVAL = 5

# 对话配置
MAX_CONTEXT_MESSAGES = 10
SESSION_TIMEOUT_MINUTES = 30

# 人工介入配置
HANDOFF_KEYWORDS = ["投诉", "退款", "赔偿", "律师", "法院", "报警", "紧急", "危险", "受伤"]
HANDOFF_CONFIDENCE_THRESHOLD = 0.6

# 响应模板
RESPONSE_TEMPLATES = {
    "greeting": "您好！我是您的旅游顾问，请问有什么可以帮您？",
    "handoff": "理解您的紧急情况，我立即为您转接人工客服，请稍等...",
    "not_found": "抱歉，这个问题我还需要确认，请您稍等或联系人工客服。",
    "error": "系统暂时出现问题，请稍后重试或联系人工客服。"
}

# 产品示例数据 (MVP使用)
SAMPLE_PRODUCTS = [
    {
        "id": "P001",
        "name": "巴厘岛7日尊享游",
        "price": 8999,
        "highlights": ["五星酒店", "私人海滩", "SPA体验"],
        "visa": "落地签"
    },
    {
        "id": "P002", 
        "name": "日本东京5日深度游",
        "price": 12999,
        "highlights": ["富士山", "温泉", "美食"],
        "visa": "需提前办理"
    },
    {
        "id": "P003",
        "name": "泰国普吉岛6日自由行",
        "price": 4999,
        "highlights": ["海岛", "潜水", "夜市"],
        "visa": "免签"
    }
]

# FAQ示例数据
SAMPLE_FAQS = [
    {
        "id": "F001",
        "question": "提前多久预订？",
        "answer": "常规线路建议提前7天预订，旺季建议提前15-30天。"
    },
    {
        "id": "F002",
        "question": "可以退改吗？",
        "answer": "出发前7天可全额退款，3-7天扣30%，1-3天扣50%，当天不予退款。"
    },
    {
        "id": "F003",
        "question": "儿童怎么收费？",
        "answer": "2-12岁儿童按成人价70%收费，不占床可减1000元。"
    }
]
