"""
QA对抽取器 - 从客服对话提取问答对
"""
import re
from typing import List, Dict
from dataclasses import dataclass
from parsers.chat_parser import Conversation, Message


@dataclass
class QAPair:
    question: str
    answer: str
    confidence: float = 0.0
    category: str = ""
    frequency: int = 1


class QAExtractor:
    """QA对抽取器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.use_llm = api_key is not None
        
        # 常见FAQ分类关键词
        self.category_keywords = {
            "预订": ["预订", "报名", "下单", "购买", "订"],
            "价格": ["价格", "多少钱", "费用", "团费", "优惠"],
            "行程": ["行程", "安排", "路线", "景点", "去哪里"],
            "签证": ["签证", "护照", "入境", "需要办"],
            "酒店": ["酒店", "住宿", "住哪里", "几星"],
            "交通": ["机票", "航班", "接送", "交通"],
            "退改": ["退改", "取消", "退款", "改签", "变更"],
            "儿童": ["儿童", "小孩", "婴儿", "年龄", "收费"],
            "保险": ["保险", "意外险", "旅游险"]
        }
    
    def extract(self, conversations: List[Conversation]) -> List[Dict]:
        """从对话提取QA对"""
        qa_pairs = []
        
        for conv in conversations:
            pairs = self._extract_from_conversation(conv)
            qa_pairs.extend(pairs)
        
        # 合并相似QA
        qa_pairs = self._merge_similar(qa_pairs)
        
        # 转换为输出格式
        return [{
            "id": f"F{str(i+1).zfill(3)}",
            "question": qa.question,
            "answer": qa.answer,
            "category": qa.category,
            "confidence": qa.confidence,
            "frequency": qa.frequency
        } for i, qa in enumerate(qa_pairs)]
    
    def _extract_from_conversation(self, conv: Conversation) -> List[QAPair]:
        """从单一会话提取QA对"""
        pairs = []
        messages = conv.messages
        
        i = 0
        while i < len(messages):
            msg = messages[i]
            
            # 找到客户提问
            if msg.role == "customer":
                question = self._clean_question(msg.content)
                
                # 找后续的客服回复
                answer = ""
                for j in range(i + 1, min(i + 4, len(messages))):
                    if messages[j].role == "agent":
                        answer = messages[j].content
                        break
                
                if answer and self._is_valid_qa(question, answer):
                    confidence = self._score_qa_quality(question, answer)
                    category = self._classify_question(question)
                    
                    pairs.append(QAPair(
                        question=question,
                        answer=self._clean_answer(answer),
                        confidence=confidence,
                        category=category
                    ))
            
            i += 1
        
        return pairs
    
    def _clean_question(self, text: str) -> str:
        """清理问题"""
        # 移除语气词
        text = re.sub(r'[啊呢吧吗嘛]', '', text)
        # 移除多余空格
        text = ' '.join(text.split())
        return text.strip()
    
    def _clean_answer(self, text: str) -> str:
        """清理答案"""
        # 截断过长答案
        if len(text) > 300:
            text = text[:297] + "..."
        return text.strip()
    
    def _is_valid_qa(self, question: str, answer: str) -> bool:
        """判断是否为有效QA对"""
        # 问题太短
        if len(question) < 5:
            return False
        
        # 答案太短或太长
        if len(answer) < 3 or len(answer) > 500:
            return False
        
        # 排除问候语
        greetings = ["你好", "您好", "在吗", "在么", "hi", "hello"]
        if any(g in question for g in greetings) and len(question) < 10:
            return False
        
        # 排除纯表情
        if re.match(r'^[\s\u4e00-\u9fff]*$', question) is None and len(question) < 3:
            return False
        
        return True
    
    def _score_qa_quality(self, question: str, answer: str) -> float:
        """评分QA质量"""
        score = 0.5
        
        # 问题长度适中
        if 10 <= len(question) <= 50:
            score += 0.1
        
        # 答案长度适中
        if 20 <= len(answer) <= 200:
            score += 0.1
        
        # 包含关键信息
        if any(kw in answer for kw in ["元", "天", "包含", "需要", "可以"]):
            score += 0.1
        
        # 答案有结构化信息
        if any(kw in answer for kw in ["1.", "2.", "3.", "首先", "其次"]):
            score += 0.1
        
        return min(score, 1.0)
    
    def _classify_question(self, question: str) -> str:
        """问题分类"""
        for category, keywords in self.category_keywords.items():
            if any(kw in question for kw in keywords):
                return category
        return "其他"
    
    def _merge_similar(self, qa_pairs: List[QAPair]) -> List[QAPair]:
        """合并相似QA"""
        merged = []
        
        for qa in qa_pairs:
            # 查找是否有相似问题
            found = False
            for existing in merged:
                if self._is_similar(qa.question, existing.question):
                    # 保留置信度更高的
                    if qa.confidence > existing.confidence:
                        existing.answer = qa.answer
                        existing.confidence = qa.confidence
                    existing.frequency += 1
                    found = True
                    break
            
            if not found:
                merged.append(qa)
        
        # 按频率和置信度排序
        merged.sort(key=lambda x: (x.frequency, x.confidence), reverse=True)
        
        return merged
    
    def _is_similar(self, q1: str, q2: str) -> bool:
        """判断两个问题是否相似"""
        # 简单实现：包含相同关键词
        # 实际可用：语义相似度模型
        
        # 完全包含
        if q1 in q2 or q2 in q1:
            return True
        
        # 编辑距离
        # 简化：相同关键词数量
        words1 = set(q1)
        words2 = set(q2)
        common = words1 & words2
        
        if len(common) >= min(len(q1), len(q2)) * 0.5:
            return True
        
        return False
