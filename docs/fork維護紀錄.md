# Fork 定期維護文件: `open-webui`

> 用法：
> 1. 複製本檔到你的專案，**先填好「A. 專案設定」**（只填一次）。
> 2. 要同步時，把整份文件交給 AI 並說「照本文件執行同步」。
> 3. AI 依「B. 執行授權」行動，並在「C. 本次執行紀錄」回填結果。
>
> 流程細節見 [`docs/fork維護流程.md`](fork維護流程.md)。

---

## A. 專案設定（建檔時填一次，AI 以此為執行依據）

**上游**
- 網址：`https://github.com/open-webui/open-webui.git`（remote 名稱：`upstream`）
- 追蹤分支：`upstream/main`（**穩定發版線**，只跟正式版號如 v0.10.2；非每日開發的 `upstream/dev`）

> 為何追 `main` 而非 `dev`：`upstream/main` 是上游定期打版號（v0.10.x）的穩定發版分支，經過發版驗證、較適合部署；`upstream/dev` 是每日開發主線、未發版、可能含 bug。本 fork 已於 2026-07-03 從追 `dev` 改為追 `main`。

**目前實際採用的簡化模式（非通用流程文件的 patch-a/patch-b 架構）**
- 本 fork 尚未建立任何 `[PATCH-A]` / `[PATCH-B]` 自訂改動，`main` 直接合併上游：`git fetch upstream && git merge upstream/main`。
- 若之後真的需要維護「不想上游看到 / 上游還沒合併」的自訂改動，再依 [`fork維護流程.md`](fork維護流程.md) 的「一、初始建立」補建 `fork/patch-a`、`fork/patch-b` 分支，屆時下面的 Patch A / Patch B 佔位符才會啟用。

**Patch A（自製功能，尚未啟用）**
- 分支：`fork/patch-a`（尚未建立）
- 功能說明：`[一句話]`
- 改過的檔案：`[檔案路徑...]`
- 程式碼標記：`[PATCH-A]`

**Patch B（引用上游 PR，尚未啟用）**
- 分支：`fork/patch-b`（尚未建立）
- 來源：PR #`<PR編號>`，功能：`[一句話]`
- 程式碼標記：`[PATCH-B]`

**`fork/release`（部署分支）**
- 定位：對外部署用的分支，內容應等於 `main`（因為目前沒有 patch-a/patch-b，內容 = 純上游同步結果）。之後若啟用 Patch A/B，內容改為 patch-a + patch-b。
- 更新方式：確認 `main` 已同步、驗證通過後，`git checkout fork/release && git reset --hard main`。
- 只用 `reset --hard` 更新，不直接在這條分支上 commit。

**`feat/exact-pdf-citation-source-panel`（上游追蹤分支，非本 fork 自製）**
- 來源：從上游 open-webui 帶過來的分支（commit 作者為上游維護者 Tim Baek），不是本 fork 開發的功能。
- 現況：與其 merge-base 相比目前**沒有任何內容差異**——上游還沒真的往裡面加 PDF 引用來源面板的程式碼，純粹是個空的追蹤點。
- 處理方式：每次上游同步時一併 `git fetch origin` 觀察它有無新進度即可，**不需要**合併進 `main` 或做任何 rebase；等上游真的開始寫功能、且內容確定要用時，再另行評估是否要 cherry-pick 或整條合併進來。
- 不屬於 Patch A（不是自製）也不屬於 Patch B（不是我們主動要提前用的上游 PR），純觀察用，故單獨列出。

---

## B. 執行授權（AI 必須遵守）

**AI 可自行執行：**
- `git status`、`git fetch upstream`、`git fetch origin`、`git log`、`git diff`（唯讀）
- `main` 合併上游：`git merge upstream/main`（若有衝突，停下回報，見下方）
- 對 `fork/patch-a`、`fork/patch-b` 的 `git rebase`（啟用後才適用）
- 對 `fork/release` 的 `git reset --hard main`（啟用 patch-a/b 後改為 `git reset --hard fork/patch-b`）
- 檢查 `feat/exact-pdf-citation-source-panel` 有無新內容（唯讀比較，不合併、不 rebase）

**AI 必須停下、回報、等我確認後才能做：**
- 解決任何 merge / rebase / cherry-pick 衝突（先說明衝突內容與建議，不要自行決定保留哪邊）
- 任何 `git push`，特別是 `--force`
- 對 `main`、`fork/patch-a`、`fork/patch-b`、`fork/release` 以外的分支做 `reset --hard`
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
- [ ] 確認上游有無重大變更（破壞性改動、相依套件升級）

**2. 分支同步**

| 分支 | 指令 | 結果 |
| --- | --- | --- |
| `main` | `git merge upstream/main`（尚未啟用 patch-a/b，暫不走 rebase） | `[成功 / 有衝突]` |
| `fork/patch-a` | `git rebase upstream/main fork/patch-a`（尚未啟用） | `[N/A]` |
| `fork/patch-b` | `git rebase fork/patch-a fork/patch-b`（尚未啟用） | `[N/A]` |
| `fork/release` | `git reset --hard main` | `[完成]` |
| `feat/exact-pdf-citation-source-panel` | `git fetch origin`（僅觀察，不合併） | `[有新內容 / 仍無差異]` |

**3. 衝突處理**（無則填「無」；依 B 區規則，需等確認後才動手）
- 衝突檔案：`[檔案路徑]`
- 保留版本：`[我方 patch / 上游]`
- 處理說明：`[一句話]`

**4. 驗證**
- [ ] `git log --oneline` 確認 main 已包含上游最新 commit
- [ ] 本地建置或啟動測試通過
- [ ] `[PATCH-A]` / `[PATCH-B]` 功能實測正常（啟用後才適用）

**5. PR / 分支狀態追蹤**

| 項目 | 來源 | 狀態 | 後續動作 |
| --- | --- | --- | --- |
| Patch B | PR #`<PR編號>` | `[未合併 / 已合併]`（尚未啟用） | `[繼續維護 / 移除標記清理]` |
| `feat/exact-pdf-citation-source-panel` | 上游 WIP 分支 | `[仍無內容 / 上游已開始開發]` | `[繼續觀察 / 評估是否採用]` |

**6. 結論**
- 本次結果：`[順利 / 需後續處理]`
- 待辦：`[下次要注意的事項]`
</content>
