# Fork 定期維護文件: `open-webui`

> 用法：
> 1. 複製本檔到你的專案，**先填好「A. 專案設定」**（只填一次）。
> 2. 要同步時，把整份文件交給 AI 並說「照本文件執行同步」。
> 3. AI 依「B. 執行授權」行動，並在「C. 本次執行紀錄」回填結果。
>
> 分支操作步驟（新增／移除 Patch）見「D. 分支操作 SOP」。
>
> **本文件是分支拓撲與 Patch 登記的唯一權威來源，只在 `main` 維護。** 任何 patch 分支不得修改本文件（見「A. 分支堆疊表」與「B. 執行授權」）。

---

## A. 專案設定（建檔時填一次，AI 以此為執行依據）

**上游**
- 網址：`https://github.com/open-webui/open-webui.git`（remote 名稱：`upstream`）
- 追蹤分支：`upstream/main`（**穩定發版線**，只跟正式版號如 v0.10.2；非每日開發的 `upstream/dev`）

> 為何追 `main` 而非 `dev`：`upstream/main` 是上游定期打版號（v0.10.x）的穩定發版分支，經過發版驗證、較適合部署；`upstream/dev` 是每日開發主線、未發版、可能含 bug。本 fork 已於 2026-07-03 從追 `dev` 改為追 `main`。

### 分支堆疊表（Single Source of Truth）

**這張表是「誰是誰下游」的唯一依據。** 由上游到下游依序疊加，每條分支 rebase 到它的 parent；**某分支的下游 = 本表中 parent 指向它的那一列**。

| 順序 | 分支 | parent（上游） | 角色 | 更新指令 |
| --- | --- | --- | --- | --- |
| 0 | `main` | `upstream/main` | 上游同步線 + 本維護文件唯一維護處 | `git merge upstream/main` |
| 1 | `feat/single-active-session` | `main` | Patch A：單一有效登入 | `git rebase main feat/single-active-session` |
| 2 | `fork/release` | 鏡像堆疊最末端 tip | 部署分支（只 reset，不 commit） | `git reset --hard feat/single-active-session` |

> 2026-09-14（v0.11.3 同步）：Patch B、Patch C 皆已整支移除，堆疊由四層收斂為兩層。細節見下方「已移除的 Patch」與「部署備忘」。

> 新增/移除 Patch：只改本表與下方登記（都在 `main`），再依表重新 rebase 堆疊即可。堆疊順序改變時，同步更新各列的 parent 與更新指令。完整步驟見「D. 分支操作 SOP」。

**Patch A（自製功能，已啟用）**
- 分支：`feat/single-active-session`（parent：`main`）
- 功能說明：單一有效登入——同帳號只保留最後一次登入，前次登入立即失效。
- 改過的檔案（皆 `[PATCH-A]` 標記，各一小段）：
  - 後端：`backend/open_webui/utils/auth.py`、`backend/open_webui/routers/auths.py`
  - 前端（被踢出時正確轉跳登入頁、避免無限轉跳迴圈）：`src/routes/auth/+page.svelte`、`src/routes/+layout.svelte`
- 新增檔案：`backend/open_webui/models/user_sessions.py`、`backend/open_webui/migrations/versions/a1c0ffee5e55_add_user_session_table.py`、`backend/open_webui/utils/single_session.py`、`docs/單一有效登入.md`
- 程式碼標記：`[PATCH-A]`

> ⚠️ **每次跨版本同步必做：重新指向 migration 的 `down_revision`。**
> Patch A 是本 fork 唯一動到資料庫 schema 的 patch（新增 `user_session` 表）。它的遷移檔 `a1c0ffee5e55` 把 `down_revision` 釘在**當時**上游的 alembic head；上游新版一旦加了新遷移，這裡就會變成**兩個 head**，`alembic upgrade head` 直接失敗。
>
> **這是靜默故障**：rebase 不會衝突、程式碼能編譯、容器照樣啟動，但 `user_session` 表建不出來，單一有效登入等於沒開，沒有任何錯誤訊息指向這裡。
>
> 做法（rebase Patch A 之後、驗證之前）：
> 1. 找出上游新 head：`ls backend/open_webui/migrations/versions/*.py`，取沒有被任何檔案當作 `down_revision` 引用、且不是 `a1c0ffee5e55` 的那一個。
> 2. 改 `a1c0ffee5e55_add_user_session_table.py` 的 `down_revision`（連同 docstring 的 `Revises:`）指向它。
> 3. 驗證只剩單一 head——啟動容器後 `select * from alembic_version` 應為 `a1c0ffee5e55`，且啟動 log 出現 `Running upgrade <上游新head> -> a1c0ffee5e55`。
>
> 歷次指向：`42e2978c7933`（v0.10.2）→ `f0bd01a18a3d`（v0.11.0）。

**`fork/release`（部署分支）**
- 定位：對外部署用的分支，內容 = 堆疊最末端 tip（目前為 Patch A）。
- 更新方式：確認堆疊已重新 rebase、驗證通過後，`git checkout fork/release && git reset --hard feat/single-active-session`。
- 只用 `reset --hard` 更新，不直接在這條分支上 commit。

### 已移除的 Patch（歷史紀錄，分支已刪除）

**Patch B（PDF 引用來源面板，於 v0.11.3 同步時移除）**
- 原分支：`feat/pdf-citation-source-panel`（parent：`feat/single-active-session`）。舊內容可從備份 tag `fork-v0.11.0-stack` 回溯。
- 原功能：來源 PR #25076，逐字 cherry-pick 上游兩個 commit（`c38f98c09` 後端、`b98415286` 前端），點擊精確 PDF 引用時於右側開啟該 PDF 並跳到引用頁。
- **移除原因**：PR #25076 已於 2026-08-28 被上游作者正式 **CLOSED**（非合併），上游選擇了不同方向——`display_file` 工具機制（由 AI 主動觸發開檔，非點擊引用自動跳頁），明確表示不打算走這個 PR 的體驗路線。原訂「PR 合併即移除」的關卡永久不會成立。
- **決策**：與其無限期維護一支上游已拒絕方向的 cherry-pick patch，選擇整支移除、接受 UX 改變（使用者不再有「點擊引用自動跳頁」功能）。
- 交付文件 `docs/PDF引用來源面板.md` 隨分支一併移除，需要時可從 `fork-v0.11.0-stack` tag 取回。

**Patch C（Tika 4.0 上傳修正，於 v0.11.3 同步時移除，改用上游原生方案）**
- 原分支：`feat/tika4-rmeta-loader`（parent：`feat/pdf-citation-source-panel`）。舊內容可從備份 tag `fork-v0.11.0-stack` 回溯。
- 原功能：修正 `TikaLoader.load()` 對 Apache Tika 4.0 的 `JSONDecodeError`，改打 `/rmeta/text` 端點通吃 Tika 3.x/4.x。
- **移除原因**：上游在 v0.11.0→v0.11.3 之間原生修好同一個問題，新增 `RAG.TIKA_SERVER_VERSION` 設定（環境變數 `TIKA_SERVER_VERSION`，預設 `'3'`），依版本切換端點：`'3'` 打 `tika/text`（讀 `X-TIKA:content`）、`'4'` 打 `tika/json/text`（讀 `tk:content`）。串接路徑（`retrieval/utils.py`、`routers/retrieval.py`、admin API `RAGConfigForm.TIKA_SERVER_VERSION`）皆完整，可在 Admin → Documents 後台直接切換，不必改程式碼。
- **決策**：改用上游原生方案，移除自製 patch 降低長期維護面。
- ⚠️ **部署配套動作（必做，見下方「部署備忘」）**：上游預設值是 `'3'`，本 fork 部署依賴 Tika 4.0（圖片 OCR 的 VLM parser 只有 4.0 提供）。若同步後沒有把 `TIKA_SERVER_VERSION` 設成 `'4'`，會**靜默退回** Patch C 修復前的 `JSONDecodeError`，且不會有任何錯誤訊息指向這裡。
- ⚠️ **驗證時發現的第二個坑：`tk:content` 這個鍵名要求夠新的 Tika 4.0 SNAPSHOT build**——2026-09-14 實測本機快取的舊 image（build 2026-07-25）回應仍是 `X-TIKA:content`（跟 v3 一樣），`tk:content` 不存在，導致 `server_version='4'` 雖不噴錯，卻**靜默**拿到空字串 `<No text content found>`，比原本的 `JSONDecodeError` 更難察覺。重新 `docker pull apache/tika:4.0.0-SNAPSHOT-full` 拿到新 image（build 2026-08-18）後，回應才改用 `tk:content`，上游程式碼與實測結果一致。**結論：Tika 專案本身在這兩個 SNAPSHOT build 之間把 metadata key 命名從 `X-TIKA:` 改成 `tk:`，這不是上游 OWUI 程式碼的問題，是 SNAPSHOT image 版本飄移的問題。**
- 交付文件 `docs/Tika4上傳修正.md` 隨分支一併移除，需要時可從 `fork-v0.11.0-stack` tag 取回。

### 部署備忘

- **Tika 版本設定（v0.11.3 起必做）**：本 fork 部署使用 Apache Tika 4.0（原因：圖片 OCR 的 VLM parser 只有 4.0 提供，不能降版解決）。上游原生的 `TIKA_SERVER_VERSION` 設定預設是 `'3'`，**部署時必須明確設成 `'4'`**（環境變數 `TIKA_SERVER_VERSION=4`，或啟動後於 Admin → Documents 後台設定），否則檔案上傳會靜默回到 `JSONDecodeError`（v0.11.3 之前由已移除的 Patch C 修復，見上方「已移除的 Patch」）。
- **Tika image 必須夠新（v0.11.3 起必做）**：`apache/tika:4.0.0-SNAPSHOT-full` 是浮動 tag，SNAPSHOT 內容會隨時間改變。實測 2026-07-25 的 build 用 `X-TIKA:content`、2026-08-18 之後的 build 才改用上游程式碼要讀的 `tk:content`。部署或重建映像前務必 `docker pull` 拿最新 SNAPSHOT，並用本機驗證方式（見下）確認 JSON 回應含 `tk:content` 鍵，否則會遇到「不噴錯但抽出空文字」的靜默故障：
  ```bash
  curl -s -X PUT --data-binary @somefile.txt -H "Content-Type: text/plain" \
    http://<TIKA_HOST>:9998/tika/json/text | grep -o "tk:content"
  ```
  沒有輸出就代表這個 Tika image 太舊，`TIKA_SERVER_VERSION=4` 對它無效。
- 本 repo 未 tracked 任何設定此值的 `docker-compose`/`.env`（Tika 服務為外部自建），故每個部署環境都要自行確認此設定，不會由程式碼預設帶出正確值。

### 維護文件規則（避免 rebase 衝突與拓撲分歧）

- **本文件（`docs/fork維護紀錄.md`）只在 `main` 維護**，patch 分支不得手動修改；拓撲/登記變更一律改 `main`。
- **`.gitattributes` 已設 `docs/fork維護紀錄.md merge=ours`**：rebase 時此文件一律保留 parent（→ `main`）版本，不衝突、並自動把各分支拉回 `main` 版本。
- **一次性 bootstrap（每個 clone 各做一次）**：`git config merge.ours.driver true`（啟用 `merge=ours` 驅動；驅動定義存於本機 `.git/config`、不隨 push）。

---

## B. 執行授權（AI 必須遵守）

**AI 可自行執行：**
- `git status`、`git fetch upstream`、`git fetch origin`、`git log`、`git diff`（唯讀）
- 查上游 PR 狀態（唯讀）：`gh pr view <PR編號> -R open-webui/open-webui --json state,baseRefName,mergedAt`
- `main` 合併上游：`git merge upstream/main`（若有衝突，停下回報，見下方）
- 依「分支堆疊表」對堆疊分支做 `git rebase`（`feat/single-active-session`）
- 對 `fork/release` 的 `git reset --hard <堆疊最末端 tip>`（目前為 `feat/single-active-session`）

**AI 必須停下、回報、等我確認後才能做：**
- 解決任何 merge / rebase / cherry-pick 衝突（先說明衝突內容與建議，不要自行決定保留哪邊）
- 任何 `git push`，特別是 `--force`
- 對「分支堆疊表」以外的分支做 `reset --hard`
- 修改 `docs/fork維護紀錄.md` 於 `main` 以外的任何分支
- 把非本 fork 自製的上游觀察分支內容合併進 `main` 或其他分支
- 刪除 `[PATCH-A]` 標記的程式碼
- 設定中沒寫到的破壞性操作

**出錯時的復原：**
- rebase 中途要放棄：`git rebase --abort`
- cherry-pick 中途要放棄：`git cherry-pick --abort`
- 分支被改壞，找回原狀態：`git reflog` → `git reset --hard <好的 commit>`
- 不確定後果時：停下回報，不要繼續往下執行。

---

## C. 本次執行紀錄（每次同步新增一份，複製以下整段）

### `YYYY-MM-DD` — `[每週同步 / PR 合併後清理]`

**執行人 / AI:** `[名稱]`
**上游基準:** `upstream/main` @ `[commit hash]`

**1. 同步前檢查**
- [ ] `git status` 乾淨，無未提交改動
- [ ] `git fetch upstream`、`git fetch origin` 已完成
- [ ] `git config --get merge.ours.driver` 回 `true`（未設先 `git config merge.ours.driver true`）
- [ ] 確認上游有無重大變更（破壞性改動、相依套件升級）

**2. 分支同步**（依「分支堆疊表」順序，由上游到下游）

| 分支 | 指令 | 結果 |
| --- | --- | --- |
| `main` | `git merge upstream/main` | `[成功 / 有衝突]` |
| `feat/single-active-session` | `git rebase main feat/single-active-session` | `[成功 / 有衝突]` |
| `fork/release` | `git reset --hard feat/single-active-session` | `[完成]` |

> **rebase Patch A 之後、往下疊之前**：重新指向 `a1c0ffee5e55` 的 `down_revision`（見 A 區 Patch A 登記的 ⚠️ 說明）。跨版本同步時不做這步，`alembic upgrade head` 會因 multiple heads 失敗，且**不會有任何錯誤指向 Patch A**。
> - 本次指向：`[上游新 head]`

**3. 衝突處理**（無則填「無」；依 B 區規則，需等確認後才動手）
- 衝突檔案：`[檔案路徑]`
- 保留版本：`[我方 patch / 上游]`
- 處理說明：`[一句話]`

**4. 驗證**
- [ ] `git log --oneline` 確認 `main` 已包含上游最新 commit
- [ ] 本地建置或啟動測試通過
- [ ] **Alembic 單一 head**：容器啟動 log 有 `Running upgrade <上游新head> -> a1c0ffee5e55`，且 `alembic_version` = `a1c0ffee5e55`
- [ ] `[PATCH-A]` 行內標記數量與同步前一致（`grep -ro '\[PATCH-A\]' backend/ src/ --exclude-dir=__pycache__ | wc -l`）
- [ ] Patch A 功能實測正常

> **rebase 乾淨 ≠ 正確。** 本次同步實際發生過：git 未報衝突卻靜默丟掉一個函式定義、留下孤兒呼叫。每次 rebase 後除了看衝突，還要驗
> (a) 刪除的行是否全屬本 patch 該改的（`git diff <parent> <branch> | grep '^-'` 逐行看）；
> (b) 用 `git range-diff <舊parent>..<舊tip> <新parent>..<新tip>` 比對 patch 本身有無非預期變化；
> (c) 跨檔案的呼叫鏈／事件鏈是否仍完整（上游大改介面時最容易在此靜默失效）。

**5. PR / 分支狀態追蹤**

（目前堆疊只剩 Patch A，無引用型 patch 需要追蹤 PR 狀態。若新增 Patch，依「D-1」登記後在此補上追蹤表。）

**6. 結論**
- 本次結果：`[順利 / 需後續處理]`
- 待辦：`[下次要注意的事項]`

---

### `2026-08-14` — `跨版本同步 v0.10.2 → v0.11.0`

**執行人 / AI:** Claude Code（Opus 5）
**上游基準:** tag `v0.11.0` @ `f9590b801`

> 註：`upstream/main` 當時已在 `01f4282f1`（領先 v0.11.0 兩個 commit），**刻意只合併到 tag `v0.11.0`**，以對齊正式發版點。

**1. 同步前檢查**
- [x] `git status` 乾淨
- [x] `git fetch upstream` / `origin` 完成
- [x] `merge.ours.driver` = `true`
- [x] 同步前建立回退點（本 fork 首次打 tag，已推 origin）：
  - `fork-v0.10.2-main` → `13178b8e6`
  - `fork-v0.10.2-stack` → `0143a22d1`（涵蓋 A/B/C，因 A、B 皆為 C 的祖先）

**2. 分支同步**

| 分支 | 結果 | 新 tip |
| --- | --- | --- |
| `main` | 合併乾淨（事前以 `git merge-tree --write-tree` 預檢，exit 0）；649 檔 +85388/−37651 | `929844029` |
| `feat/single-active-session` | 2 段衝突 + 1 處靜默丟失，已處理 | `8b7963112` |
| `feat/pdf-citation-source-panel` | 7 段衝突，已處理 | `e16ebeade` |
| `feat/tika4-rmeta-loader` | **零衝突**（上游未碰 `TikaLoader`），`range-diff` 顯示逐位元組相同 | `7a9d5c92e` |
| `fork/release` | `reset --hard feat/tika4-rmeta-loader` 完成 | `7a9d5c92e` |
| `feat/exact-pdf-citation-source-panel` | 上游已刪除該分支，origin 殘留 `b711935dd` | 未動 |

> Patch A 的 `down_revision` 已重指：`42e2978c7933` → `f0bd01a18a3d`（commit `8b7963112`）。

**3. 衝突處理**

*Patch A*
- `src/routes/+layout.svelte`：上游 v0.11.0 自行實作了 `clearExpiredSession()`，是 Patch A 原本 `redirectToAuthAfterUnauthorized()` 的**超集**（多做清 `tokenTimer`、清 OAuth cookie、呼叫 `userSignOut()`）。改呼叫上游函式，Patch A 因此縮為 **268 行純新增、0 行刪除**，不再改動任何上游程式碼。
- `src/routes/auth/+page.svelte`：純註解衝突，保留 `[PATCH-A]` 註解。
- **靜默丟失**：rebase 未報衝突卻移除了 `redirectToAuthAfterUnauthorized` 的定義，留下孤兒呼叫。由解衝突後的 grep 覆驗抓到，非 git 提示。

*Patch B*
- 6 段成因相同：上游在同一 prop 位置新增 `{onInsertToNote}`，Patch B 在同位置新增 `on:openSourcePanel`。兩者皆為純新增 → **兩邊都留**。（`Chat.svelte`、`Messages.svelte`、`Message.svelte`、`MultiResponseMessages.svelte`×2）
- `Chat.svelte` ChatControls 區塊：上游把開關由 `{#if $showControls}` 改為 `{#if !embedded}`。採用上游版本，並依使用者決定將 SourcePanel 一併 gate 為 `{#if sourcePanelTarget && !embedded}`——`embedded` 是 v0.11.0 全新引入（舊版 0 次出現），Patch B 原本無從考慮；唯一使用者是 `NoteEditor.svelte`，內嵌聊天不宜再開 35% 寬側邊面板。
- `Chat.svelte` `containerId={chatContainerId}`：上下文位移造成的假衝突，保留上游。

**4. 驗證**（三個 patch 皆以 Docker 實機測試，非僅編譯）
- [x] Alembic 單一 head：log 有 `Running upgrade f0bd01a18a3d -> a1c0ffee5e55`，`alembic_version` = `a1c0ffee5e55`，`user_session` 表與 CASCADE 外鍵正確
- [x] 標記數量：`[PATCH-A]` 9 處 / 7 檔、`[PATCH-C]` 2 處
- [x] 前端建置：6355 modules `✓ built`，零錯誤
- [x] **Patch A**：兩個隔離瀏覽器情境同帳號登入，A 被踢後自動落 `/auth?redirect=%2F`（非空白頁）、token 與 cookie 清空、無轉跳迴圈、B 仍正常；後端舊 token 401 / 新 token 200。log 時序 `disconnect_user_sessions` → 17ms 後 401，證實走的是本次改動的 socket 路徑。
- [x] **Patch B**：上傳 6 頁 PDF + 以 API 灌入帶 `[1#0]/[1#1]/[1#2]` 的訊息（免 LLM）。三個引用分別捲到 scrollTop 0 / 1950 / 3900（每頁 975px，精準對應第 1/3/5 頁）；手動捲開後重複點擊仍能回正確頁（`scrollRequestId` 有效）；關閉正常、零 console error。
- [x] **Patch C**：以 `inspect.getsource` 斷言執行版本後，對兩個版本的 Tika 各實打一次。
  - **Tika 3.3.1**（`apache/tika:latest`）：`/tika/text` 回 JSON **物件**、`/rmeta/text` 回 JSON **陣列**——兩個端點皆可解析，故舊版不會踩到此 bug。
  - **Tika 4.0**（`apache/tika:4.0.0-SNAPSHOT-full`）：`/tika/text` 回**純文字**，`json.loads` 噴 `JSONDecodeError: Expecting value: line 17 column 1`；`/rmeta/text` 仍回 JSON 陣列（`len=1`、`[0]` 含 `X-TIKA:content`）。
  - **A/B 對照**（同一份 `.txt`、同一台 Tika 4.0）：上游未修補版 → `JSONDecodeError`；rebase 後的 PATCH-C 版 → 成功抽出全文，metadata `Content-Type: text/plain; charset=UTF-8`。
  - 另測空白 PDF 正確落到 `<No text content found>` 備援。

> Patch C 的移除判定：直接對 Tika 4.0 打 `/tika/text`，若上游哪天改回傳 JSON、或 OWUI 自行改用 `/rmeta/text`，才可評估移除。截至 v0.11.0，上游仍是 `tika/text` + `r.json()`。

**5. PR / 分支狀態追蹤**

| 項目 | 來源 | 狀態 | 後續動作 |
| --- | --- | --- | --- |
| Patch B | PR #25076 | 仍 `OPEN`、目標 `dev`、`mergedAt: null` | **繼續維護**。關卡一、二皆不成立（v0.11.0 無 `SourcePanel.svelte`） |
| Patch C | 上游 Tika 支援 | v0.11.0 仍為 `tika/text` + `r.json()`，**未修** | 繼續維護 |
| `feat/exact-pdf-citation-source-panel` | 上游 WIP 分支 | **上游已刪除**，origin 殘留副本 | 觀察點已失效，下次評估刪除 origin 殘留 |

**6. 結論**
- 本次結果：順利。三個 patch 全部保留並實測通過。
- 待辦：
  - 下次同步前先看 `docker builder du`。本次快取僅命中 2 層，全量重建約 35–40 分鐘（`npm ci` 20 分、`apt-get` 16 分，皆為網路等待）。
  - 以 `USE_SLIM=true` 建置的映像**執行時**才抓 embedding 模型，會卡住啟動；測試時加 `-e RAG_EMBEDDING_ENGINE=ollama` 繞開。config 首次啟動即 seed 進 DB，換 env 需連 volume 一併清除才生效。
  - 評估刪除 origin 上的 `feat/exact-pdf-citation-source-panel` 殘留副本。

---

### `2026-09-14` — `跨版本同步 v0.11.0 → v0.11.3 + 移除 Patch B/C`

**執行人 / AI:** Claude Code（Sonnet 5）
**上游基準:** tag `v0.11.3` @ `2a960a59f`

> 註：`upstream/main` 當時已在 `0a7c15832`（領先 v0.11.3 1 個非功能性 commit：CI 設定），**刻意只合併到 tag `v0.11.3`**，以對齊正式發版點。

**1. 同步前檢查**
- [x] `git status` 乾淨
- [x] `git fetch upstream` / `origin` 完成
- [x] `merge.ours.driver` = `true`
- [x] 同步前建立回退點，已推 origin：
  - `fork-v0.11.0-main` → `6510b15b8`
  - `fork-v0.11.0-stack` → `943613976`（涵蓋 A/B/C，因 A、B 皆為 C 的祖先；Patch B、C 移除後這是唯一能回溯舊內容的地方）

**2. 分支同步與拓撲異動**

| 分支 | 結果 | 新 tip |
| --- | --- | --- |
| `main` | 合併乾淨（事前以 `git merge-tree --write-tree` 預檢，exit 0） | `5338a6dee` |
| `feat/single-active-session` | 1 段衝突（`src/routes/auth/+page.svelte`，假衝突，兩邊相容），已處理 | `8bc97c9b9` |
| `feat/pdf-citation-source-panel` / `feat/tika4-rmeta-loader` | **整支移除**（Patch B、C，依 SOP D-2），未 rebase 直接跳過 | 分支已刪除 |
| `fork/release` | `reset --hard feat/single-active-session` | 同 Patch A tip |

> Patch A 的 `down_revision` 已重指：`f0bd01a18a3d` → `d4c1a8e37b62`（commit `8bc97c9b9`，新上游 migration 鏈：`f0bd01a18a3d → 1ce6ade7d93b → 6d09d1bf1f23 → d4c1a8e37b62`）。

**3. 衝突處理**

*Patch A*
- `src/routes/auth/+page.svelte`：上游 v0.11.3 新增 `state=logout` 判斷（`if ($user && !logout)`，供使用者主動登出時抑制自動導回/OAuth 自動導向），與 Patch A 原本只加在同位置的說明註解（`if ($user)` 條件式本身未改）重疊成衝突。兩邊語意互不衝突（一個管「主動登出」、一個管「被踢出」），保留上游新條件式＋Patch A 的 `[PATCH-A]` 註解，未刪任何一方邏輯。

*Patch B / C*：無 rebase 衝突可言——整支移除，未嘗試 rebase。

**4. 驗證**（本次未走完整 Docker image build——建置卡住/效率異常，見「結論」——改用本機 venv + `bash dev.sh` 風格直接啟動＋API 測試，驗證目的等價）
- [x] `[PATCH-A]` 行內標記數量：9 處 / 7 檔，與 v0.11.0 同步時一致（`--exclude-dir=__pycache__` 排除 bytecode 誤報）
- [x] `git range-diff fork-v0.11.0-main..fork-v0.11.0-stack main..feat/single-active-session`：Patch A 自身 2 個功能 commit 內容與預期一致，無非預期變化
- [x] `npm run check`：7791 個既有型別問題，與合併前數量一致，無新增
- [x] 本機啟動測試：`.venv` + `pip install -r backend/requirements.txt` + 直接跑 `uvicorn open_webui.main:app`（SQLite），`import open_webui.main` 成功、伺服器正常啟動
- [x] **Alembic 單一 head**：啟動 log 實際出現 `Running upgrade d4c1a8e37b62 -> a1c0ffee5e55, Add user_session table`，`user_session` 表建立成功
- [x] **Patch A 功能實測**（API 層，等價於雙瀏覽器測試）：同帳號登入兩次拿到不同 token；舊 token 打 `/api/v1/auths/` → `401`；新 token 打同一支 API → `200`
- [x] **Tika 原生方案 smoke test**：直接呼叫 `TikaLoader(server_version='4')` 對 `apache/tika:4.0.0-SNAPSHOT-full` 容器，正確抽出全文；`server_version='3'` 對同一台 Tika 4.0 重現原始 `JSONDecodeError`，驗證了「上游原生方案確實解決同一個問題」
  - ⚠️ 過程中發現本機快取的 Tika image（build 2026-07-25）用的是 `X-TIKA:content`、不是上游程式碼要讀的 `tk:content`，導致 `server_version='4'` 不噴錯但靜默拿到空字串；重新 `docker pull` 到 2026-08-18 的 build 後才正確。已記錄進 A 區「部署備忘」。

**5. PR / 分支狀態追蹤**

| 項目 | 來源 | 狀態 | 後續動作 |
| --- | --- | --- | --- |
| Patch B | PR #25076 | 已於 2026-08-28 **CLOSED**（非合併），上游改走 `display_file` 工具機制 | **已整支移除**（見 A 區「已移除的 Patch」） |
| Patch C | 上游 Tika 支援 | v0.11.3 已原生支援（`RAG.TIKA_SERVER_VERSION`），非 Patch C 的做法但解決同一問題 | **已整支移除**，改用上游原生方案；部署須設 `TIKA_SERVER_VERSION=4` |
| `feat/exact-pdf-citation-source-panel` | 上游已刪除的觀察分支 | origin 殘留副本 `b711935dd`，與 merge-base 無差異 | 本次一併清除（見下方分支清理） |
| `pr-25076`（未登記殘留分支） | 先前手動測試 PR #25076 cherry-pick 用 | 已確認為測試殘留 | 本次一併清除 |

**6. 結論**
- 本次結果：順利。Patch A rebase 成功並實測通過，Patch B/C 整支移除且移除依據都經過查證（PR 已 CLOSED、上游原生方案實測可行），堆疊由四層收斂為兩層。
- 這次沒有走完整 Docker image build 驗證：嘗試建置時觀察到疑似卡住（`docker events` 過去 60 分鐘無任何 pull/build 事件，但同時 `docker pull hello-world` 7 秒完成、證明非網路問題），研判是這次建置流程本身的問題，改用本機 Python venv 直接跑 `uvicorn`（`bash dev.sh` 風格）達到同等驗證效果，且更快。下次同步建議先確認 Docker build 沒有類似異常再投入時間等待，或優先採用本機驗證路徑。
- 待辦：
  - 找時間查清楚這次 Docker image build 卡住的根因（是這台機器的 buildx 狀態問題，還是 Dockerfile 本身在 v0.11.3 有變化導致建置變慢/卡住），影響往後是否還能倚賴 Docker 驗證流程。
  - `apache/tika:4.0.0-SNAPSHOT-full` 是浮動 SNAPSHOT tag，`tk:content` 這個上游程式碼依賴的 metadata key 只在夠新的 build（2026-08-18 之後）才存在。部署或重建正式 Tika 服務前務必重新 `docker pull` 並用文件裡「部署備忘」的 curl 指令驗證，不能假設本機快取的舊 image 還適用。
  - 驗證用的 `.venv-v0113-test/`、`.scratch-tika-test/`、測試用 Docker 容器（`tika4-test-new`）與 image 為本機一次性產物，非追蹤內容，會在完成後清理，不會進 commit。

---

## D. 分支操作 SOP（新增／移除 Patch，只在需要時執行）

> 原則：**登記改在 `main`、程式碼放在分支**（見「A. 維護文件規則」）。所有 `push --force`、`reset --hard`、刪遠端分支，依「B. 執行授權」須逐一停下確認。

### D-1 新增 Patch 分支

前置：先決定新 Patch 疊在誰之上（parent＝堆疊表現有最末端 patch，或指定某一層）。

1. **開分支**（從 parent）：`git switch <parent> && git switch -c <新分支名>`
   - 命名：`feat/<簡短功能名>`；勿與上游觀察分支（如 `feat/exact-...`）同名。
2. **放程式碼**（只在新分支 commit，**勿改本文件**）：
   - 自製功能：改動處加 `[PATCH-A/B]` 標記，能新增檔就別改既有檔。
   - 引用上游 PR：`git cherry-pick <上游 commit...>`，保留原作者、**不加**行內標記。
3. **登記**（切回 `main` 改本文件）：`git switch main`
   - 在「分支堆疊表」插入一列（填 parent 與更新指令），並於下方新增該 Patch 登記段（分支、功能、來源、影響檔案）。
   - commit 後 `git push origin main`。
4. **重疊堆疊**（依表由該層往下 rebase；本文件由 `merge=ours` 自動以 main 為準、不衝突）：
   - `git rebase <parent> <新分支>`，再逐一 rebase 其所有下游。
5. **對齊部署**：`git switch fork/release && git reset --hard <堆疊最末端 tip>`。
6. **上線**：`git push --force-with-lease` 更新受影響分支（**逐一確認**）。

### D-2 移除 Patch 分支（例：上游已合併該 PR，清理引用型 Patch）

1. **登記**（切 `main` 改本文件）：`git switch main`
   - 從「分支堆疊表」刪除該列；把它的下游 re-parent 到它原本的 parent，並同步更新該下游列的更新指令。
   - 刪除對應的 Patch 登記段；commit 後 `git push origin main`。
2. **重疊堆疊**（跳過被移除者）：`git rebase <新 parent> <下游分支>`，再往下逐一 rebase。
3. **對齊部署**：`git switch fork/release && git reset --hard <堆疊最末端 tip>`。
4. **收尾**：確認無誤後刪本地與遠端舊分支 `git branch -D <被移除分支>`、`git push origin --delete <被移除分支>`（**刪遠端須確認**）。
5. **上線**：`git push --force-with-lease` 更新受影響分支（**逐一確認**）。
