"""
知识库构建工具 - 主入口
从原始数据自动构建结构化知识库
"""
import argparse
import json
import os
from pathlib import Path
from typing import List, Dict

from parsers.document_parser import DocumentParser
from parsers.order_parser import OrderParser
from parsers.chat_parser import ChatParser
from extractors.product_extractor import ProductExtractor
from extractors.qa_extractor import QAExtractor
from analyzers.order_analyzer import OrderAnalyzer
from analyzers.knowledge_fusion import KnowledgeFusion


class KnowledgeBuilder:
    """知识库构建器"""
    
    def __init__(self, llm_api_key: str = None):
        self.doc_parser = DocumentParser()
        self.order_parser = OrderParser()
        self.chat_parser = ChatParser()
        self.product_extractor = ProductExtractor(llm_api_key)
        self.qa_extractor = QAExtractor(llm_api_key)
        self.order_analyzer = OrderAnalyzer()
        self.fusion = KnowledgeFusion()
        
    def build_from_documents(self, docs_dir: str) -> List[Dict]:
        """从产品文档构建知识"""
        products = []
        docs_path = Path(docs_dir)
        
        for file_path in docs_path.rglob('*'):
            if file_path.suffix.lower() in ['.pdf', '.docx', '.doc', '.txt', '.html']:
                print(f"📄 处理文档: {file_path}")
                text = self.doc_parser.parse(file_path)
                if text:
                    product = self.product_extractor.extract(text)
                    if product:
                        products.append(product)
                        
        return products
    
    def build_from_orders(self, orders_file: str) -> Dict:
        """从历史订单分析知识"""
        print(f"📊 分析订单: {orders_file}")
        orders = self.order_parser.parse(orders_file)
        insights = self.order_analyzer.analyze(orders)
        return insights
    
    def build_from_chats(self, chats_file: str) -> List[Dict]:
        """从聊天记录提取QA"""
        print(f"💬 处理聊天记录: {chats_file}")
        conversations = self.chat_parser.parse(chats_file)
        qa_pairs = self.qa_extractor.extract(conversations)
        return qa_pairs
    
    def build(self, 
              products_dir: str = None,
              orders_file: str = None, 
              chats_file: str = None,
              output_file: str = "knowledge_base.json") -> Dict:
        """构建完整知识库"""
        
        kb = {
            "products": [],
            "faqs": [],
            "policies": [],
            "metadata": {
                "sources": [],
                "generated_at": None,
                "stats": {}
            }
        }
        
        # 1. 处理产品文档
        if products_dir and os.path.exists(products_dir):
            products = self.build_from_documents(products_dir)
            kb["products"] = products
            kb["metadata"]["sources"].append(f"products:{products_dir}")
            print(f"✅ 提取 {len(products)} 个产品")
        
        # 2. 分析订单数据
        if orders_file and os.path.exists(orders_file):
            insights = self.build_from_orders(orders_file)
            # 从洞察生成FAQ和政策
            kb["faqs"].extend(insights.get("faq_candidates", []))
            kb["policies"].extend(insights.get("policies", []))
            kb["metadata"]["sources"].append(f"orders:{orders_file}")
            print(f"✅ 从订单提取 {len(insights.get('faq_candidates', []))} 个FAQ")
        
        # 3. 提取对话QA
        if chats_file and os.path.exists(chats_file):
            qa_pairs = self.build_from_chats(chats_file)
            kb["faqs"].extend(qa_pairs)
            kb["metadata"]["sources"].append(f"chats:{chats_file}")
            print(f"✅ 从对话提取 {len(qa_pairs)} 个QA对")
        
        # 4. 知识融合与去重
        print("🔄 融合知识...")
        kb = self.fusion.fuse(kb)
        
        # 5. 生成元数据
        kb["metadata"]["generated_at"] = self._get_timestamp()
        kb["metadata"]["stats"] = {
            "products": len(kb["products"]),
            "faqs": len(kb["faqs"]),
            "policies": len(kb["policies"])
        }
        
        # 6. 保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        
        print(f"\n✨ 知识库已生成: {output_file}")
        print(f"   产品: {kb['metadata']['stats']['products']}")
        print(f"   FAQ: {kb['metadata']['stats']['faqs']}")
        print(f"   政策: {kb['metadata']['stats']['policies']}")
        
        return kb
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    parser = argparse.ArgumentParser(description='自动构建旅游客服知识库')
    parser.add_argument('--products-dir', '-p', help='产品文档目录')
    parser.add_argument('--orders-file', '-o', help='历史订单CSV文件')
    parser.add_argument('--chats-file', '-c', help='聊天记录JSON文件')
    parser.add_argument('--output', '-O', default='knowledge_base.json', help='输出文件')
    parser.add_argument('--llm-key', '-k', help='LLM API Key')
    
    args = parser.parse_args()
    
    if not any([args.products_dir, args.orders_file, args.chats_file]):
        parser.print_help()
        print("\n❌ 至少指定一个数据源")
        return
    
    builder = KnowledgeBuilder(llm_api_key=args.llm_key)
    builder.build(
        products_dir=args.products_dir,
        orders_file=args.orders_file,
        chats_file=args.chats_file,
        output_file=args.output
    )


if __name__ == '__main__':
    main()
