# 資安情訊平臺

這是一個基於 Flask + SQLite + Tailwind CSS 的資安新聞情報平臺，具備以下功能：

## 核心功能

- 🔍 **RSS 爬蟲**：自動從多個資安新聞源抓取最新資訊
- 🤖 **AI 分析**：使用 Google GenAI 提供摘要、翻譯、關鍵字和利用方式分析
- 🛡️ **CVE 擷取**：自動識別和擷取 CVE 編號
- 🔎 **POC 查詢**：手動查詢 Sploitus 上的 POC 資源
- 👥 **使用者管理**：審核制註冊系統
- 📰 **新聞瀏覽**：支援搜尋、篩選的新聞列表
- 🔔 **Discord 通知**：可推送新聞到 Discord 頻道
- 📊 **統計分析**：基本的數據統計和圖表

## 快速開始

### 1. 環境設置

```bash
# 克隆專案
git clone https://github.com/yutimmy/mis-security-platform.git

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 2. 環境變數設置

複製 `.env.example` 為 `.env` 並填入相關 API 金鑰：

```bash
cp .env.example .env
# 編輯 .env 檔案，填入以下金鑰：
# - GOOGLE_GENAI_API_KEY：Google GenAI API 金鑰
# - DISCORD_BOT_TOKEN：Discord 機器人 Token
# - DISCORD_CHANNEL_ID：Discord 頻道 ID
```

### 3. 初始化資料庫

```bash
python init_db.py
```

這會建立：
- SQLite 資料庫（`./data/app.db`）
- 預設管理員帳號：`admin` / `admin123`
- 預設的 RSS 來源（The Hacker News、Krebs on Security、Bleeping Computer）

### 4. 啟動應用程式

```bash
python app.py
```

應用程式將在 http://127.0.0.1:5000 啟動

## 使用說明

### 登入系統

1. 訪問 http://127.0.0.1:5000/auth/login
2. 使用管理員帳號登入：`admin` / `admin123`
3. 或註冊新帳號（需要管理員審核）

### 管理後台

管理員登入後可以訪問：
- 使用者管理：審核新註冊的使用者
- RSS 來源管理：新增/停用 RSS 來源
- 任務管理：查看爬蟲執行記錄

### RSS 爬蟲

可以透過以下方式觸發：

1. **管理後台**：登入後台點擊「執行 RSS 爬蟲」
2. **API 呼叫**：
   ```bash
   curl -X POST http://127.0.0.1:5000/api/jobs/rss
   ```
3. **測試腳本**：
   ```bash
   python test_crawler.py
   ```

### POC 查詢

對於包含 CVE 的新聞：
1. 在新聞列表或詳情頁點擊「查 POC」按鈕
2. 如有多個 CVE，會彈出選擇對話框
3. 系統會查詢 Sploitus 並更新結果

## API 文檔

### 健康檢查
```
GET /api/healthz
```

### 新聞列表
```
GET /api/news?page=1&size=20&source=thehackernews&q=keyword&cve=CVE-2024-12345
```

### 新聞詳情
```
GET /api/news/{id}
```

### 觸發 RSS 爬蟲
```
POST /api/jobs/rss
```

### 觸發 POC 查詢
```
POST /api/jobs/poc
Content-Type: application/json

{
  "news_id": 123,
  "cve_ids": ["CVE-2024-12345"]
}
```

## 檔案結構

```
├── app.py                    # Flask 入口
├── config.py                 # 設定檔
├── init_db.py               # 資料庫初始化
├── test_crawler.py          # 爬蟲測試腳本
├── requirements.txt         # Python 依賴
├── .env.example            # 環境變數範例
├── app/                    # Flask 應用程式
│   ├── __init__.py
│   ├── blueprints/         # 路由藍圖
│   ├── models/             # 資料模型
│   └── templates/          # Jinja2 模板
├── crawlers/               # 爬蟲模組
│   ├── rss.py             # RSS 處理
│   ├── cleaners.py        # 內容清理
│   ├── extractors.py      # 資訊擷取
│   ├── jina_reader.py     # Jina AI 讀取器
│   ├── genai_client.py    # Google GenAI 客戶端
│   └── sploitus.py        # POC 查詢
└── data/                  # 資料庫檔案
```

## 開發說明

### 新增 RSS 來源

1. 透過管理後台新增
2. 或修改 `config.py` 中的 `DEFAULT_RSS_SOURCES`

### 自訂 AI 提示詞

可以修改 `crawlers/genai_client.py` 中的提示詞模板來調整 AI 分析的輸出格式。

### 擴展功能

- 新增爬蟲模組：在 `crawlers/` 目錄新增
- 新增頁面：在 `app/blueprints/` 和 `app/templates/` 新增
- 新增 API：在 `app/blueprints/api/` 新增端點

## 注意事項

- 🔑 **API 金鑰**：Google GenAI 和 Discord 功能需要相應的 API 金鑰
- 🚫 **速率限制**：Jina Reader 預設每分鐘 10 次請求
- 🔒 **安全性**：生產環境請更改預設密碼和密鑰
- 📱 **響應式設計**：使用 Tailwind CSS，支援行動裝置

## 故障排除

### 常見問題

1. **資料庫連線失敗**：檢查 `data/` 目錄是否存在
2. **爬蟲無法取得內容**：檢查網路連線和 RSS 來源狀態
3. **AI 分析失敗**：檢查 Google GenAI API 金鑰設定
4. **POC 查詢失敗**：可能是 Sploitus 網站結構變更

### 日誌檢查

應用程式會在終端輸出詳細的執行日誌，包括：
- RSS 爬蟲處理進度
- AI 分析結果
- POC 查詢狀態
- 資料庫操作結果

## 授權

此專案僅供學習和研究使用。使用時請遵守相關網站的使用條款和 API 限制。

## 支援

如有問題或建議，請檢查：
1. 日誌輸出
2. 環境變數設定
3. API 金鑰有效性
4. 網路連線狀態
