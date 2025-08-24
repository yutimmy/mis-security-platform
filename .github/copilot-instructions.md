## 0. 專案快速脈絡
* **目標**：建置「資安情訊平臺」：Flask + SQLite + Tailwind（CDN）。
* **核心功能**：模組化 RSS 爬蟲 → Jina AI 讀取器清洗 → Google GenAI 摘要/翻譯/關鍵字/利用方式 → 正則擷取（CVE/Email）→ Sploitus POC 查詢（手動）→ 審核制使用者系統 → Markdown 協作 → Discord 通知 → 簡易統計。
* **配置**：集中於 `config.py`，機敏金鑰由 `.env` 讀取（版本庫提供 `.env.example`）。
* **資料庫**：SQLite（建議 SQLAlchemy ORM）。
* **前端**：Jinja2 + Tailwind（CDN），少量原生 JS（可用 marked.js、DOMPurify、Chart.js via CDN）。

> 完整資料夾結構、資料表、API 與流程請參考 `/` 根目錄的設計文件（`document.md`）。

---

## 1. 基礎規範
**要求**：

1. 產生 **可執行、可測試** 的最小增量變更（MVP first），必要時以 TODO 註記後續強化點。
2. 嚴格遵循本檔的 **程式風格與專案約束**。
3. 任何返回 **JSON** 時，請輸出 **純 JSON**，不得夾帶註解或多餘文字。
4. 對外服務（Jina、Google GenAI、Sploitus、Discord）**一律走封裝客戶端/服務層**，不得在視圖（route）內直接呼叫。
5. 若功能涉及速率限制或重試，**先引用 `utils/rate_limit.py` 或於服務層實作退避**，切勿在控制器層硬寫 sleep。
6. 一律在已啟用 .venv 的情況下執行 python/pip/flask 指令。產生任何 Shell 指令時，請先給出啟用 .venv 的步驟，接著再執行目標指令。

---

## 2. 程式風格

**Python 一致風格**

* **函式參數**：**不要有型別註記**（`def fn(a, b):`），回傳型別亦不標註。
* **函式註解**：使用 **簡短、易懂** 的 docstring 或行內註解；重點描述「做什麼」與「關鍵參數」，避免長篇理論。
* **import 次序（PEP 8）**：

  1. 標準函式庫（stdlib）
  2. 第三方套件
  3. 本地套件（本專案模組）

  各群組之間空一行；避免萬用匯入 `*`；按字母序排列。

**命名與格式**

* 檔案、模組、函式使用 **snake\_case**；類別使用 **PascalCase**。
* 常數大寫（`MAX_IMAGE_SIZE_MB`）。
* 每個模組須自我含注：頂部以 1–3 行註解說明用途。

**Jinja / 前端**

* 遵循 Tailwind 原子化樣式；共用塊請抽成 `templates/layouts/` 或 partial。
* 客端 JS 僅做互動與輕量校驗；Markdown 預覽一律經 DOMPurify。

---

## 3. 重要工程約束

1. **資料安全**：

   * 任何新聞內容以 **純文字** 存入 `news.content`（嚴禁 HTML）。
   * 金鑰僅可讀取自 `.env`，禁止硬編碼。禁止將 `.env` 寫入版本控制。
2. **時間與時區**：所有 `DATE` 以 **UTC+8**（格式 `YYYY-MM-DD`）存入 DB。
3. **外部服務**：

   * **Jina Reader**：使用 `https://r.jina.ai/<URL>`，預設 10 RPM（硬上限 20）。
   * **Google GenAI**（`google-genai`）：統一由 `crawlers/genai_client.py` 或 `app/services/ai_service.py` 代理，支援摘要/翻譯/關鍵字/利用方式，回傳 JSON。
   * **Sploitus**：僅供 **手動** POC 查詢，封裝於 `crawlers/sploitus.py` 與 `app/services/poc_service.py`，搭配速率限制。
   * **Discord**：`app/services/notify/discord.py`，支援頻道/對象選擇與節流。
4. **權限與審核**：註冊預設 `is_active=0`；後台可核可與角色管理。
5. **API 規範**：回應 JSON 形如 `{code, message, details}`；列表支援 `page,size,sort`；提供 `/healthz`、`/metrics`。

---

## 4. 產碼優先順序

1. **骨架**：`app.py`、`config.py`、`app/__init__.py`、`models/db.py`、`models/schema.py`、`templates/layouts/base.html`。
2. **使用者系統**：`blueprints/auth`（註冊/登入/登出）、角色與審核欄位與流程。
3. **資料模型**：`rss_sources`、`news`、`job_runs`、`posts`、`images`、`notifications`（建議 SQLAlchemy）。
4. **爬蟲流程**：`crawlers/rss.py`（唯一入口）→ `cleaners.py` → `jina_reader.py` → `genai_client.py` → `extractors.py` → 入庫。
5. **前端頁面**：公開列表/詳情、搜尋/篩選；後台骨架與任務面板。
6. **POC 查詢**：API 與前端按鈕互動（含多 CVE Modal 與狀態回饋）。
7. **Discord 通知**：手動通知路徑與格式模板。
8. **統計**：`stats_service.py` 與 Chart.js 圖表。

---

## 5. 典型樣板（請在對應路徑產出）

> 下列範例僅示意關鍵約束與結構；**請維持：無型別註記、簡短註解、PEP8 import 次序**。

### 5.1 `app.py`

```python
# Flask 入口與藍圖註冊
import os

from flask import Flask

from app import create_app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```

### 5.2 `app/__init__.py`

```python
# 建立 Flask App、載入配置與藍圖
import os

from flask import Flask

from .models.db import init_db
from .blueprints.public.views import public_bp
from .blueprints.auth.views import auth_bp
from .blueprints.admin.views import admin_bp
from .blueprints.api.views import api_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    init_db(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
```

### 5.3 `config.py`

```python
# 讀取 .env、集中設定與預設值
import os

from dotenv import load_dotenv


class Config:
    load_dotenv()

    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    SQLITE_PATH = os.getenv("SQLITE_PATH", "./data/app.db")
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Taipei")

    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")

    GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    JINA_MAX_RPM = int(os.getenv("JINA_MAX_RPM", 10))
    GENAI_MAX_RPM = int(os.getenv("GENAI_MAX_RPM", 5))

    ALLOWED_IMAGE_TYPES = os.getenv("ALLOWED_IMAGE_TYPES", "image/png,image/jpeg,image/webp")
    MAX_IMAGE_SIZE_MB = float(os.getenv("MAX_IMAGE_SIZE_MB", 1.5))

    DATE_FMT = "%Y-%m-%d"
```

### 5.4 `app/models/db.py`

```python
# SQLAlchemy 初始化與 BaseModel
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{app.config['SQLITE_PATH']}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
```

### 5.5 `crawlers/jina_reader.py`

```python
# 透過 r.jina.ai 讀取並節流
import time

import requests


def fetch_readable(url, rpm):
    # 取得可讀內容；呼叫方負責錯誤處理
    time.sleep(60.0 / max(1, rpm))
    r = requests.get(f"https://r.jina.ai/{url}", timeout=20)
    if r.status_code != 200:
        return ""
    return r.text
```

### 5.6 `crawlers/extractors.py`

```python
# 正則擷取：CVE、Email
import re


def extract_cves(text):
    # 傳回去重排序後的 CVE 清單
    pattern = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
    found = set(m.upper() for m in pattern.findall(text))
    return sorted(found)


def extract_emails(text):
    # 傳回去重排序後的 Email 清單
    pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    return sorted(set(pattern.findall(text)))
```

---

## 6. Do / Don’t 清單

**Do**

* 以 **服務層** 封裝外部呼叫與重試/節流。
* 回傳 **可用的最小實作**，以 TODO 標明擴充點。
* 以 **JSON** 格式儲存 AI 結果至 `news.ai_content`（或由服務層協助拆欄位）。
* 每次新增外部依賴時，更新 `requirements.txt` 與 `.env.example`。

**Don’t**

* 不要在 route 內直接呼叫外部 API。
* 不要將 HTML 存入 DB 的 `news.content`。
* 不要硬編碼金鑰或在版本庫存放任何敏感資訊。
* 不要在函式或參數上加型別註記。

---

## 7. 測試與驗收

**基本測試**

* 單元測試：`extractors.py`（CVE/Email）、`cleaners.py`、`stats_service.py` 聚合查詢。
* 整合測試：`/api/jobs/rss` 模擬一個來源、斷言去重與入庫；`/api/jobs/poc` 返回格式與佇列行為。

**驗收條件**

* 新聞詳情頁展示：標題、來源、日期、純文字內容、AI 摘要/翻譯/利用方式、CVE/Email、POC 標記。
* 列表頁可依來源/日期/CVE 搜尋與篩選。
* 後台：看見 job 執行紀錄（成功/部分/失敗），可手動觸發 RSS/POC/AI 重跑。

---

## 8. 安全與合規（生成時務必檢查）

* **CSRF / XSS**：表單 CSRF Token、Jinja `|e`、DOMPurify 淨化 Markdown。
* **檔案上傳**：固定路徑 `static/uploads/images/`，哈希檔名、MIME 白名單、大小限制（讀自 `config`）。
* **注入防護**：ORM 為主；對任何原生 SQL 以參數化查詢；路徑/檔名嚴格驗證。
* **速率限制**：Jina 10 RPM（預設）、GenAI 依 `GENAI_MAX_RPM`、通知每頻道每分鐘 N 則。

---

## 9. 共同規範備忘

* Commit 訊息簡潔，以模組為單位（如 `crawlers: add jina reader with rpm limit`）。
* 新檔案加上文件頂部功用註解與 TODO 區塊。
* 變更需同步更新 README.md/document.md 之相關段落。