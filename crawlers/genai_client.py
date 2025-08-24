# Google GenAI（google-genai）統一介面
import json
import os

import google.generativeai as genai


class GenAIClient:
    """Google GenAI 客戶端"""
    
    def __init__(self, api_key=None, model="gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_GENAI_API_KEY")
        self.model_name = model
        
        if not self.api_key:
            raise ValueError("Google GenAI API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_analysis(self, text, news_title="", source=""):
        """
        生成新聞分析：摘要、翻譯、利用方式、關鍵字
        """
        prompt = f"""
請分析以下資安新聞，並以 JSON 格式回應：

新聞標題：{news_title}
新聞來源：{source}
新聞內容：
{text}

請提供：
1. summary: 中文摘要 (50-150字)
2. translation: 如果是英文新聞請翻譯為中文，如果是中文新聞請翻譯為英文
3. how_to_exploit: 攻擊者可能的利用方式與防護建議 (100-200字)
4. keywords: 3-10個關鍵字 (陣列格式)

回應格式：
{{
  "summary": "...",
  "translation": "...", 
  "how_to_exploit": "...",
  "keywords": ["關鍵字1", "關鍵字2", "..."]
}}

請確保回應是有效的 JSON 格式。
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # 嘗試解析 JSON
            # 有時 AI 會在 JSON 前後加上其他文字，需要提取
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                # 如果找不到 JSON，返回原始文字
                return {
                    "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "translation": "",
                    "how_to_exploit": "",
                    "keywords": []
                }
                
        except Exception as e:
            print(f"GenAI analysis failed: {e}")
            return {
                "summary": "AI 分析失敗",
                "translation": "",
                "how_to_exploit": "",
                "keywords": []
            }
    
    def test_connection(self):
        """測試 API 連線"""
        try:
            response = self.model.generate_content("請回覆：API 連線正常")
            return True, response.text
        except Exception as e:
            return False, str(e)
