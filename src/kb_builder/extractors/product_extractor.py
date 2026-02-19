"""
产品信息抽取器 - 使用LLM从文档提取结构化产品信息
"""
import json
import re
from typing import Dict, Optional


class ProductExtractor:
    """产品信息抽取器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        # 如果API key为空，使用规则抽取
        self.use_llm = api_key is not None
    
    def extract(self, doc_text: str) -> Optional[Dict]:
        """从产品文档提取信息"""
        if self.use_llm:
            return self._extract_with_llm(doc_text)
        else:
            return self._extract_with_rules(doc_text)
    
    def _extract_with_llm(self, doc_text: str) -> Dict:
        """使用LLM抽取"""
        # 这里接入实际的LLM API
        # 目前使用模拟实现
        prompt = f"""
请从以下旅游产品文档中提取结构化信息，返回JSON格式:

文档内容:
{doc_text[:2000]}

需要提取的字段:
- name: 产品名称
- price: 价格 (数字)
- duration: 天数 (数字)
- destination: 目的地 (列表)
- highlights: 亮点 (列表)
- inclusions: 包含项目 (列表)
- exclusions: 不包含项目 (列表)
- visa_info: 签证信息
- booking_policy: 预订政策
- cancellation_policy: 退改政策

仅返回JSON，不要其他内容。
"""
        # 模拟LLM响应
        return self._mock_llm_extraction(doc_text)
    
    def _mock_llm_extraction(self, doc_text: str) -> Dict:
        """模拟LLM抽取 (实际部署时替换为真实API)"""
        # 尝试用规则提取一些基本信息
        product = {
            "name": self._extract_name(doc_text),
            "price": self._extract_price(doc_text),
            "duration": self._extract_duration(doc_text),
            "destination": self._extract_destination(doc_text),
            "highlights": self._extract_highlights(doc_text),
            "inclusions": [],
            "exclusions": [],
            "visa_info": self._extract_visa(doc_text),
            "booking_policy": "",
            "cancellation_policy": self._extract_cancellation(doc_text),
            "confidence": 0.7,
            "source_text": doc_text[:500]
        }
        return product
    
    def _extract_with_rules(self, doc_text: str) -> Dict:
        """使用规则抽取"""
        return self._mock_llm_extraction(doc_text)
    
    def _extract_name(self, text: str) -> str:
        """提取产品名称"""
        # 找标题或第一行
        lines = text.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 5 and '游' in line or '之旅' in line:
                return line
        return lines[0] if lines else "未知产品"
    
    def _extract_price(self, text: str) -> float:
        """提取价格"""
        # 匹配 ¥8999 / 8999元 / 价格：8999
        patterns = [
            r'[¥￥]\s*(\d{3,5})',
            r'(\d{3,5})\s*元',
            r'价格[:：]?\s*(\d{3,5})',
            r'团费[:：]?\s*(\d{3,5})'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return 0.0
    
    def _extract_duration(self, text: str) -> int:
        """提取天数"""
        patterns = [
            r'(\d+)\s*天',
            r'(\d+)\s*日',
            r'(\d+)\s*晚'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return 0
    
    def _extract_destination(self, text: str) -> list:
        """提取目的地"""
        # 常见旅游目的地关键词
        destinations = []
        keywords = ['巴厘岛', '东京', '普吉岛', '马尔代夫', '巴黎', '伦敦', '纽约', 
                   '悉尼', '迪拜', '新加坡', '曼谷', '首尔', '大阪', '京都']
        for kw in keywords:
            if kw in text:
                destinations.append(kw)
        return destinations
    
    def _extract_highlights(self, text: str) -> list:
        """提取亮点"""
        highlights = []
        # 找"亮点"、"特色"后面的内容
        patterns = [
            r'亮点[:：]\s*([^\n]+)',
            r'特色[:：]\s*([^\n]+)',
            r'行程.*?(?:包括|包含).*?([^
]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                items = match.group(1).split('、')
                highlights.extend([i.strip() for i in items if len(i.strip()) > 1])
        return highlights[:5]  # 最多5个
    
    def _extract_visa(self, text: str) -> str:
        """提取签证信息"""
        patterns = [
            r'签证[:：]\s*([^\n]+)',
            r'(免签|落地签|需提前办理签证)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""
    
    def _extract_cancellation(self, text: str) -> str:
        """提取退改政策"""
        patterns = [
            r'退改.*?(?:政策)?[:：]\s*([^\n]+)',
            r'取消.*?(?:政策)?[:：]\s*([^\n]+)',
            r'退款.*?(?:政策)?[:：]\s*([^\n]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""
