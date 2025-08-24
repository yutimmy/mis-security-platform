# HTML → 純文字清洗、標籤移除、正規化
import re

from bs4 import BeautifulSoup


def clean_html_content(html_content):
    """清理 HTML 內容，轉為純文字"""
    if not html_content:
        return ""
    
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除 script 和 style 標籤
    for script in soup(["script", "style"]):
        script.decompose()
    
    # 取得純文字
    text = soup.get_text()
    
    # 正規化空白字元
    text = re.sub(r'\s+', ' ', text)
    
    # 移除開頭結尾的空白
    text = text.strip()
    
    return text


def normalize_text(text):
    """正規化文字內容"""
    if not text:
        return ""
    
    # 統一換行符號
    text = re.sub(r'\r\n|\r', '\n', text)
    
    # 壓縮多個空白行
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # 移除行首行尾空白
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text.strip()
