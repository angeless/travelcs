"""
Travel CS AI - Chat Engine
核心对话引擎实现
"""
import json
import re
import hashlib
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field
import requests
import numpy as np

import config


@dataclass
class Message:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Conversation:
    session_id: str
    messages: List[Message] = field(default_factory=list)
    state: str = "init"
    context: Dict = field(default_factory=dict)


class IntentClassifier:
    """意图分类器 - 基于规则和关键词"""
    
    INTENTS = {
        'itinerary_query': {
            'keywords': ['行程', '路线', '推荐', '去哪', '好玩', '哪里', '地方'],
            'priority': 1
        },
        'price_inquiry': {
            'keywords': ['多少钱', '价格', '费用', '团费', '便宜', '贵', '预算'],
            'priority': 1
        },
        'booking': {
            'keywords': ['预订', '报名', '下单', '购买', '订', '怎么买'],
            'priority': 2
        },
        'date_query': {
            'keywords': ['日期', '时间', '什么时候', '几号', '有团吗'],
            'priority': 1
        },
        'visa_query': {
            'keywords': ['签证', '护照', '要办', '入境', '落地签'],
            'priority': 1
        },
        'modification': {
            'keywords': ['改', '换', '退', '取消', '换人', '加人', '减人'],
            'priority': 2
        },
        'complaint': {
            'keywords': ['投诉', '差评', '坑', '骗', '虚假宣传', '不满意'],
            'priority': 5
        },
        'emergency': {
            'keywords': ['急', '紧急', '生病', '受伤', '机场', '航班取消', '被困'],
            'priority': 5
        },
        'general': {
            'keywords': [],
            'priority': 1
        }
    }
    
    def classify(self, message: str) -> Tuple[str, float]:
        """
        返回: (intent, confidence)
        """
        message_lower = message.lower()
        best_intent = 'general'
        best_score = 0
        
        for intent, cfg in self.INTENTS.items():
            score = sum(1 for kw in cfg['keywords'] if kw in message_lower)
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # 计算置信度
        confidence = min(0.5 + best_score * 0.15, 1.0)
        
        # 强制触发词
        for kw in config.HANDOFF_KEYWORDS:
            if kw in message_lower:
                if kw in ['投诉', '赔偿', '律师', '法院']:
                    return ('complaint', 1.0)
                elif kw in ['紧急', '危险', '报警']:
                    return ('emergency', 1.0)
        
        return (best_intent, confidence)
    
    def should_handoff(self, intent: str, confidence: float) -> bool:
        """是否需要转人工"""
        if intent in config.HANDOFF_INTENTS:
            return True
        if confidence < config.CONFIDENCE_THRESHOLD:
            return True
        return False


class SimpleKnowledgeBase:
    """简易知识库 - 内存存储，用于快速启动"""
    
    def __init__(self):
        self.products = {p['id']: p for p in config.SAMPLE_PRODUCTS}
        self.faqs = {f['id']: f for f in config.SAMPLE_FAQS}
        self.conversations: Dict[str, Conversation] = {}
    
    def search_products(self, query: str) -> List[Dict]:
        """搜索产品 - 简单关键词匹配"""
        query_lower = query.lower()
        results = []
        
        for product in self.products.values():
            score = 0
            # 名称匹配
            if query_lower in product['name'].lower():
                score += 10
            # 目的地匹配
            for dest in product['destination']:
                if query_lower in dest.lower():
                    score += 5
            # 亮点匹配
            for highlight in product['highlights']:
                if query_lower in highlight.lower():
                    score += 3
            
            if score > 0:
                results.append((score, product))
        
        results.sort(reverse=True, key=lambda x: x[0])
        return [r[1] for r in results[:3]]
    
    def search_faqs(self, query: str) -> List[Dict]:
        """搜索FAQ"""
        query_lower = query.lower()
        results = []
        
        for faq in self.faqs.values():
            score = 0
            # 问题匹配
            if query_lower in faq['question'].lower():
                score += 10
            # 答案匹配
            if query_lower in faq['answer'].lower():
                score += 3
            # 关键词匹配
            for kw in faq.get('keywords', []):
                if kw in query_lower:
                    score += 5
            
            if score > 0:
                results.append((score, faq))
        
        results.sort(reverse=True, key=lambda x: x[0])
        return [r[1] for r in results[:3]]
    
    def get_or_create_conversation(self, session_id: str) -> Conversation:
        """获取或创建会话"""
        if session_id not in self.conversations:
            self.conversations[session_id] = Conversation(session_id=session_id)
        return self.conversations[session_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话"""
        conv = self.get_or_create_conversation(session_id)
        conv.messages.append(Message(role=role, content=content))
        # 限制历史长度
        if len(conv.messages) > config.MAX_CONTEXT_MESSAGES:
            conv.messages = conv.messages[-config.MAX_CONTEXT_MESSAGES:]


class LLMClient:
    """LLM客户端 - 支持DeepSeek和OpenAI"""
    
    def __init__(self):
        self.deepseek_key = config.DEEPSEEK_API_KEY
        self.openai_key = config.OPENAI_API_KEY
    
    def generate(self, prompt: str, model: str = None) -> str:
        """生成回复"""
        if not model:
            model = config.LLM_MODEL
        
        if 'deepseek' in model.lower() and self.deepseek_key:
            return self._call_deepseek(prompt, model)
        elif self.openai_key:
            return self._call_openai(prompt, model)
        else:
            return "[LLM未配置，返回默认回复]"
    
    def _call_deepseek(self, prompt: str, model: str) -> str:
        """调用DeepSeek API"""
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.deepseek_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": config.LLM_TEMPERATURE,
                    "max_tokens": config.LLM_MAX_TOKENS
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"DeepSeek API error: {e}")
            return self._fallback_response()
    
    def _call_openai(self, prompt: str, model: str) -> str:
        """调用OpenAI API"""
        try:
            import openai
            openai.api_key = self.openai_key
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._fallback_response()
    
    def _fallback_response(self) -> str:
        """兜底回复"""
        return "抱歉，我暂时无法处理这个问题，请稍后再试或联系人工客服。"


class ChatEngine:
    """对话引擎 - 主入口"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.kb = SimpleKnowledgeBase()
        self.llm = LLMClient()
    
    def process(self, session_id: str, message: str) -> Dict:
        """
        处理用户消息
        
        Returns:
            {
                'response': str,
                'intent': str,
                'confidence': float,
                'need_escalation': bool,
                'sources': list
            }
        """
        # 1. 意图识别
        intent, confidence = self.intent_classifier.classify(message)
        
        # 2. 检查是否需要转人工
        if self.intent_classifier.should_handoff(intent, confidence):
            response = "理解您的紧急情况，我立即为您转接人工客服处理。"
            self._save_message(session_id, 'user', message, intent)
            self._save_message(session_id, 'assistant', response, intent, handoff=True)
            return {
                'response': response,
                'intent': intent,
                'confidence': confidence,
                'need_escalation': True,
                'sources': []
            }
        
        # 3. 知识检索
        products = self.kb.search_products(message)
        faqs = self.kb.search_faqs(message)
        
        # 4. 生成回复
        response = self._generate_response(message, intent, products, faqs)
        
        # 5. 保存对话
        self._save_message(session_id, 'user', message, intent)
        self._save_message(session_id, 'assistant', response, intent, 
                          sources={'products': products, 'faqs': faqs})
        
        return {
            'response': response,
            'intent': intent,
            'confidence': confidence,
            'need_escalation': False,
            'sources': {
                'products': [p['id'] for p in products],
                'faqs': [f['id'] for f in faqs]
            }
        }
    
    def _generate_response(self, message: str, intent: str, 
                          products: List[Dict], faqs: List[Dict]) -> str:
        """生成回复"""
        
        # 优先级1: 直接匹配FAQ
        if faqs and intent in ['general', 'price_inquiry', 'date_query']:
            return faqs[0]['answer']
        
        # 优先级2: 产品推荐
        if products and intent in ['itinerary_query', 'booking']:
            p = products[0]
            highlights = '、'.join(p['highlights'][:3])
            return f"推荐【{p['name']}】，{p['duration']}天行程，价格¥{p['price']}。包含{highlights}。需要了解详情吗？"
        
        # 优先级3: 价格咨询
        if intent == 'price_inquiry':
            if products:
                prices = [f"{p['name']}: ¥{p['price']}" for p in products[:2]]
                return "我们的产品价格：\n" + "\n".join(prices) + "\n请问您对哪个感兴趣？"
            return "我们有多个价位的产品，从¥4999到¥12999不等。您想了解哪个目的地？"
        
        # 优先级4: 使用LLM生成
        if config.DEEPSEEK_API_KEY or config.OPENAI_API_KEY:
            context = self._build_context(products, faqs)
            prompt = f"用户问题: {message}\n\n相关知识:\n{context}\n\n请基于以上知识回答，如果不确定请说需要确认。"
            return self.llm.generate(prompt)
        
        # 兜底回复
        return "您好，我是您的旅游顾问。请问您想了解哪个目的地或产品？"
    
    def _build_context(self, products: List[Dict], faqs: List[Dict]) -> str:
        """构建上下文"""
        context = []
        for p in products[:2]:
            context.append(f"产品: {p['name']}, 价格¥{p['price']}, {p['duration']}天")
        for f in faqs[:2]:
            context.append(f"Q: {f['question']}\nA: {f['answer']}")
        return "\n".join(context)
    
    def _save_message(self, session_id: str, role: str, content: str, 
                     intent: str = None, handoff: bool = False, sources: Dict = None):
        """保存消息"""
        self.kb.add_message(session_id, role, content)
    
    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """获取会话历史"""
        return self.kb.conversations.get(session_id)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total_msgs = sum(len(c.messages) for c in self.kb.conversations.values())
        return {
            'sessions': len(self.kb.conversations),
            'total_messages': total_msgs,
            'products': len(self.kb.products),
            'faqs': len(self.kb.faqs)
        }


# 全局引擎实例
engine = ChatEngine()
