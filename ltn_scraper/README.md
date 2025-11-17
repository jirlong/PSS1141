LTN Search Scraper

A minimal, procedural Python scraper for Liberty Times Net (LTN) search results.

Usage

- Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Run the scraper (defaults to keyword 川普):

```bash
python scrape_ltn.py
# or with arguments, example:
# Scrape keyword "川普", from 2024-01-01 to 2025-10-12, 3 pages, write to results.jsonl
python scrape_ltn.py --keyword 川普 --start-date 2024-01-01 --end-date 2025-10-12 --pages 3 --output results.jsonl
```

Batch keywords from a file (one keyword per line):

```bash
# keywords.txt contains one keyword per line
python scrape_ltn.py --keywords-file keywords.txt --pages 3 --output combined.jsonl
```

Use multiple workers for faster fetching (be careful with rate limits):

```bash
python scrape_ltn.py -k 川普 -p 5 -w 4 --debug
```

## Developer Prompt Template

下面是一個完整且可直接複製使用的 Prompt（中文），可用來在未來讓 AI 或開發者清楚理解並重現本專案的要求與功能：

---

我有一個 Python 爬蟲專案 `ltn_scraper`，目前已有基本的 search.ltn.com.tw 搜尋結果抓取腳本 `scrape_ltn.py`。

請根據以下需求幫我開發或維護此專案：

- CLI 功能
	- 可從命令列指定單一關鍵字（`--keyword` / `-k`）、時間區間（`--start-date`, `--end-date`，支援 YYYYMMDD / YYYY-MM-DD / YYYY/MM/DD）、要抓取的頁數（`--pages` / `-p`）、輸出檔案（`--output` / `-o`）。
	- 支援批次關鍵字檔案（`--keywords-file` / `-K`），檔案每行一個關鍵字，允許 `#` 作為註解開頭的行。
	- 支援 debug 模式（`--debug`）以輸出更多日誌。
	- 支援並行工作者參數（`--workers` / `-w`）以多執行緒抓取每個 page（預設 1）。

- 日誌與錯誤處理
	- 使用 Python 的 `logging` 模組，依 `--debug` 切換 INFO/DEBUG。
	- HTTP 請求應有 retry + exponential backoff（預設 3 次重試，backoff factor 可調）並在最終失敗時記錄警告並忽略該頁。
	- 要有合理的 polite sleep（單執行緒模式下每頁 sleep，例如 0.8s），並在並行模式下可考慮更嚴格的速率限制或全域 rate limiter。

- 功能行為
	- 對每個搜尋結果頁面解析原有邏輯（使用 CSS selectors `ul.list.boxTitle` 與 `a.tit` 作為主要/備援解析方式）。
	- 批次模式下應合併所有關鍵字的結果並根據 `url` 去重，最後將合併結果寫入指定的 output JSONL 檔。
	- 預設輸出為 JSON Lines（每行一個 JSON 物件，包括至少 `title` 與 `url` 欄位）。

- 可選擴充（非必須但建議）
	- 使用更成熟的重試套件（如 `tenacity` 或 `requests` 的 urllib3 Retry）以提升韌性。
	- 增加 per-host rate limiting 或 token bucket 控制並行速率。
	- 改成非同步 aiohttp 版本以提高吞吐（需改寫請求與解析邏輯）。
	- 新增單元測試（使用 requests-mock / responses 模擬 HTML、測試解析器與去重邏輯）。

---

可直接把上面的 prompt 貼給 AI 或留給其他開發者作為需求規格。若要我把它轉成英文、或加入更詳細的參數說明範例（例如 backoff 參數、timeout 設定）我也可以幫你擴充。

Notes

- The script intentionally uses no functions or classes (procedural style).
- It's a simple scraper for personal use. Be respectful of the site's robots.txt and rate limits.
- If the page structure changes, update the CSS selectors in `scrape_ltn.py`.
