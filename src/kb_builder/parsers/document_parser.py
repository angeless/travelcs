"""
文档解析器 - 支持PDF, DOCX, TXT, HTML
"""
from pathlib import Path
from typing import Optional


class DocumentParser:
    """文档解析器"""
    
    def parse(self, file_path: Path) -> Optional[str]:
        """解析文档返回文本"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._parse_pdf(file_path)
        elif suffix in ['.docx', '.doc']:
            return self._parse_docx(file_path)
        elif suffix == '.txt':
            return self._parse_txt(file_path)
        elif suffix in ['.html', '.htm']:
            return self._parse_html(file_path)
        else:
            print(f"⚠️ 不支持的格式: {suffix}")
            return None
    
    def _parse_pdf(self, file_path: Path) -> str:
        """解析PDF"""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except ImportError:
            print("📦 安装PyPDF2: pip install PyPDF2")
            return self._fallback_read(file_path)
    
    def _parse_docx(self, file_path: Path) -> str:
        """解析Word"""
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            print("📦 安装python-docx: pip install python-docx")
            return self._fallback_read(file_path)
    
    def _parse_txt(self, file_path: Path) -> str:
        """解析文本"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _parse_html(self, file_path: Path) -> str:
        """解析HTML"""
        try:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                # 移除脚本和样式
                for script in soup(["script", "style"]):
                    script.decompose()
                return soup.get_text(separator='\n', strip=True)
        except ImportError:
            return self._fallback_read(file_path)
    
    def _fallback_read(self, file_path: Path) -> str:
        """兜底读取"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            return ""
