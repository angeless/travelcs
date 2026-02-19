# 旅游产品智能客服 - 知识库建模与索引策略

> **任务**: T3 - 知识库建模与索引策略  
> **交付物**: `docs/knowledge-base-design.md`  
> **负责人**: 析理  
> **日期**: 2026-02-19

---

## 一、数据结构定义

### 1.1 产品知识 Schema

```json
{
  "product": {
    "id": "P20250219001",
    "name": "巴厘岛7日尊享游",
    "category": "海岛游",
    "destination": ["印度尼西亚", "巴厘岛"],
    "duration": 7,
    "price": {
      "adult": 8999,
      "child": 6999,
      "single_room_supplement": 1500
    },
    "highlights": ["五星酒店", "私人海滩", "SPA体验"],
    "itinerary": [
      {"day": 1, "title": "抵达巴厘岛", "activities": [...]},
      {"day": 2, "title": "乌布文化之旅", "activities": [...]}
    ],
    "inclusions": ["往返机票", "酒店住宿", "景点门票"],
    "exclusions": ["个人消费", "签证费"],
    "visa_info": "落地签，费用35美元",
    "booking_policy": {
      "advance_days": 7,
      "deposit_percent": 30,
      "balance_due_days": 3
    },
    "cancellation_policy": {
      "7_days": "全额退款",
      "3_7_days": "扣30%",
      "1_3_days": "扣50%",
      "0_1_days": "不予退款"
    },
    "valid_from": "2026-03-01",
    "valid_to": "2026-12-31",
    "status": "active"
  }
}
```

### 1.2 FAQ Schema

```json
{
  "faq": {
    "id": "FAQ001",
    "category": "预订相关",
    "question": "提前多久预订？",
    "answer": "常规线路建议提前7天预订，旺季建议提前15-30天，热门线路可能需要更早。",
    "keywords": ["预订", "提前", "时间", "多久"],
    "related_products": ["all"],
    "frequency": 95,
    "last_updated": "2026-02-19"
  }
}
```

### 1.3 政策文档 Schema

```json
{
  "policy": {
    "id": "POL001",
    "type": "退改政策",
    "title": "标准退改规则",
    "content": "...",
    "applies_to": ["跟团游", "自由行"],
    "exceptions": ["特价产品不退不改"],
    "version": "2026-v1",
    "effective_date": "2026-01-01"
  }
}
```

### 1.4 历史对话 Schema

```json
{
  "conversation": {
    "session_id": "SESS001",
    "user_id": "USER001",
    "channel": "whatsapp",
    "messages": [
      {
        "role": "user",
        "content": "巴厘岛有什么好玩的？",
        "timestamp": "2026-02-19T10:00:00Z",
        "intent": "产品咨询",
        "entities": {"destination": "巴厘岛"}
      },
      {
        "role": "assistant",
        "content": "巴厘岛有海滩、乌布、火山...",
        "timestamp": "2026-02-19T10:00:05Z",
        "sources": ["P20250219001"]
      }
    ],
    "satisfaction_score": 4.5,
    "handoff_to_human": false
  }
}
```

---

## 二、向量索引策略

### 2.1 分块 (Chunking) 策略

```
┌─────────────────────────────────────────────────────────────┐
│                    文档分块策略                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  原始文档                                                    │
│  ├─ 产品详情页 (2000字)                                      │
│  ├─ FAQ列表 (500条)                                          │
│  └─ 政策文档 (3000字)                                        │
│                                                             │
│  分块策略                                                    │
│  ├── 产品文档                                                │
│  │   ├─ Chunk 1: 基本信息 (名称/价格/天数)                   │
│  │   ├─ Chunk 2: 行程亮点                                    │
│  │   ├─ Chunk 3: 每日行程详情                                │
│  │   └─ Chunk 4: 预订/退改政策                               │
│  │   【Chunk大小: 300-500 tokens】                           │
│  │   【重叠: 50 tokens (保留上下文)】                        │
│  │                                                          │
│  ├── FAQ                                                     │
│  │   ├─ 每条FAQ独立成块                                      │
│  │   ├─ 元数据: 问题+答案+关键词                             │
│  │   └─ 向量化: 问题(0.7权重) + 答案(0.3权重)                │
│  │                                                          │
│  └── 政策文档                                                │
│      ├─ 按条款分块                                           │
│      ├─ 标题作为上下文前缀                                   │
│      └─ 保留层级结构                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 分块参数配置

```python
# 分块配置
CHUNK_CONFIG = {
    "product": {
        "chunk_size": 400,        # tokens
        "chunk_overlap": 50,      # tokens
        "separator": ["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
        "min_chunk_size": 100
    },
    "faq": {
        "chunk_size": 300,
        "chunk_overlap": 0,       # FAQ独立，不需要重叠
        "separator": ["\nQ:", "\nA:"],
        "metadata_enrichment": True
    },
    "policy": {
        "chunk_size": 500,
        "chunk_overlap": 100,     # 政策条款间保留上下文
        "separator": ["\n第", "\n## ", "\n\n", "\n"],
        "hierarchy_preservation": True
    }
}
```

### 2.3 Embedding 策略

```python
# Embedding 配置
EMBEDDING_CONFIG = {
    "model": "BAAI/bge-large-zh-v1.5",  # 中文优化
    "dimensions": 1024,
    "normalize": True,
    "batch_size": 32,
    
    # 查询增强
    "query_expansion": {
        "enabled": True,
        "synonyms": {
            "价格": ["多少钱", "费用", "花费", "团费"],
            "预订": ["报名", "下单", "购买", "定"],
            "取消": ["退款", "退订", "不去了"]
        }
    }
}
```

---

## 三、知识更新流程

### 3.1 增量更新机制

```
┌─────────────────────────────────────────────────────────────┐
│                   知识更新流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 变更检测                                                 │
│     ├─ 文件MD5对比                                           │
│     ├─ 数据库更新时间戳                                      │
│     └─ API变更推送                                           │
│                                                             │
│  2. 增量处理                                                 │
│     ├─ 新增文档 → 全量处理                                   │
│     ├─ 修改文档 → 标记旧向量删除 + 新增向量                  │
│     └─ 删除文档 → 软删除向量 (保留30天)                      │
│                                                             │
│  3. 重新索引                                                 │
│     ├─ 仅处理变更的chunk                                     │
│     ├─ 批量Embedding (32条/批)                               │
│     └─ 原子性提交                                            │
│                                                             │
│  4. 验证回滚                                                 │
│     ├─ 抽样检索测试                                          │
│     ├─ 新旧结果对比                                          │
│     └─ 异常自动回滚                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 更新触发方式

| 触发方式 | 频率 | 适用场景 |
|---------|------|---------|
| **定时任务** | 每日凌晨2点 | 批量同步外部数据源 |
| **Webhook** | 实时 | CMS内容更新 |
| **手动触发** | 按需 | 紧急修正错误信息 |
| **文件监听** | 近实时 | 本地文档变更 |

### 3.3 版本管理

```json
{
  "version_control": {
    "strategy": "append_only",
    "retention": {
      "versions": 5,
      "days": 90
    },
    "rollback": {
      "enabled": true,
      "auto_rollback_on_error": true
    }
  }
}
```

---

## 四、多语言知识管理

### 4.1 语言检测与路由

```
用户消息
    │
    ▼
┌─────────────────┐
│ 语言检测 (langdetect)
│ ├─ 中文 → 中文知识库
│ ├─ 英文 → 英文知识库
│ ├─ 日文 → 日文知识库 (fallback中文)
│ └─ 其他 → 英文知识库 (fallback中文)
└─────────────────┘
```

### 4.2 多语言知识库架构

```
knowledge_base/
├── zh-CN/                    # 简体中文 (主库)
│   ├── products/
│   ├── faqs/
│   └── policies/
├── en/                       # 英文
│   ├── products/
│   ├── faqs/
│   └── policies/
├── ja/                       # 日文
│   └── ...
└── _sync/                    # 同步映射表
    ├── product_translations.json
    └── terminology_glossary.json
```

### 4.3 翻译策略

| 内容类型 | 策略 | 工具 |
|---------|------|------|
| 产品名称 | 保留原文 + 括号翻译 | 术语表 |
| 价格/数字 | 自动转换 | 格式化函数 |
| 政策条款 | 专业翻译 | DeepL API |
| FAQ | 机器翻译 + 人工审核 | GPT-4 |

---

## 五、检索优化策略

### 5.1 混合检索

```python
# 混合检索配置
RETRIEVAL_CONFIG = {
    "semantic_search": {
        "weight": 0.7,
        "top_k": 10,
        "similarity_threshold": 0.75
    },
    "keyword_search": {
        "weight": 0.3,
        "fields": ["title", "keywords", "tags"],
        "boost": 2.0
    },
    "reranking": {
        "enabled": True,
        "model": "cross-encoder",
        "top_n": 5
    }
}
```

### 5.2 重排序 (Re-ranking)

```
初步检索 (Top-10)
    │
    ▼
┌─────────────────────────────────────┐
│ Cross-Encoder 重排序                 │
│ ├─ Query + Doc1 → Score: 0.92       │
│ ├─ Query + Doc2 → Score: 0.85       │
│ ├─ Query + Doc3 → Score: 0.78       │
│ ...                                 │
└─────────────────────────────────────┘
    │
    ▼
最终返回 (Top-5)
```

---

## 六、数据存储设计

### 6.1 SQLite 表结构

```sql
-- 产品表
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    destination TEXT,
    duration INTEGER,
    price_adult INTEGER,
    price_child INTEGER,
    json_data TEXT,          -- 完整JSON
    valid_from DATE,
    valid_to DATE,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 向量索引表 (QMD/Chroma)
CREATE TABLE vector_index (
    id TEXT PRIMARY KEY,
    doc_id TEXT,             -- 关联产品/FAQ ID
    doc_type TEXT,           -- product/faq/policy
    chunk_index INTEGER,
    content TEXT,            -- 文本内容
    embedding BLOB,          -- 向量数据
    metadata TEXT,           -- JSON元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FAQ表
CREATE TABLE faqs (
    id TEXT PRIMARY KEY,
    category TEXT,
    question TEXT,
    answer TEXT,
    keywords TEXT,           -- JSON数组
    frequency INTEGER,
    last_updated TIMESTAMP
);

-- 对话记录表
CREATE TABLE conversations (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    channel TEXT,
    messages TEXT,           -- JSON数组
    satisfaction_score REAL,
    handoff_to_human BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 七、性能优化

### 7.1 索引优化

```sql
-- 向量检索优化
CREATE INDEX idx_vector_doc_type ON vector_index(doc_type);
CREATE INDEX idx_vector_doc_id ON vector_index(doc_id);

-- FAQ查询优化
CREATE INDEX idx_faq_category ON faqs(category);
CREATE INDEX idx_faq_keywords ON faqs(keywords);

-- 产品查询优化
CREATE INDEX idx_product_category ON products(category);
CREATE INDEX idx_product_destination ON products(destination);
CREATE INDEX idx_product_valid ON products(valid_from, valid_to);
```

### 7.2 缓存策略

```python
CACHE_CONFIG = {
    "hot_faqs": {
        "ttl": 3600,          # 1小时
        "max_size": 100
    },
    "product_cache": {
        "ttl": 1800,          # 30分钟
        "max_size": 50
    },
    "embedding_cache": {
        "ttl": 86400,         # 24小时
        "max_size": 1000
    }
}
```

---

## 八、交付清单

- [x] 数据结构定义 (产品/FAQ/政策/对话 Schema)
- [x] 向量索引策略 (分块/chunking参数)
- [x] 知识更新流程 (增量更新/版本管理)
- [x] 多语言知识管理方案
- [x] 检索优化策略 (混合检索/重排序)
- [x] 数据存储设计 (SQLite表结构)
- [x] 性能优化方案

**下一步**: T4 - MVP原型开发
