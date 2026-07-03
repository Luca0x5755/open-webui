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
| 3 | `fork/release` | 鏡像堆疊最末端 tip | 部署分支（只 reset，不 commit） | `git reset --hard feat/pdf-citation-source-panel` |

> 新增/移除 Patch：只改本表與下方登記（都在 `main`），再依表重新 rebase 堆疊即可。堆疊順序改變時，同步更新各列的 parent 與更新指令。完整步驟見「D. 分支操作 SOP」。

**Patch A（自製功能，已啟用）**
- 分支：`feat/single-active-session`（parent：`main`）
- 功能說明：單一有效登入——同帳號只保留最後一次登入，前次登入立即失效。
- 改過的檔案（皆 `[PATCH-A]` 標記，各一小段）：
  - 後端：`backend/open_webui/utils/auth.py`、`backend/open_webui/routers/auths.py`
  - 前端（被踢出時正確轉跳登入頁、避免無限轉跳迴圈）：`src/routes/auth/+page.svelte`、`src/routes/+layout.svelte`
- 新增檔案：`backend/open_webui/models/user_sessions.py`、`backend/open_webui/migrations/versions/a1c0ffee5e55_add_user_session_table.py`、`backend/open_webui/utils/single_session.py`、`docs/單一有效登入.md`
- 程式碼標記：`[PATCH-A]`

**Patch B（引用上游 PR，已啟用）**
- 分支：`feat/pdf-citation-source-panel`（parent：`feat/single-active-session`）
- 來源：PR #25076（`open-webui/open-webui`，狀態 OPEN、目標 `dev`）。功能：PDF 引用來源面板——點擊精確 PDF 引用時於右側開啟該 PDF 並跳到引用頁。
- 導入方式：以 `git cherry-pick` 逐字套用上游兩個 commit（`c38f98c09` 後端、`b98415286` 前端），保留原作者、保持與上游一致以利日後同步。
- 追蹤方式：逐字移植上游 commit，故**不加 `[PATCH-B]` 行內標記**（以免污染與上游的差異）；改以「commit 出處（作者 glonor、上述 hash）＋本登記」辨識。上游合併 PR #25076 後即可於同步時移除本 Patch B。
- 影響檔案：新增 `src/lib/components/chat/SourcePanel.svelte`；其餘為上游既有檔案改動（`Citations.svelte`、`common/PDFViewer.svelte`、`Chat.svelte`、`Messages*.svelte`、`Message.svelte`、`ResponseMessage.svelte`、`backend/open_webui/config.py`、`backend/open_webui/utils/middleware.py`）。
- 交付文件：`docs/PDF引用來源面板.md`

**`fork/release`（部署分支）**
- 定位：對外部署用的分支，內容 = 堆疊最末端 tip（目前為 Patch B）。
- 更新方式：確認堆疊已重新 rebase、驗證通過後，`git checkout fork/release && git reset --hard feat/pdf-citation-source-panel`。
- 只用 `reset --hard` 更新，不直接在這條分支上 commit。

**`feat/exact-pdf-citation-source-panel`（上游追蹤分支，非本 fork 自製，不在堆疊內）**
- 來源：從上游 open-webui 帶過來的分支（commit 作者為上游維護者 Tim Baek），不是本 fork 開發的功能。
- 現況：與其 merge-base 相比目前**沒有任何內容差異**——上游還沒真的往裡面加程式碼，純觀察點。
- 處理方式：每次同步時 `git fetch origin` 觀察其進度即可，**不需要**合併進 `main` 或做任何 rebase。
- 註：其功能（PDF 引用面板）我方已以 Patch B（cherry-pick PR #25076）提前導入；此觀察分支僅續追上游該分支自身進度，兩者互不影響。

### 維護文件規則（避免 rebase 衝突與拓撲分歧）

- **本文件（`docs/fork維護紀錄.md`）只在 `main` 維護**，patch 分支不得手動修改；拓撲/登記變更一律改 `main`。
- **`.gitattributes` 已設 `docs/fork維護紀錄.md merge=ours`**：rebase 時此文件一律保留 parent（→ `main`）版本，不衝突、並自動把各分支拉回 `main` 版本。
- **一次性 bootstrap（每個 clone 各做一次）**：`git config merge.ours.driver true`（啟用 `merge=ours` 驅動；驅動定義存於本機 `.git/config`、不隨 push）。

---

## B. 執行授權（AI 必須遵守）

**AI 可自行執行：**
- `git status`、`git fetch upstream`、`git fetch origin`、`git log`、`git diff`（唯讀）
- `main` 合併上游：`git merge upstream/main`（若有衝突，停下回報，見下方）
- 依「分支堆疊表」對堆疊分支做 `git rebase`（`feat/single-active-session`、`feat/pdf-citation-source-panel`）
- 對 `fork/release` 的 `git reset --hard <堆疊最末端 tip>`（目前為 `feat/pdf-citation-source-panel`）

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
| `fork/release` | `git reset --hard feat/pdf-citation-source-panel` | `[完成]` |
| `feat/exact-pdf-citation-source-panel` | `git fetch origin`（僅觀察，不合併） | `[有新內容 / 仍無差異]` |

**3. 衝突處理**（無則填「無」；依 B 區規則，需等確認後才動手）
- 衝突檔案：`[檔案路徑]`
- 保留版本：`[我方 patch / 上游]`
- 處理說明：`[一句話]`

**4. 驗證**
- [ ] `git log --oneline` 確認 `main` 已包含上游最新 commit
- [ ] 本地建置或啟動測試通過
- [ ] `[PATCH-A]` / `[PATCH-B]` 功能實測正常

**5. PR / 分支狀態追蹤**

| 項目 | 來源 | 狀態 | 後續動作 |
| --- | --- | --- | --- |
| Patch B | PR #25076 | `[上游未合併 / 已合併]` | `[繼續維護 / 上游合併後移除本 Patch]` |
| `feat/exact-pdf-citation-source-panel` | 上游 WIP 分支 | `[仍無內容 / 上游已開始開發]` | `[繼續觀察 / 評估是否採用]` |

**6. 結論**
- 本次結果：`[順利 / 需後續處理]`
- 待辦：`[下次要注意的事項]`

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
