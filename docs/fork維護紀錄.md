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
| 2 | `feat/pdf-citation-source-panel` | `feat/single-active-session` | Patch B：PDF 引用來源面板（PR #25076） | `git rebase feat/single-active-session feat/pdf-citation-source-panel` |
| 3 | `feat/tika4-rmeta-loader` | `feat/pdf-citation-source-panel` | Patch C：Tika 4.0 上傳 JSONDecode 修正 | `git rebase feat/pdf-citation-source-panel feat/tika4-rmeta-loader` |
| 4 | `fork/release` | 鏡像堆疊最末端 tip | 部署分支（只 reset，不 commit） | `git reset --hard feat/tika4-rmeta-loader` |

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

**Patch B（引用上游 PR，已啟用）**
- 分支：`feat/pdf-citation-source-panel`（parent：`feat/single-active-session`）
- 來源：PR #25076（`open-webui/open-webui`，狀態 OPEN、目標 `dev`）。功能：PDF 引用來源面板——點擊精確 PDF 引用時於右側開啟該 PDF 並跳到引用頁。
- 導入方式：以 `git cherry-pick` 逐字套用上游兩個 commit（`c38f98c09` 後端、`b98415286` 前端），保留原作者、保持與上游一致以利日後同步。
- 追蹤方式：逐字移植上游 commit，故**不加 `[PATCH-B]` 行內標記**（以免污染與上游的差異）；改以「commit 出處（作者 glonor、上述 hash）＋本登記」辨識。上游合併 PR #25076 後即可於同步時移除本 Patch B。
- 影響檔案：新增 `src/lib/components/chat/SourcePanel.svelte`；其餘為上游既有檔案改動（`Citations.svelte`、`common/PDFViewer.svelte`、`Chat.svelte`、`Messages*.svelte`、`Message.svelte`、`ResponseMessage.svelte`、`backend/open_webui/config.py`、`backend/open_webui/utils/middleware.py`）。
- 交付文件：`docs/PDF引用來源面板.md`

**Patch C（自製功能，已啟用）**
- 分支：`feat/tika4-rmeta-loader`（parent：`feat/pdf-citation-source-panel`）
- 功能說明：修正 OWUI 上傳檔案時的 `JSONDecodeError`。Apache Tika 4.0 把 `/tika/text` 端點輸出從 JSON 物件改為純文字，`TikaLoader.load()` 的 `r.json()` 因此解析失敗；改打回 JSON 的 `/rmeta/text` 端點並處理其陣列回應（取 `[0]` 為母文件）。因圖片 OCR 的 VLM parser 只在 Tika 4.0 提供，不能靠降版解決。
- 改過的檔案（皆 `[PATCH-C]` 標記）：
  - 後端：`backend/open_webui/retrieval/loaders/main.py`（`TikaLoader.load()`）
- 程式碼標記：`[PATCH-C]`
- 交付文件：`docs/Tika4上傳修正.md`
- 上游動向：若日後升級 OWUI，先確認上游是否已支援 Tika 4.0；若上游已順應，可於同步時評估移除本 Patch C。

**`fork/release`（部署分支）**
- 定位：對外部署用的分支，內容 = 堆疊最末端 tip（目前為 Patch C）。
- 更新方式：確認堆疊已重新 rebase、驗證通過後，`git checkout fork/release && git reset --hard feat/tika4-rmeta-loader`。
- 只用 `reset --hard` 更新，不直接在這條分支上 commit。

**`feat/exact-pdf-citation-source-panel`（上游追蹤分支的殘留副本，非本 fork 自製，不在堆疊內）**
- 來源：從上游 open-webui 帶過來的分支（commit 作者為上游維護者 Tim Baek），不是本 fork 開發的功能。
- 現況（2026-08-14 查證）：**上游已刪除此分支**（`git ls-remote --heads upstream | grep exact` 無結果），只剩 origin 上的一份殘留副本 `b711935dd`，本地無同名分支。與其 merge-base 相比沒有任何內容差異——上游從未往裡面加程式碼。
- 處理方式：**不需要**合併進 `main` 或做任何 rebase。上游既已刪分支，此觀察點已失去意義，可於下次同步時評估刪除 origin 上的殘留副本（刪遠端分支依 B 區須停下確認）。
- 註：其功能（PDF 引用面板）我方已以 Patch B（cherry-pick PR #25076）提前導入，兩者互不影響。

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
- 依「分支堆疊表」對堆疊分支做 `git rebase`（`feat/single-active-session`、`feat/pdf-citation-source-panel`、`feat/tika4-rmeta-loader`）
- 對 `fork/release` 的 `git reset --hard <堆疊最末端 tip>`（目前為 `feat/tika4-rmeta-loader`）

**AI 必須停下、回報、等我確認後才能做：**
- 解決任何 merge / rebase / cherry-pick 衝突（先說明衝突內容與建議，不要自行決定保留哪邊）
- 任何 `git push`，特別是 `--force`
- 對「分支堆疊表」以外的分支做 `reset --hard`
- 修改 `docs/fork維護紀錄.md` 於 `main` 以外的任何分支
- 把 `feat/exact-pdf-citation-source-panel` 的內容合併進 `main` 或其他分支
- 刪除 `[PATCH-A]` / `[PATCH-B]` 標記的程式碼
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
| `feat/pdf-citation-source-panel` | `git rebase feat/single-active-session feat/pdf-citation-source-panel` | `[成功 / 有衝突]` |
| `feat/tika4-rmeta-loader` | `git rebase feat/pdf-citation-source-panel feat/tika4-rmeta-loader` | `[成功 / 有衝突]` |
| `fork/release` | `git reset --hard feat/tika4-rmeta-loader` | `[完成]` |
| `feat/exact-pdf-citation-source-panel` | 上游已刪除，origin 殘留副本（僅觀察，不合併） | `[維持 / 已清除]` |

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
- [ ] `[PATCH-A]` / `[PATCH-C]` 行內標記數量與同步前一致（`grep -ro '\[PATCH-A\]' backend/ src/ | wc -l`）
- [ ] Patch A / B / C 功能實測正常（Patch B 無行內標記，靠功能實測把關）

> **rebase 乾淨 ≠ 正確。** 本次同步實際發生過：git 未報衝突卻靜默丟掉一個函式定義、留下孤兒呼叫。每次 rebase 後除了看衝突，還要驗
> (a) 刪除的行是否全屬本 patch 該改的（`git diff <parent> <branch> | grep '^-'` 逐行看）；
> (b) 用 `git range-diff <舊parent>..<舊tip> <新parent>..<新tip>` 比對 patch 本身有無非預期變化；
> (c) 跨檔案的呼叫鏈／事件鏈是否仍完整（上游大改介面時最容易在此靜默失效）。

**5. PR / 分支狀態追蹤**

| 項目 | 來源 | 狀態 | 後續動作 |
| --- | --- | --- | --- |
| Patch B | PR #25076 | `[上游未合併 / 已合併]` | `[繼續維護 / 上游合併後移除本 Patch]` |
| `feat/exact-pdf-citation-source-panel` | 上游 WIP 分支 | `[仍無內容 / 上游已開始開發]` | `[繼續觀察 / 評估是否採用]` |

> **偵測 Patch B 是否可移除**（兩關卡都成立才移除；移除屬破壞性，**須停下等確認**後依「D-2」執行）：
> - 關卡一（PR 已合併）：`gh pr view 25076 -R open-webui/open-webui --json state,mergedAt` → `state` 為 `MERGED`。
> - 關卡二（功能已進追蹤線 `upstream/main`）：本次 `git merge upstream/main` 後，`git cat-file -e main:src/lib/components/chat/SourcePanel.svelte` 成立（main 已含該功能檔）。
> - 只到關卡一（PR 通常先進 `dev`）**先不移除**——否則下個上游發版前會憑空少掉此功能；等關卡二成立再處理。
> - 移除前確認：`git diff main feat/pdf-citation-source-panel` 應僅剩無關差異；若上游 squash/改寫致仍有實質差異，先評估 Patch B 要保留或調整，再決定是否移除。

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
