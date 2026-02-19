# Travel CS AI - Implementation Guide

可运行的旅游产品智能客服系统。

## Quick Start

```bash
git clone https://github.com/angeless/travelcs.git
cd travelcs/src
pip install -r requirements.txt
python api/main.py
```

访问 http://localhost:8000/web/chat.html

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│  LLM        │
│  (Web/App)  │◀────│   Server    │◀────│ (DeepSeek)  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  Qdrant     │
                    │ Vector DB   │
                    └─────────────┘
```

---

## Implementation Details

### 1. Intent Classifier

文件: `chat/engine.py`

```python
class IntentClassifier:
    """意图分类 - 直接可用的实现"""
    
    INTENTS = {
        'itinerary_query': {
            'keywords': ['行程', '路线', '推荐', '去哪', '好玩'],
            'handler': 'handle_itinerary'
        },
        'price_inquiry': {
            'keywords': ['多少钱', '价格', '费用', '团费', '便宜'],
            'handler': 'handle_price'
        },
        'booking': {
            'keywords': ['预订', '报名', '下单', '购买'],
            'handler': 'handle_booking'
        },
        'complaint': {
            'keywords': ['投诉', '退款', '赔偿', '差评'],
            'handler': 'handle_complaint',
            'priority': 5  # 强制转人工
        },
        'emergency': {
            'keywords': ['急', '取消', '生病', '机场'],
            'handler': 'handle_emergency',
            'priority': 5
        }
    }
    
    def classify(self, message: str) -> tuple:
        """
        返回: (intent, confidence, handler)
        示例: ('price_inquiry', 0.95, 'handle_price')
        """
        message = message.lower()
        
        for intent, config in self.INTENTS.items():
            score = sum(1 for kw in config['keywords'] if kw in message)
            if score > 0:
                confidence = min(0.5 + score * 0.2, 1.0)
                return (intent, confidence, config['handler'])
        
        return ('general', 0.5, 'handle_general')
```

### 2. RAG Retrieval

文件: `chat/engine.py`

```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class RAGRetriever:
    """RAG检索 - 需要预先配置Qdrant"""
    
    def __init__(self):
        # 本地模型，无需API
        self.encoder = SentenceTransformer('BAAI/bge-large-zh-v1.5')
        self.client = QdrantClient(host="localhost", port=6333)
    
    def retrieve(self, query: str, top_k: int = 5) -> list:
        """
        返回相关文档列表
        示例返回: [
            {'content': '巴厘岛7日游...', 'score': 0.92, 'source': 'itinerary'},
            {'content': '退改政策...', 'score': 0.85, 'source': 'policy'}
        ]
        """
        # 向量化查询
        query_vector = self.encoder.encode(query).tolist()
        
        # 检索
        results = self.client.search(
            collection_name="travel_kb",
            query_vector=query_vector,
            limit=top_k
        )
        
        return [
            {
                'content': hit.payload['content'],
                'score': hit.score,
                'source': hit.payload.get('source', 'unknown')
            }
            for hit in results
        ]
```

### 3. Response Generator

```python
import openai

class ResponseGenerator:
    """回复生成 - 支持多模型切换"""
    
    def __init__(self):
        # 主模型: DeepSeek (便宜，中文好)
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        # 备用模型: OpenAI (处理复杂投诉)
        self.openai_key = os.getenv("OPENAI_API_KEY")
    
    def generate(self, query: str, context: list, intent: str) -> dict:
        """
        生成回复
        
        Args:
            query: 用户问题
            context: RAG检索结果
            intent: 意图类型
        
        Returns:
            {
                'response': '回复文本',
                'model_used': 'deepseek',
                'confidence': 0.9,
                'sources': ['doc1', 'doc2']
            }
        """
        
        # 构建prompt
        prompt = self._build_prompt(query, context, intent)
        
        # 投诉/紧急用GPT-4
        if intent in ['complaint', 'emergency']:
            response = self._call_openai(prompt, model="gpt-4")
            model = "openai"
        else:
            response = self._call_deepseek(prompt)
            model = "deepseek"
        
        return {
            'response': response,
            'model_used': model,
            'sources': [c['source'] for c in context],
            'need_escalation': intent in ['complaint', 'emergency']
        }
    
    def _call_deepseek(self, prompt: str) -> str:
        """调用DeepSeek API"""
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.deepseek_key}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        return response.json()['choices'][0]['message']['content']
```

---

## Configuration

### 环境变量

创建 `.env` 文件:

```bash
# LLM API Keys (必须)
DEEPSEEK_API_KEY=sk-xxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxx

# Vector DB (必须)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis (会话存储)
REDIS_URL=redis://localhost:6379/0

# 可选: 渠道API Keys
WHATSAPP_TOKEN=xxxxxxxx
WECHAT_APPID=xxxxxxxx
WECHAT_SECRET=xxxxxxxx
WECOM_CORP_ID=xxxxxxxx
```

### 依赖安装

`requirements.txt`:

```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# LLM
openai==1.12.0
requests==2.31.0

# Vector DB
qdrant-client==1.7.0
sentence-transformers==2.3.0

# Data Processing
pandas==2.2.0
numpy==1.26.0
PyPDF2==3.0.1
python-docx==1.1.0

# Storage
redis==5.0.1
sqlalchemy==2.0.25

# Utils
python-dotenv==1.0.0
pydantic==2.6.0
```

---

## Database Setup

### Qdrant (Vector DB)

```bash
# Docker启动
docker run -p 6333:6333 qdrant/qdrant:latest

# 创建集合
curl -X PUT http://localhost:6333/collections/travel_kb \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1024,
      "distance": "Cosine"
    }
  }'
```

### 数据导入

```python
# scripts/load_kb.py
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import json

client = QdrantClient("localhost", port=6333)
encoder = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# 加载知识
with open('kb/itineraries.json') as f:
    docs = json.load(f)

# 生成向量并入库
for i, doc in enumerate(docs):
    vector = encoder.encode(doc['content'])
    client.upsert(
        collection_name="travel_kb",
        points=[{
            "id": i,
            "vector": vector.tolist(),
            "payload": doc
        }]
    )
```

---

## API Endpoints

### Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "巴厘岛多少钱？",
    "session_id": "user_123"
  }'
```

响应:
```json
{
  "response": "巴厘岛7日游现价8999元，包含机票和五星酒店。",
  "intent": "price_inquiry",
  "confidence": 0.95,
  "sources": ["itinerary_jp001"],
  "need_escalation": false
}
```

### Knowledge Base Management

```bash
# 添加产品
curl -X POST http://localhost:8000/api/kb/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "巴厘岛7日游",
    "price": 8999,
    "duration": 7,
    "highlights": ["五星酒店", "私人海滩"]
  }'

# 查询知识库
 curl http://localhost:8000/api/kb/search?q=巴厘岛
```

---

## Testing

```bash
# 运行测试
pytest tests/

# 测试意图分类
python -c "
from chat.engine import IntentClassifier
ic = IntentClassifier()
print(ic.classify('巴厘岛多少钱？'))
"

# 测试RAG检索
python -c "
from chat.engine import RAGRetriever
r = RAGRetriever()
print(r.retrieve('巴厘岛价格', top_k=3))
"
```

---

## Deployment

### Docker Compose

```yaml
version: '3'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - QDRANT_HOST=qdrant
    depends_on:
      - qdrant
      - redis
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  qdrant_storage:
```

启动:
```bash
docker-compose up -d
```

---

## Monitoring

```bash
# 查看日志
docker-compose logs -f api

# 检查服务健康
curl http://localhost:8000/health

# 监控指标 (Prometheus)
curl http://localhost:8000/metrics
```

---

## Troubleshooting

**Q: 启动时报 "Qdrant connection refused"**
```bash
docker ps | grep qdrant  # 检查Qdrant是否运行
docker logs qdrant       # 查看错误日志
```

**Q: LLM调用超时**
```bash
# 检查API Key
echo $DEEPSEEK_API_KEY

# 测试网络
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

**Q: 检索结果为空**
```bash
# 检查知识库是否导入
curl http://localhost:6333/collections/travel_kb

# 重新导入数据
python scripts/load_kb.py
```

---

## File Structure

```
travelcs/
├── src/
│   ├── api/
│   │   └── main.py           # FastAPI入口
│   ├── chat/
│   │   └── engine.py         # 核心引擎
│   ├── kb_builder/           # 知识库构建
│   ├── web/
│   │   └── chat.html         # 聊天界面
│   ├── admin/
│   │   └── dashboard.html    # 管理后台
│   ├── config.py
│   ├── requirements.txt
│   └── run.sh
├── scripts/
│   └── load_kb.py            # 数据导入脚本
├── tests/
├── docker-compose.yml
└── .env.example
```
