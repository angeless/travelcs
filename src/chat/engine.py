"""
旅游客服AI - 核心对话引擎
"""
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import config

class IntentClassifier:
    """意图识别器"""
    
    INTENTS = {
        "urgent": ["紧急", "危险", "受伤", "丢失", "报警", "医院", "急诊"],
        "complaint": ["投诉", "不满", "差劲", "糟糕", "骗人"],
        "refund": ["退款", "退钱", "退费", "赔偿", "补偿"],
        "booking": ["预订", "报名", "下单", "购买", "定"],
        "consult": ["咨询", "了解", "问问", "介绍", "推荐"],
        "payment": ["付款", "支付", "发票", "多少钱", "价格"]
    }
    
    def classify(self, message: str) -> Tuple[str, float]:
        """返回意图类型和置信度"""
        message = message.lower()
        scores = {}
        
        for intent, keywords in self.INTENTS.items():
            score = sum(1 for kw in keywords if kw in message)
            if score > 0:
                scores[intent] = score / len(keywords)
        
        if not scores:
            return "general", 0.5
        
        best_intent = max(scores, key=scores.get)
        return best_intent, min(scores[best_intent] + 0.3, 1.0)
    
    def should_handoff(self, message: str, intent: str, confidence: float) -> bool:
        """判断是否需要转人工"""
        # 关键词触发
        for kw in config.HANDOFF_KEYWORDS:
            if kw in message:
                return True
        
        # 紧急意图
        if intent == "urgent":
            return True
        
        # 低置信度
        if confidence < config.HANDOFF_CONFIDENCE_THRESHOLD:
            return True
        
        return False


class KnowledgeBase:
    """简易知识库 (MVP版本使用内存存储)"""
    
    def __init__(self):
        self.products = {p["id"]: p for p in config.SAMPLE_PRODUCTS}
        self.faqs = {f["id"]: f for f in config.SAMPLE_FAQS}
        self.conversations = {}  # session_id -> messages
    
    def search_products(self, query: str) -> List[Dict]:
        """搜索产品 (简易关键词匹配)"""
        results = []
        query_lower = query.lower()
        
        for product in self.products.values():
            score = 0
            if query_lower in product["name"].lower():
                score += 3
            if any(query_lower in h for h in product["highlights"]):
                score += 1
            if score > 0:
                results.append((score, product))
        
        results.sort(reverse=True)
        return [r[1] for r in results[:3]]
    
    def search_faqs(self, query: str) -> List[Dict]:
        """搜索FAQ"""
        results = []
        query_lower = query.lower()
        
        for faq in self.faqs.values():
            score = 0
            if query_lower in faq["question"].lower():
                score += 3
            if query_lower in faq["answer"].lower():
                score += 1
            if score > 0:
                results.append((score, faq))
        
        results.sort(reverse=True)
        return [r[1] for r in results[:3]]
    
    def get_context(self, session_id: str) -> List[Dict]:
        """获取对话上下文"""
        return self.conversations.get(session_id, [])[-config.MAX_CONTEXT_MESSAGES:]
    
    def save_message(self, session_id: str, role: str, content: str, metadata: dict = None):
        """保存对话消息"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "products": len(self.products),
            "faqs": len(self.faqs),
            "sessions": len(self.conversations),
            "total_messages": sum(len(msgs) for msgs in self.conversations.values())
        }


class ChatEngine:
    """对话引擎"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.kb = KnowledgeBase()
    
    def process(self, session_id: str, message: str) -> Dict:
        """处理用户消息"""
        # 1. 意图识别
        intent, confidence = self.intent_classifier.classify(message)
        
        # 2. 检查是否需要转人工
        if self.intent_classifier.should_handoff(message, intent, confidence):
            response = config.RESPONSE_TEMPLATES["handoff"]
            self.kb.save_message(session_id, "user", message, {"intent": intent, "handoff": True})
            self.kb.save_message(session_id, "assistant", response, {"handoff": True})
            return {
                "response": response,
                "intent": intent,
                "confidence": confidence,
                "handoff": True,
                "sources": []
            }
        
        # 3. 检索知识
        products = self.kb.search_products(message)
        faqs = self.kb.search_faqs(message)
        
        # 4. 生成回复
        response = self._generate_response(message, intent, products, faqs)
        
        # 5. 保存对话
        self.kb.save_message(session_id, "user", message, {"intent": intent})
        self.kb.save_message(session_id, "assistant", response, {"sources": [p["id"] for p in products] + [f["id"] for f in faqs]})
        
        return {
            "response": response,
            "intent": intent,
            "confidence": confidence,
            "handoff": False,
            "sources": {
                "products": products,
                "faqs": faqs
            }
        }
    
    def _generate_response(self, message: str, intent: str, products: List[Dict], faqs: List[Dict]) -> str:
        """生成回复 (MVP版本：规则模板，后续接入LLM)"""
        
        # 如果匹配到FAQ，直接返回答案
        if faqs and intent in ["consult", "general"]:
            return faqs[0]["answer"]
        
        # 产品推荐
        if products and "订" in message or "买" in message or "推荐" in message:
            p = products[0]
            return f"推荐您【{p['name']}】，价格¥{p['price']}，包含{', '.join(p['highlights'])}。需要了解更多详情吗？"
        
        # 价格咨询
        if intent == "payment":
            if products:
                prices = [f"{p['name']}: ¥{p['price']}" for p in products[:2]]
                return "我们的产品价格如下：\n" + "\n".join(prices) + "\n请问您对哪个产品感兴趣？"
            return "我们有多个价位的线路，从¥4999到¥12999不等，您想了解哪个目的地呢？"
        
        # 问候
        if any(kw in message for kw in ["你好", "您好", "在吗", "hi", "hello"]):
            return config.RESPONSE_TEMPLATES["greeting"]
        
        # 默认回复
        if products or faqs:
            context = []
            if products:
                context.append(f"产品：{products[0]['name']}")
            if faqs:
                context.append(f"FAQ：{faqs[0]['question']}")
            return f"关于您的问题，我找到了以下信息：{', '.join(context)}。请问具体想了解哪方面？"
        
        return config.RESPONSE_TEMPLATES["not_found"]
    
    def get_history(self, session_id: str) -> List[Dict]:
        """获取对话历史"""
        return self.kb.get_context(session_id)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return self.kb.get_stats()


# 全局引擎实例
engine = ChatEngine()
