"""
Travel CS AI - Configuration
直接可用的配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Vector DB
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = "travel_kb"

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Server
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# LLM Config
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_FALLBACK = os.getenv("LLM_FALLBACK", "gpt-3.5-turbo")
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 500

# RAG Config
RAG_TOP_K = 5
RAG_SCORE_THRESHOLD = 0.75
EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"

# Session
SESSION_TIMEOUT = 3600  # 1 hour
MAX_CONTEXT_MESSAGES = 10

# Intent Classification
HANDOFF_INTENTS = ["complaint", "emergency"]
HANDOFF_KEYWORDS = ["投诉", "退款", "赔偿", "律师", "法院", "报警", "紧急", "危险"]
CONFIDENCE_THRESHOLD = 0.6

# Sample Data (for testing without KB)
SAMPLE_PRODUCTS = [
    {
        "id": "P001",
        "name": "巴厘岛7日尊享游",
        "price": 8999,
        "duration": 7,
        "destination": ["巴厘岛", "印度尼西亚"],
        "highlights": ["五星酒店", "私人海滩", "SPA体验", "火山观景"],
        "visa": "落地签",
        "inclusions": ["往返机票", "酒店住宿", "景点门票", "导游服务"],
        "cancellation": "出发前30天可全额退款"
    },
    {
        "id": "P002",
        "name": "日本东京5日深度游",
        "price": 12999,
        "duration": 5,
        "destination": ["东京", "日本"],
        "highlights": ["富士山", "温泉体验", "筑地市场", "秋叶原"],
        "visa": "需提前办理",
        "inclusions": ["往返机票", "酒店住宿", "JR Pass", "导游服务"],
        "cancellation": "出发前15天可退款80%"
    },
    {
        "id": "P003",
        "name": "泰国普吉岛6日自由行",
        "price": 4999,
        "duration": 6,
        "destination": ["普吉岛", "泰国"],
        "highlights": ["海岛游", "潜水体验", "夜市美食"],
        "visa": "免签",
        "inclusions": ["往返机票", "酒店住宿"],
        "cancellation": "出发前7天可全额退款"
    }
]

SAMPLE_FAQS = [
    {
        "id": "F001",
        "question": "提前多久预订？",
        "answer": "常规线路建议提前7天预订，旺季建议提前15-30天。",
        "category": "预订",
        "keywords": ["预订", "提前", "时间"]
    },
    {
        "id": "F002",
        "question": "可以退改吗？",
        "answer": "出发前7天可全额退款，3-7天扣30%，1-3天扣50%。",
        "category": "退改",
        "keywords": ["退改", "取消", "退款"]
    },
    {
        "id": "F003",
        "question": "儿童怎么收费？",
        "answer": "2岁以下婴儿免费，2-12岁儿童收成人价80%。",
        "category": "价格",
        "keywords": ["儿童", "婴儿", "收费"]
    }
]
