# 設計文件

> 目標：以 **Flask + SQLite + Tailwind（CDN）** 建立「資安情訊平臺」。功能涵蓋：模組化 RSS 爬蟲 + Jina AI 讀取器清洗 + Google GenAI 摘要/翻譯/關鍵字 + 正則擷取（CVE/Email）+ Sploitus POC 查詢 + 後台審核制使用者系統 + Markdown 協作 + Discord 通知 + 簡易統計分析。全域設定集中於 `config.py` 並以 `.env` 管理祕鑰。

**更新紀錄**：
- 2025年：更新版權年份為2025年，並優化網頁UI/UX設計，強化響應式設計(RWD)，提供更好的手機用戶體驗。移除過多的emoji使用，採用更簡潔的設計風格。

---

## 一、專案資料夾結構（簡潔、邏輯分層）

```
MIS/
├─ app.py                    # Flask 入口（WSGI 亦可由此導入）
├─ config.py                 # 統一設定（讀取 .env；系統預設值；RSS 預設清單）
├─ .env.example              # 範例環境變數（勿含祕鑰）
├─ requirements.txt          # 套件清單（含 google-genai、feedparser、beautifulsoup4 等）
├─ prompts/                  # LLM 提示詞
│  ├─ summarization.md       # 摘要 + 利用方式
│  ├─ keywords.md            # 關鍵字抽取
│  ├─ translation.md         # 中英互譯
│  └─ classification.md      # 類別/標籤（可選）
├─ crawlers/                 # 爬蟲模組（以 rss.py 為唯一統一入口）
│  ├─ rss.py                 # 主腳本：讀 config/DB 的 RSS，節流調度、清洗、入庫
│  ├─ cleaners.py            # HTML → 純文字清洗、標籤移除、正規化
│  ├─ extractors.py          # 正則擷取（CVE、Email）
│  ├─ jina_reader.py         # Jina AI 讀取器請求（r.jina.ai/*）+ 節流（RPM）
│  ├─ genai_client.py        # Google GenAI（google-genai）統一介面
│  ├─ sploitus.py            # 手動 POC 查詢（輸入 CVE → 回傳 POC 連結）
│  └─ pipeline.py            # 針對單篇/單源的處理流程封裝（重用於 API 觸發）
├─ app/                      # Flask 應用程式
│  ├─ __init__.py
│  ├─ blueprints/
│  │  ├─ public/             # 公開頁面（新聞列表、詳情、搜尋）
│  │  ├─ auth/               # 註冊/登入/登出（審核制）
│  │  ├─ admin/              # 後台（RSS 管理、用戶 CRUD、檢視統計、手動觸發爬蟲/POC）
│  │  └─ api/                # 前後端用 JSON API（新聞、文章、通知觸發、POC 查詢）
│  ├─ services/
│  │  ├─ ai_service.py       # 摘要/翻譯/關鍵字/安全利用提示（整合 prompts/*）
│  │  ├─ notify/
│  │  │  └─ discord.py       # Discord 通知模組（頻道/使用者）
│  │  ├─ rss_service.py      # 從 DB/Config 讀 RSS + 交給 crawlers.rss
│  │  ├─ poc_service.py      # 封裝 POC 查詢（呼叫 crawlers.sploitus）
│  │  └─ stats_service.py    # 統計資料讀取/彙整
│  ├─ models/                # SQLite 資料表定義/DAO（可用 SQLAlchemy 或 sqlite3）
│  │  ├─ db.py
│  │  └─ schema.py
│  ├─ utils/
│  │  ├─ rate_limit.py       # 節流與簡易佇列（Jina/GenAI/通知）
│  │  ├─ security.py         # 雜湊、CSRF、防注入、檔案驗證
│  │  ├─ markdown.py         # Markdown 渲染/消毒（DOMPurify/marked 配置）
│  │  └─ validators.py       # 表單/輸入驗證
│  ├─ templates/             # Jinja2 模板（Tailwind CDN）
│  │  ├─ layouts/
│  │  ├─ public/
│  │  ├─ admin/
│  │  └─ auth/
│  └─ static/
│     ├─ css/                # 可放自訂 CSS（補強 Tailwind）
│     ├─ js/                 # 輕量 JS（無框架），可用 marked.js、DOMPurify、Chart.js（CDN）
│     └─ uploads/
│        └─ images/          # Markdown 圖片上傳（哈希檔名、大小限制）
├─ migrations/               # （選）資料表演進版本化記錄
├─ tests/                    # 單元/整合測試
│  ├─ __init__.py
│  ├─ test_crawler.py        # 爬蟲模組測試
│  └─ test_modules.py        # 其他模組測試
└─ docs/                     # （選）流程圖/ERD/維運筆記
```

---

## 二、環境與設定（`.env` 與 `config.py`）

### `.env`（範例欄位）

* `FLASK_ENV`：`development` / `production`
* `SECRET_KEY`：Flask session 祕鑰
* `SQLITE_PATH`：資料庫檔案路徑（如 `./data/app.db`）
* `DISCORD_BOT_TOKEN`、`DISCORD_CHANNEL_ID`（可多頻道）
* `GOOGLE_GENAI_API_KEY`：Google GenAI 祕鑰（\*\*使用最新 \*\*\`\`）
* `GEMINI_MODEL`：如 `gemini-2.0-flash`（可由 UI 切換）
* `JINA_MAX_RPM`：預設 `10`（Jina 讀取器每分鐘請求上限，硬上限 20）
* `GENAI_MAX_RPM`：GenAI 請求節流
* `ALLOWED_IMAGE_TYPES`：`image/png,image/jpeg,image/webp`
* `MAX_IMAGE_SIZE_MB`：如 `1.5`
* `TIMEZONE`：`Asia/Taipei`

### `config.py`

* 從 `.env` 讀取，並提供預設值與型別驗證。
* **RSS 預設清單**（`rss_targets`：`[{name, link, source}]`）。
* UI 可新增/停用 RSS；落地至 DB（`rss_sources`），`config.py` 只保留「系統預設」。
* 全域常數：

  * `DATE_TZ = UTC+8`；`DATE_FMT = 'YYYY-MM-DD'`（所有 `created_at` 皆以 UTC+8 存）
  * 內容最長長度、清洗策略、重試策略（最大次數、退避倍數）。
  * 審核制開關（是否需要管理員核可）。

---

## 三、資料庫設計（SQLite，一個 DB，多個表）

> 建議使用 SQLAlchemy（對新手友善、易維護），也可純 `sqlite3`。

### 1) 使用者與權限

* `users`

  * `id` INTEGER PK AUTOINCREMENT
  * `username` TEXT UNIQUE
  * `email` TEXT UNIQUE
  * `password_hash` TEXT
  * `role` TEXT（`admin`/`user`/`other`）
  * `is_active` INTEGER（0/1；**註冊後需管理員核可**）
  * `discord_user_id` TEXT NULLABLE
  * `created_at` DATE（UTC+8，`YYYY-MM-DD`）
  * `updated_at` DATE

* `sessions`（選）：如需長會話/設備紀錄

  * `id` INTEGER PK
  * `user_id` INTEGER FK → `users.id`
  * `ip` TEXT、`ua` TEXT、`created_at` DATE、`revoked` INTEGER

### 2) RSS 與新聞

* `rss_sources`

  * `id` INTEGER PK
  * `name` TEXT（顯示名；如 *The Hacker News*）
  * `link` TEXT UNIQUE（RSS URL）
  * `source` TEXT（來源識別；與新聞表 `source` 欄位對應）
  * `enabled` INTEGER（0/1）
  * `last_run_at` DATE NULLABLE

* `news`

  * `id` INTEGER PK AUTOINCREMENT
  * `link` TEXT UNIQUE（**去重依據**）
  * `title` TEXT NULLABLE
  * `source` TEXT（如 `iThome` / `The Hacker News` / `MITRE ATT&CK`）
  * `created_at` DATE（UTC+8，`YYYY-MM-DD`）
  * `content` TEXT（**純文字**，已移除 HTML）
  * `ai_content` TEXT NULLABLE（GenAI 產生「翻譯/摘要/利用方式」）
  * `keyword` TEXT NULLABLE（GenAI 產生關鍵字；以分隔字串或 JSON 儲存）
  * `email` TEXT NULLABLE（正則擷取；多值可以逗號/JSON）
  * `cve_id` TEXT NULLABLE（正則擷取；多值可以逗號/JSON）
  * `poc_link` TEXT NULLABLE（如 Sploitus 有找到）
  * 索引：`(source, created_at)`、`title`（FTS 可選）

* `cve_pocs`（正規化 POC；供多筆連結）

  * `id` INTEGER PK
  * `cve_id` TEXT
  * `poc_link` TEXT
  * `source` TEXT（如 `sploitus`）
  * `found_at` DATE
  * UNIQUE(`cve_id`,`poc_link`)

* `job_runs`（爬蟲與手動任務執行紀錄）

  * `id` INTEGER PK
  * `job_type` TEXT（`rss_all`/`rss_one`/`poc_check`/...）
  * `target` TEXT NULLABLE（如 RSS 名稱或 CVE）
  * `started_at` DATE、`ended_at` DATE
  * `inserted_count` INTEGER、`skipped_count` INTEGER、`error_count` INTEGER
  * `status` TEXT（`success`/`partial`/`failed`）

### 3) Markdown 協作與媒體

* `posts`

  * `id` INTEGER PK
  * `title` TEXT
  * `body_markdown` TEXT
  * `author_id` INTEGER FK → `users.id`
  * `is_published` INTEGER（0/1）
  * `created_at` DATE、`updated_at` DATE
  * （選）`tags` TEXT

* `images`

  * `id` INTEGER PK
  * `post_id` INTEGER FK → `posts.id`
  * `file_path` TEXT、`mime_type` TEXT
  * `file_size` INTEGER（位元組；需限制）
  * `width` INTEGER、`height` INTEGER
  * `created_at` DATE

### 4) 通知與審計

* `notifications`

  * `id` INTEGER PK
  * `type` TEXT（`discord`）
  * `payload` TEXT（JSON 字串；標題、連結、關鍵字、CVE 等）
  * `target_role` TEXT（`all`/`user`/`admin`/`custom`）
  * `news_id` INTEGER NULLABLE FK → `news.id`
  * `post_id` INTEGER NULLABLE FK → `posts.id`
  * `status` TEXT（`queued`/`sent`/`failed`）
  * `created_at` DATE、`sent_at` DATE

* `api_usage_logs`（LLM/外部 API 使用記錄）

  * `id` INTEGER PK
  * `provider` TEXT（`google-genai`/`jina`）
  * `model` TEXT、`latency_ms` INTEGER、`ok` INTEGER（0/1）
  * `cost` REAL NULLABLE、`requested_at` DATE

---

## 四、爬蟲與處理流程（`crawlers/rss.py` 為唯一統一入口）

### 來源與調度

1. 讀取 `rss_sources.enabled=1`；若 UI 指定單一 RSS 或臨時輸入 `rss_link/rss_name`，則僅處理該來源。
2. 使用 `feedparser` 取得項目（`title/link/published`）。
3. 以 \`\` 做去重（先 `SELECT link`）。

### Jina AI 讀取器（r.jina.ai）

* 對於新連結，改以 `https://r.jina.ai/<原始URL>` 取得 LLM-friendly 內容。
* 節流：**硬上限 20 RPM；**\`\`\*\* 預設 10\*\*（可由 UI 調整）。
* 失敗回退：可重試 N 次；仍失敗則記錄 `job_runs.error_count`。

### 內容清理 → 純文字

* `cleaners.py`：移除 HTML 標籤、壓縮空白、標點正規化、刪除殘留 script/style。
* 輸出 **純文字** 至 `news.content`（**不可存 HTML**）。

### AI 處理（`google-genai`）

* 客戶端統一由 `crawlers/genai_client.py` 封裝（\*\*非 \*\*\`\`）。
* 任務：

  * `摘要`（保留關鍵事實，50–150 字）
  * `翻譯`（中→英或英→中，依來源語言）
  * `如何利用`（高階說明：攻擊者可能如何濫用；防護重點）
  * `關鍵字`（3–10 個）
* **提示詞** 皆外置於 `prompts/`，以利調整。
* 回傳格式建議 **JSON**（供自動入庫）：

```json
{
  "summary": "...",
  "translation": "...",
  "how_to_exploit": "...",
  "keywords": ["...", "..."]
}
```

→ 以字串化 JSON 存入 `news.ai_content`（或拆欄位，視簡化需求）。

### 正則擷取（`extractors.py`）

* **CVE**：`CVE-\d{4}-\d{4,7}`（全形/半形/大小寫正規化）
* **Email**：`[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}`
* 擷取結果去重、排序；以逗號或 JSON 陣列存入 `news.cve_id` / `news.email`。

### Sploitus POC（`crawlers/sploitus.py`）

* **手動執行**（UI 觸發）：輸入 `CVE-YYYY-NNNN` → 查詢 `https://sploitus.com/?query=<CVE>#exploits`。
* 若有 POC：回傳第一層連結（或多筆），存 `news.poc_link` 或 `cve_pocs`。
* 供管理員/一般使用者在新聞詳情與列表列上之 **「查 POC」按鈕** 觸發；成功後更新 DB 並可選擇通知。
* **節流與佇列**：UI 端同一 `news_id` 同時只允許一個進行中請求；伺服器端以 `utils/rate_limit.py` 控制對 Sploitus 的請求頻率。

### 任務觸發方式

* **UI 按鈕**：

  * 「跑全部 RSS」、「跑指定 RSS」、「對此文章重跑 AI」、「查詢此 CVE 的 POC」。
* **定時**：可由系統排程（cron）呼叫 **HTTP 端點** 觸發 `rss.py` 流程（避免 CLI）。

---

## 五、Web 端（無框架；Tailwind CDN）

### 主要頁面

* **首頁 / 新聞列表**：來源/日期/關鍵字/CVE 篩選、搜尋；列表顯示 `title/source/date/tags`；點入詳情。
* **新聞詳情**：

  * 原文連結、純文字內容、AI 摘要/翻譯/如何利用、關聯 CVE/Email。
  * **按鈕**：「查 POC（Sploitus）」、「通知使用者」、「重跑 AI」。
* **Markdown 協作**：

  * 列表/詳情/編輯器（CDN：`marked.js` + `DOMPurify` 預覽）。
  * 圖片上傳（僅 `png/jpg/webp`，大小上限由 `config` 控制，顯示壓縮/限制說明）。
* **統計分析**：

  * 圖表（CDN：`Chart.js`）：

    * 每日新聞量（折線）
    * 來源占比（圓餅）
    * Top N CVE（橫條）
    * 有/無 POC 的占比
* **身分與後台**：

  * 註冊（建立帳號 → 狀態 `is_active=0`）
  * 登入/登出
  * **管理後台**：

    * 使用者 CRUD（核可/停用/角色）
    * RSS 管理（新增/停用/測試抓取）
    * 任務面板（按鈕觸發爬蟲/POC；查看 `job_runs`）
    * 通知面板（選擇對象/內容 → 送出 Discord）

### 「查 POC」按鈕（前端規格）

* **顯示條件**：當 `news.cve_id` **非空** 時在「新聞列表每列」與「新聞詳情頁」顯示「查 POC」按鈕；否則不顯示。
* **多 CVE 處理**：

  * 若該新聞含多個 CVE，點擊按鈕先彈出 Modal 列出 CVE 清單（可多選），並提供「全選」選項。
* **狀態與回饋**：

  * 送出後按鈕進入 `loading` 狀態並禁用；顯示「查詢中…」。
  * 成功：以 Toast/Modal 呈現「找到的 POC 連結清單」，並在該新聞卡片/詳情中即時更新 **POC 標記與連結區塊**。
  * 未找到：顯示「未找到 POC」訊息並提供「稍後重試」。
  * 失敗/節流：顯示可讀錯誤（429/逾時），提示稍後再試。
* **權限**：`admin` 與 `user` 皆可觸發；未登入者按鈕呈現 **灰階禁用** 並提示登入。
* **列表頁微設計**：如已有 POC，於卡片右上角顯示 `POC` 標籤；若多筆，顯示計數徽章。
* **可用性**：按鈕上方顯示 CVE 總數；行動裝置寬度時收斂為圖示按鈕（Tooltip：查 POC）。

### 權限矩陣

* `admin`：使用者核可與角色管理、RSS 管理、觸發所有任務、手動通知、刪修任何內容。
* `user`：瀏覽、搜尋、撰寫/發佈 Markdown、對有 CVE 的新聞執行「查 POC」、可提出「請通知」。
* `other`：僅瀏覽公開內容（依需求）。

### UI/UX 重點

* Tailwind CDN：基礎排版 + 元件以 `components/` 模板切片（Navbar、Card、Modal）。
* 表單回饋：即時驗證（長度、格式），錯誤訊息簡潔。
* 模組化 Partial：列表 Row、標籤 Pills、來源徽章、日期徽章（UTC+8）。

---

## 六、API 設計（供前端/排程/整合使用）

> 僅列要點；回應皆為 JSON。需 CSRF/Session 或最低限度 Token 驗證。

**API/前端可用性**：所有列表預設分頁與排序參數（`page,size,sort`），統一錯誤格式（`{code,message,details}`）；新增 `/healthz` 與 `/metrics`；為 cron 觸發提供受限 token；「查 POC」按鈕加去抖（避免連點）與 idempotency token；當已有進行中的同新聞查詢時，UI 顯示佇列/鎖定狀態並可查看最近一次結果。

* Auth：`POST /api/auth/login`、`POST /api/auth/logout`、`POST /api/auth/register`（`is_active=0`）
* Users（admin）：`GET/POST/PATCH/DELETE /api/admin/users`
* RSS（admin）：`GET/POST/PATCH /api/admin/rss`
* 爬蟲觸發（admin/user）

  * `POST /api/jobs/rss`（all 或 指定 `rss_id/link/name`）
  * `POST /api/jobs/ai-rerun`（指定 `news_id`）
  * `POST /api/jobs/poc`（**查 POC**）

    * **請求體**：`{ "news_id": 123, "cve_ids": ["CVE-2024-12345", "CVE-2024-99999"] }`（`cve_ids` 可省略代表使用該新聞全部 CVE）
    * **回應**：`{ "job_run_id": 42, "found": [{"cve_id":"...","links":["...","..."]}], "not_found":["CVE-...."], "updated_news": true }`
* 新聞：`GET /api/news`（支援 `q/source/date/cve/has_poc`）/ `GET /api/news/{id}`
* Markdown：`GET/POST/PATCH/DELETE /api/posts`、`GET /api/posts/{id}`
* 通知：`POST /api/notify`（admin 可自由撰寫或引用 `news_id/post_id`）
* 統計：`GET /api/stats/overview`（量、占比、Top N）

---

## 七、通知模組（Discord）

* 設計思路：

  * 入列 `notifications(status=queued)` → 背景工作或立即送出。
  * 節流：每分鐘上限（避免刷頻）。
  * 格式：標題、來源、日期、連結、摘要、關鍵字、CVE、POC 連結（若有）。
  * 目標：`target_role`（`all`/`admin`/`user`/`custom`）。
* 觸發點：

  * RSS 新增新聞（可選自動通知）
  * 管理員在後台對新聞/文章點擊「通知」
  * 使用者提交「請通知」後由管理員審核

---

## 八、內容安全與合規

* **輸入驗證**：長度、格式（Email/CVE）；白名單 MIME；檔案大小上限。
* **Markdown 安全**：渲染前以 `DOMPurify` 淨化；拒絕 `<script>`、事件屬性。
* **XSS/CSRF**：Jinja2 `|e` 轉義；CSRF Token；嚴格 SameSite Cookie。
* **SSTI**：避免將使用者輸入直灌模板；所有變數白名單傳入。
* **檔名/路徑**：隨機哈希命名；固定 `static/uploads/images/`；拒絕相對路徑穿越。
* **金鑰管理**：僅 `.env`；repo 放 `.env.example`；日誌過濾敏感資訊。
* **速率限制**：

  * Jina：**預設 10 RPM，硬上限 20**。
  * GenAI：依 `GENAI_MAX_RPM`。
  * 通知：每頻道每分鐘 N 則。

---

## 九、統計分析（`stats_service.py`）

* KPI：

  * 每日新聞量（以 `created_at` 聚合）
  * 來源占比（`source`）
  * 前 N 名 CVE（解析 `news.cve_id`）
  * 有 POC/無 POC 的比例（`poc_link`/`cve_pocs`）
  * 平均處理延遲（RSS → 入庫時間差）
* 查詢策略：

  * 儘量使用索引欄位聚合；`cve_id/keyword` 若為 JSON 字串可先行快取展平至臨時表（選）。

---

## 十、開發流程（建議里程碑）

1. **基礎框架**：`app.py`、`config.py`、SQLite 初始化、模板框架（Tailwind CDN）。
2. **使用者系統**：註冊/登入/審核/角色；後台骨架。
3. **資料模型**：`rss_sources`、`news`、`job_runs`、`posts`、`images`、`notifications`。
4. **RSS 爬蟲（ALL→入庫）**：去重、Jina 清洗、AI 摘要/翻譯/關鍵字、正則擷取。
5. **前端顯示**：新聞列表/詳情、搜尋/篩選。
6. **Markdown 協作**：編輯器 + 上傳限制 + 頁面呈現。
7. **POC 查詢（手動）**：詳情頁按鈕 → Sploitus → DB 更新。
8. **Discord 通知**：手動/自動；節流；格式化。
9. **統計分析**：Chart.js 圖表；`stats_service` 彙整。
10. **強化**：AI 失敗回退、重試、錯誤監控、API 使用紀錄、匯出備份。

---

## 十一、補充與實作細節

* **時區/日期**：一律以 **UTC+8** 存 `DATE`（`YYYY-MM-DD`）。顯示端按需求人性化。
* **多語內容**：

  * 來源英文 → 產生中文摘要與關鍵字；必要時保留英文摘要。
  * `ai_content` 以 JSON 字串存，可含 `summary_zh`, `summary_en` 等欄。
* **搜尋體驗**：

  * 關鍵字/CVE 快速篩選；日期區間；來源清單。
  * （選）SQLite FTS5 為 `news.title/content` 建全文索引。
* **相依套件**（建議）：

  * `google-genai`（\*\*取代舊 \*\*\`\`）
  * `feedparser`、`beautifulsoup4`、`requests`
  * `python-dotenv`、`sqlalchemy`（或原生 `sqlite3`）
  * 前端 CDN：Tailwind、marked.js、DOMPurify、Chart.js
* **備份/搬遷**：

  * DB 檔案與 `static/uploads/` 一併備份即可。
* **錯誤處理**：

  * 外部服務逾時/429 → 退避重試；達上限記 `job_runs` 並在後台可見。
* **可維護性**：

  * 所有外部請求均透過 `utils/rate_limit.py`；方便統一調整。
  * prompts 版本化，關鍵字/摘要準確度可隨時微調。

---

## 十二、互動流程（關鍵用例）

1. **使用者註冊** → `is_active=0` → 管理員審核通過 → 可登入。
2. **管理員「跑全部 RSS」** → `rss.py` 逐源抓取 → 新增 `news` → （可選）自動推 Discord。
3. **使用者瀏覽新聞詳情或列表列** → 看到 CVE → **點「查 POC」** →（若多 CVE）在 Modal 勾選 → 送出 API。
4. **POC 查詢成功** → 新增 `cve_pocs` 或更新 `news.poc_link` → 前端即時刷新徽章與連結 → （可選）通知使用者。
5. **撰寫 Markdown** → 上傳圖片（大小/MIME 驗證）→ 發佈 → 全站可見。
6. **統計頁** → 按來源/日期/CVE 檢視趨勢與占比。

## 十三、最小可行版本（MVP）邊界

* 必做：RSS → Jina → 清洗 → GenAI（摘要/翻譯/關鍵字/利用）→ 正則擷取 → 入庫 → 列表/詳情顯示。
* 手動：POC 查詢按鈕；Discord 手動通知。
* 後台：使用者審核 + RSS 管理 + 任務面板。
* 圖表：每日量 + 來源占比。

> 後續迭代再加入自動通知、FTS5 搜尋、更多圖表、貼文標籤、RSS 匯入匯出等。