"""
知识融合器 - 去重、对齐、质量评估
"""
from typing import Dict, List
import hashlib


class KnowledgeFusion:
    """知识融合器"""
    
    def __init__(self):
        self.similarity_threshold = 0.8
    
    def fuse(self, kb: Dict) -> Dict:
        """融合知识库"""
        # 1. 产品去重
        kb["products"] = self._deduplicate_products(kb["products"])
        
        # 2. FAQ去重和排序
        kb["faqs"] = self._deduplicate_faqs(kb["faqs"])
        
        # 3. 政策去重
        kb["policies"] = self._deduplicate_policies(kb["policies"])
        
        # 4. 质量评分
        kb = self._quality_assessment(kb)
        
        return kb
    
    def _deduplicate_products(self, products: List[Dict]) -> List[Dict]:
        """产品去重"""
        seen = set()
        unique = []
        
        for p in products:
            # 使用名称+目的地作为key
            key = f"{p.get('name', '')}_{'_'.join(p.get('destination', []))}"
            key_hash = hashlib.md5(key.encode()).hexdigest()
            
            if key_hash not in seen:
                seen.add(key_hash)
                unique.append(p)
            else:
                # 合并信息
                existing = next((x for x in unique if hashlib.md5(
                    f"{x.get('name', '')}_{'_'.join(x.get('destination', []))}".encode()
                ).hexdigest() == key_hash), None)
                
                if existing:
                    # 保留更完整的信息
                    if not existing.get('price') and p.get('price'):
                        existing['price'] = p['price']
                    if not existing.get('highlights') and p.get('highlights'):
                        existing['highlights'] = p['highlights']
        
        return unique
    
    def _deduplicate_faqs(self, faqs: List[Dict]) -> List[Dict]:
        """FAQ去重"""
        seen = set()
        unique = []
        
        for f in faqs:
            question = f.get('question', '')
            # 标准化问题
            key = self._normalize_question(question)
            key_hash = hashlib.md5(key.encode()).hexdigest()
            
            if key_hash not in seen:
                seen.add(key_hash)
                unique.append(f)
            else:
                # 合并频率
                existing = next((x for x in unique if hashlib.md5(
                    self._normalize_question(x.get('question', '')).encode()
                ).hexdigest() == key_hash), None)
                
                if existing:
                    existing['frequency'] = existing.get('frequency', 1) + f.get('frequency', 1)
                    # 保留置信度更高的答案
                    if f.get('confidence', 0) > existing.get('confidence', 0):
                        existing['answer'] = f['answer']
                        existing['confidence'] = f['confidence']
        
        # 按频率和置信度排序
        unique.sort(key=lambda x: (x.get('frequency', 1), x.get('confidence', 0)), reverse=True)
        
        return unique
    
    def _normalize_question(self, question: str) -> str:
        """标准化问题"""
        # 移除标点
        import re
        question = re.sub(r'[？?。！!，,]', '', question)
        # 移除语气词
        question = question.replace('啊', '').replace('呢', '').replace('吗', '')
        # 统一空格
        question = ' '.join(question.split())
        return question.lower()
    
    def _deduplicate_policies(self, policies: List[Dict]) -> List[Dict]:
        """政策去重"""
        seen = set()
        unique = []
        
        for p in policies:
            key = f"{p.get('type', '')}_{p.get('title', '')}"
            key_hash = hashlib.md5(key.encode()).hexdigest()
            
            if key_hash not in seen:
                seen.add(key_hash)
                unique.append(p)
        
        return unique
    
    def _quality_assessment(self, kb: Dict) -> Dict:
        """质量评估"""
        # 产品完整性检查
        for p in kb["products"]:
            required_fields = ['name', 'price', 'duration']
            missing = [f for f in required_fields if not p.get(f)]
            p['quality_score'] = 1.0 - len(missing) * 0.2
            p['missing_fields'] = missing
        
        # FAQ质量检查
        for f in kb["faqs"]:
            score = 0.5
            # 问题长度适中
            q_len = len(f.get('question', ''))
            if 10 <= q_len <= 50:
                score += 0.2
            # 答案长度适中
            a_len = len(f.get('answer', ''))
            if 20 <= a_len <= 300:
                score += 0.2
            # 有分类
            if f.get('category'):
                score += 0.1
            f['quality_score'] = min(score, 1.0)
        
        # 总体统计
        kb["metadata"]["quality_summary"] = {
            "products_avg_score": sum(p.get('quality_score', 0) for p in kb["products"]) / len(kb["products"]) if kb["products"] else 0,
            "faqs_avg_score": sum(f.get('quality_score', 0) for f in kb["faqs"]) / len(kb["faqs"]) if kb["faqs"] else 0,
            "low_confidence_count": sum(1 for f in kb["faqs"] if f.get('confidence', 1) < 0.7)
        }
        
        return kb
