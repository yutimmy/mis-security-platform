# AI 服務：整合 prompts 和 GenAI 客戶端
import json
import logging
import os

from crawlers.genai_client import GenAIClient


logger = logging.getLogger(__name__)


class AIService:
    """AI 分析服務"""
    
    def __init__(self):
        self.genai_client = None
        self.prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts')
        
        # 初始化 GenAI 客戶端
        try:
            self.genai_client = GenAIClient()
        except Exception as e:
            logger.warning("GenAI client initialization failed: %s", e)
    
    def load_prompt(self, prompt_name):
        """載入提示詞模板"""
        prompt_file = os.path.join(self.prompts_dir, f"{prompt_name}.md")
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def generate_summary(self, content, title="", source=""):
        """生成摘要"""
        if not self.genai_client:
            return None
        
        # 載入摘要提示詞
        prompt_template = self.load_prompt('summarization')
        if prompt_template:
            prompt = prompt_template.format(
                title=title,
                source=source,
                content=content
            )
        else:
            # 使用預設提示詞
            prompt = f"""
請為以下資安新聞撰寫摘要（50-150字）：

標題：{title}
來源：{source}
內容：{content}

要求：
1. 保留關鍵事實和技術細節
2. 使用繁體中文
3. 簡潔明瞭
"""
        
        try:
            response = self.genai_client.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.exception("Summary generation failed")
            return None
    
    def generate_translation(self, content, title="", source_lang="auto"):
        """生成翻譯"""
        if not self.genai_client:
            return None
        
        prompt_template = self.load_prompt('translation')
        if prompt_template:
            prompt = prompt_template.format(
                title=title,
                content=content,
                source_lang=source_lang
            )
        else:
            # 使用預設提示詞
            prompt = f"""
請翻譯以下資安新聞：

標題：{title}
內容：{content}

要求：
1. 如果是英文內容，請翻譯為繁體中文
2. 如果是中文內容，請翻譯為英文
3. 保持技術術語的準確性
4. 保持原文的語調和風格
"""
        
        try:
            response = self.genai_client.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.exception("Translation generation failed")
            return None
    
    def extract_keywords(self, content, title="", max_keywords=10):
        """提取關鍵字"""
        if not self.genai_client:
            return []
        
        prompt_template = self.load_prompt('keywords')
        if prompt_template:
            prompt = prompt_template.format(
                title=title,
                content=content,
                max_keywords=max_keywords
            )
        else:
            # 使用預設提示詞
            prompt = f"""
請從以下資安新聞中提取關鍵字（3-{max_keywords}個）：

標題：{title}
內容：{content}

要求：
1. 提取最重要的技術關鍵字
2. 包含漏洞類型、產品名稱、攻擊手法等
3. 使用繁體中文
4. 以JSON陣列格式回應：["關鍵字1", "關鍵字2", ...]
"""
        
        try:
            response = self.genai_client.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # 嘗試解析JSON
            if response_text.startswith('[') and response_text.endswith(']'):
                return json.loads(response_text)
            else:
                # 如果不是JSON格式，嘗試從文字中提取
                lines = response_text.split('\n')
                keywords = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 移除序號和符號
                        keyword = line.replace('-', '').replace('*', '').replace('1.', '').replace('2.', '').strip()
                        if keyword:
                            keywords.append(keyword)
                return keywords[:max_keywords]
                
        except Exception as e:
            logger.exception("Keyword extraction failed")
            return []
    
    def generate_exploitation_analysis(self, content, title="", cve_list=None):
        """生成利用方式分析"""
        if not self.genai_client:
            return None
        
        cve_info = ""
        if cve_list:
            cve_info = f"\n相關CVE：{', '.join(cve_list)}"
        
        prompt = f"""
請分析以下資安新聞中提到的漏洞或威脅的利用方式：

標題：{title}
內容：{content}{cve_info}

請提供：
1. 攻擊者可能的利用方式（具體步驟）
2. 潛在影響和風險
3. 防護和緩解建議
4. 檢測方法

要求：
- 使用繁體中文
- 100-200字
- 技術性描述，但易於理解
"""
        
        try:
            response = self.genai_client.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.exception("Exploitation analysis failed")
            return None
    
    def generate_complete_analysis(self, content, title="", source="", cve_list=None):
        """生成完整分析（整合版本）"""
        if not self.genai_client:
            return {
                "summary": "AI服務未可用",
                "translation": "",
                "how_to_exploit": "",
                "keywords": []
            }
        
        return self.genai_client.generate_analysis(content, title, source)
