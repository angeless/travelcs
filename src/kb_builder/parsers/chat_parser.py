"""
聊天记录解析器
支持JSON格式和微信导出格式
"""
import json
import re
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str  # customer, agent
    content: str
    timestamp: str = ""


@dataclass
class Conversation:
    session_id: str
    messages: List[Message] = field(default_factory=list)


class ChatParser:
    """聊天记录解析器"""
    
    def parse(self, file_path: str) -> List[Conversation]:
        """解析聊天记录"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.json':
            return self._parse_json(path)
        elif suffix == '.txt':
            return self._parse_wechat_txt(path)
        else:
            raise ValueError(f"不支持的聊天记录格式: {suffix}")
    
    def _parse_json(self, file_path: Path) -> List[Conversation]:
        """解析标准JSON格式"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conversations = []
        
        # 支持两种格式: 列表或字典
        if isinstance(data, list):
            for item in data:
                conv = self._convert_to_conversation(item)
                conversations.append(conv)
        elif isinstance(data, dict):
            # 单一会话或会话字典
            if 'messages' in data:
                conversations.append(self._convert_to_conversation(data))
            else:
                for session_id, conv_data in data.items():
                    conv = self._convert_to_conversation(conv_data)
                    conv.session_id = session_id
                    conversations.append(conv)
        
        return conversations
    
    def _convert_to_conversation(self, data: Dict) -> Conversation:
        """转换为Conversation对象"""
        conv = Conversation(
            session_id=data.get('session_id', data.get('id', 'unknown'))
        )
        
        for msg_data in data.get('messages', []):
            msg = Message(
                role=self._normalize_role(msg_data.get('role', '')),
                content=msg_data.get('content', ''),
                timestamp=msg_data.get('timestamp', '')
            )
            conv.messages.append(msg)
        
        return conv
    
    def _normalize_role(self, role: str) -> str:
        """统一角色名称"""
        role = role.lower()
        if role in ['customer', 'user', '客户', '顾客', '买家']:
            return 'customer'
        elif role in ['agent', 'staff', '客服', '顾问', '卖家']:
            return 'agent'
        return role
    
    def _parse_wechat_txt(self, file_path: Path) -> List[Conversation]:
        """解析微信导出文本格式"""
        conversations = []
        current_conv = Conversation(session_id="wechat_export")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 微信格式示例:
        # 2025-01-15 10:30:00 客户A
        # 你好，请问巴厘岛多少钱？
        # 2025-01-15 10:31:00 客服B
        # 您好，巴厘岛7日游8999元
        
        pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+)'
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            match = re.match(pattern, line)
            
            if match and i + 1 < len(lines):
                timestamp = match.group(1)
                sender = match.group(2)
                content = lines[i + 1].strip()
                
                role = 'customer' if '客服' not in sender and '顾问' not in sender else 'agent'
                
                current_conv.messages.append(Message(
                    role=role,
                    content=content,
                    timestamp=timestamp
                ))
                i += 2
            else:
                i += 1
        
        if current_conv.messages:
            conversations.append(current_conv)
        
        return conversations
