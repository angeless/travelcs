"""
订单数据解析器
"""
import csv
import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Order:
    order_id: str
    product_name: str
    price: float
    customer_id: str
    status: str  # completed, refunded, cancelled
    refund_reason: str = ""
    created_at: str = ""


class OrderParser:
    """订单数据解析器"""
    
    def parse(self, file_path: str) -> List[Order]:
        """解析订单文件"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            return self._parse_csv(path)
        elif suffix == '.json':
            return self._parse_json(path)
        elif suffix in ['.xlsx', '.xls']:
            return self._parse_excel(path)
        else:
            raise ValueError(f"不支持的订单格式: {suffix}")
    
    def _parse_csv(self, file_path: Path) -> List[Order]:
        """解析CSV"""
        orders = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                orders.append(Order(
                    order_id=row.get('order_id', ''),
                    product_name=row.get('product_name', ''),
                    price=float(row.get('price', 0) or 0),
                    customer_id=row.get('customer_id', ''),
                    status=row.get('status', ''),
                    refund_reason=row.get('refund_reason', ''),
                    created_at=row.get('created_at', '')
                ))
        return orders
    
    def _parse_json(self, file_path: Path) -> List[Order]:
        """解析JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        orders = []
        for item in data:
            orders.append(Order(
                order_id=item.get('order_id', ''),
                product_name=item.get('product_name', ''),
                price=float(item.get('price', 0)),
                customer_id=item.get('customer_id', ''),
                status=item.get('status', ''),
                refund_reason=item.get('refund_reason', ''),
                created_at=item.get('created_at', '')
            ))
        return orders
    
    def _parse_excel(self, file_path: Path) -> List[Order]:
        """解析Excel"""
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            orders = []
            for _, row in df.iterrows():
                orders.append(Order(
                    order_id=str(row.get('order_id', '')),
                    product_name=str(row.get('product_name', '')),
                    price=float(row.get('price', 0)),
                    customer_id=str(row.get('customer_id', '')),
                    status=str(row.get('status', '')),
                    refund_reason=str(row.get('refund_reason', '')),
                    created_at=str(row.get('created_at', ''))
                ))
            return orders
        except ImportError:
            print("📦 安装pandas: pip install pandas openpyxl")
            raise
