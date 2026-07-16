# 職務移交報告：Open WebUI × Apache Tika 4.0 上傳 JSONDecodeError

**日期**：2026-07-16
**負責範圍移交**：Open WebUI 端 `TikaLoader` 與 Tika 4.0 的端點契約修正
**狀態**：Tika 服務端已修正完成；**Open WebUI 端待修（本報告主體）**

---

## 一、一句話摘要

Open WebUI 上傳檔案時噴 `JSONDecodeError: Expecting value: line 12 column 1 (char 11)`。
根因是 **OWUI 的 `TikaLoader` 打 Tika 的 `/tika/text` 端點並對回應做 `r.json()`，但 Apache Tika 4.0 已把 `/tika/text` 的輸出從「JSON 物件」改為「純文字」**，導致 `r.json()` 解析失敗。與雲端/本地 Gemma、與 tika-config 都無關。

---

## 二、背景架構

文件上傳的抽取鏈：

```
Open WebUI ──PUT /tika/text──▶ Tika(4.0.0-SNAPSHOT-full) ──VLM──▶ Gemma(Google API)
   (Python)      坑 1 在這          (內容抽取引擎)              (圖片 OCR)
```

- OWUI 環境變數：`CONTENT_EXTRACTION_ENGINE=tika`、`TIKA_SERVER_URL=http://tika:9998`
- OWUI 映像：本地自建 `open-webui-processing`（來源 `docker/Dockerfile`）
- 抽取鏈其餘部分（OWUI→Tika 連通、Tika→Gemma、圖片走 VLM）**皆已驗證可用**（見附錄）。

---

## 三、根因（附證據）

Tika 4.0 主版本刻意變更了端點預設行為（官方 release note：`/tika`、`/rmeta` 預設改輸出 Markdown；端點契約調整）。實測同一份純文字檔 PUT 到 `/tika/text`：

| Tika 版本 | `/tika/text` 回應 content-type | OWUI `r.json()` |
|---|---|---|
| 穩定版 `apache/tika:latest`（2.x/3.x） | `application/json`（物件，含 `X-TIKA:content`） | ✅ 正常 |
| **`4.0.0-SNAPSHOT-full`（本專案使用）** | **`text/plain`** | ❌ **JSONDecodeError** |

補充實測：
- `/tika/text` + `Accept: application/json` → **HTTP 406**（無法用 header 逼回 JSON）。
- 4.0 中**回 JSON 且含 `X-TIKA:content` 的端點是 `/rmeta/text`**（回傳為**陣列** `[{...}]`）。

> 為何非用 4.0 不可：圖片 OCR 的 VLM parser（`tika-vlm`）只在 Tika 4.0 才有，穩定版沒有。因此**不能靠降版**解決，只能讓 OWUI 順應 4.0 的新契約。

---

## 四、待辦：要改的檔案與具體修法

### 目標檔案
```
backend/open_webui/retrieval/loaders/main.py
```
（容器內路徑：`/app/backend/open_webui/retrieval/loaders/main.py`）
類別 `TikaLoader.load()`，約在 148–180 行。

### 現況程式（問題點）
```python
endpoint = self.url
if not endpoint.endswith('/'):
    endpoint += '/'
endpoint += 'tika/text'                       # ← 4.0 這裡回 text/plain

r = requests.put(endpoint, data=data, headers=headers, verify=REQUESTS_VERIFY)

if r.ok:
    raw_metadata = r.json()                    # ← 對純文字做 json() → 爆炸
    text = raw_metadata.get('X-TIKA:content', '<No text content found>').strip()
    if 'Content-Type' in raw_metadata:
        headers['Content-Type'] = raw_metadata['Content-Type']
    return [Document(page_content=text, metadata=headers)]
else:
    raise Exception(f'Error calling Tika: {r.reason}')
```

### 建議修法（改打 `/rmeta/text`，並處理「回傳為陣列」）
```python
endpoint = self.url
if not endpoint.endswith('/'):
    endpoint += '/'
endpoint += 'rmeta/text'                       # 改用回 JSON 的端點（Tika 4.0）

r = requests.put(endpoint, data=data, headers=headers, verify=REQUESTS_VERIFY)

if r.ok:
    payload = r.json()
    # /rmeta/text 回傳陣列（[0] 為母文件；含內嵌圖片 OCR 的彙整內容）；
    # 兼容舊版直接回物件的情況。
    raw_metadata = payload[0] if isinstance(payload, list) and payload else (
        payload if isinstance(payload, dict) else {})
    text = raw_metadata.get('X-TIKA:content', '<No text content found>').strip()
    if 'Content-Type' in raw_metadata:
        headers['Content-Type'] = raw_metadata['Content-Type']
    return [Document(page_content=text, metadata=headers)]
else:
    raise Exception(f'Error calling Tika: {r.reason}')
```

**要點**
- `/rmeta/text` 回傳是**陣列**，務必取 `[0]`（否則 `list.get` 會 AttributeError）。
- 取 `[0]` 而非合併全部：Tika 端 config 已設 `inlineContent: true`，母文件內容已含內嵌圖片的 OCR 文字，`[0]['X-TIKA:content']` 即為完整內容。
- `isinstance` 判斷是為了兼容之後若換回會回物件的 Tika 版本，避免再次硬崩。

---

## 五、驗證方式

1. 改完 `main.py` 後**重建 OWUI 映像**（本地自建 `open-webui-processing`）並重啟容器。
2. 在 OWUI 介面上傳兩種檔案：
   - **純文字/文字型 PDF** → 應正常抽取、不再噴 JSONDecodeError。
   - **含文字的圖片／掃描件** → 應抽出 Gemma 轉錄的文字（走 VLM）。
3. 如需快速驗證回應格式，可在 OWUI 容器內直接打 tika：
   ```bash
   # 純文字回應應為 application/json、且結構為陣列
   curl -s -X PUT --data-binary @some.txt -H "Content-Type: text/plain" \
     http://tika:9998/rmeta/text | head -c 300
   ```

---

## 六、注意事項／風險

- **輸出格式**：Tika 4.0 內容預設為 Markdown，對 RAG 檢索有利（保留標題/清單/表格）。`/rmeta/text` 走文字處理器，內容以文字形式回傳，OWUI 端無需額外處理。
- **維護負擔**：這是對 OWUI 上游行為的修改。若日後升級 OWUI，需確認上游是否已支援 Tika 4.0（屆時可能不需此 patch）。建議在本地 fork/Dockerfile 以明確的 patch 步驟保留，避免升級時默默失效。
- **替代方案（不建議）**：改用穩定版 Tika 讓 `/tika/text` 回 JSON——會失去 VLM 圖片 OCR 能力，與本專案目標衝突。

---

## 附錄：Tika 服務端已完成的修正（context，OWUI 端不需再處理）

`ai_server` 專案 `config/tika/tika-config.json` 已修正並在真實容器驗證：

```json
"parsers": [
  { "default-parser": { "exclude": ["tesseract-ocr-parser"] } },
  { "openai-vlm-parser": { "...": "...", "inlineContent": true } }
]
```

- **坑 2（已修）**：原本只列 `openai-vlm-parser`，把所有預設 parser 取代掉 → 文字/PDF 落到 `EmptyParser` 抽不出內容。加回 `default-parser` 修復。
- **坑 3（已修）**：`default-parser` 加 `exclude: ["tesseract-ocr-parser"]` → 圖片 OCR 從本機 Tesseract 改由 `OpenAIVLMParser`（Gemma）處理；保留 `pdf-parser` → PDF 文字層仍原生抽取。實測圖片已路由到 `org.apache.tika.parser.vlm.OpenAIVLMParser` 且 Gemma 有回應。

**操作提醒**：改 `config/tika/tika-config.json` 後需 `docker restart tika`（**不可用 `docker compose restart tika`**，tika 屬 `webui` profile，compose 會視為空操作）。

**安全提醒**：`config/tika/tika-config.json` 目前含真實 Google API 金鑰且為 git 追蹤檔，測試結束請 `git checkout config/tika/tika-config.json` 擦除，切勿 commit。
