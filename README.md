# AI 備課助手（繁體中文・台灣適配版）

原本是烏干達取向的英文開源專案，已改成台灣補習班用法。

功能：
- 成績分析：上傳 CSV／Excel（含班務系統匯出的），看熱力圖、排名、出缺勤，AI 給建議
- AI 出題：輸入範圍出選擇題，可混搭難易度，下載 DOCX 考卷＋參考答案
- 教案／講義：台灣 108 課綱格式，國小 1–6 年級、國中 7–9 年級，產 DOCX 教案和 PPT 大綱
- 課文摘要：貼講義或上傳 PDF／DOCX，AI 整理重點，可下載
- 教師心情樹洞：聊備課壓力，對話可下載

## 啟動

1. 進入這個資料夾，安裝依賴：`pip install -r requirements.txt`
2. 設定金鑰（三選一）：
   - 直接在左側欄輸入 OpenAI API 金鑰（最簡單，不存檔），或
   - 複製 `.env.example` 為 `.env` 填入金鑰，或
   - 設定環境變數 `OPENAI_API_KEY`
3. 啟動：`streamlit run app.py`

沒設金鑰也能開程式、看介面、上傳檔案；按到 AI 功能時會中文提醒補金鑰。

## 部署到 Streamlit 官方雲（24 小時線上）

1. 推上 GitHub（本資料夾就是獨立 repo）
2. 到 share.streamlit.io 用 GitHub 登入，按 New app，選這個 repo、分支 main、主檔 app.py
3. 在 App settings → Secrets 貼上：
   OPENAI_API_KEY="sk-xxxx"
   要換模型再加一行 OPENAI_MODEL="gpt-5-mini"
4. 按 Deploy，等幾分鐘就有公開網址，Chrome 存書籤即可
