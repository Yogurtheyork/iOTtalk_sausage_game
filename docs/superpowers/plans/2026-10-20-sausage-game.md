# 香腸體感投擲遊戲 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增可用鍵盤試玩、可接手機揮動的 2.5D 香腸投擲遊戲。

**Architecture:** 純 Python 核心計算飛行、碰撞和揮動；Pygame 主執行緒負責畫面與操作。獨立 SA_game 經本機 UDP 傳送三軸資料，沿用既有 DAI 啟動方式。

**Tech Stack:** Python 3、Pygame 2、標準函式庫 unittest/socket/json；手機連線沿用既有 requests 與 paho-mqtt。

**Spec:** [設計文件](../specs/2026-10-20-sausage-game-design.md)

## Global Constraints

- 保留現有 SA.py（包含使用者未提交的修改）、DAI.py、DAN.py、csmapi.py、Agent.py 與原 README。
- 第一版固定正前方與仰角，只由揮動強弱控制射程。
- 成功時整根香腸落在桌面並平躺停住，可重新準備再玩。
- 接收端僅綁定 127.0.0.1，可設定連接埠。
- 無須課程附件或外部圖片；無手機時可鍵盤離線遊玩。
- 所有新增檔案明確列於各任務；不得把現有 SA.py 修改或虛擬環境納入提交。
- 實作時才評估隔離工作區；若使用 worktree，交付需說明位置並保留現有未提交內容。

## Review Focus

1. 數值極大但有限的封包不得造成溢位或使遊戲停止；Task 2 測試限制長度與強度。
2. 窗口拖曳造成長幀間隔時仍判定正確落點；Task 1 測試一次跨越完整飛行。
3. 重新準備時不能沿用前一輪峰值或舊封包；Task 3 測試重設與過期樣本。
4. 沒有中文字型時仍能讀取操作指示；Task 4 以強制英文模式驗證。
5. 遊戲未啟動或連接埠被占用時應有可理解的行為；Task 2 測試發送與綁定失敗。

---

### Task 1: 飛行與桌面碰撞核心

**Files:** Create `game_core.py`, `tests/test_game_core.py`.

**Interfaces:** `World` dataclass 包含重力、起點、桌面矩形、香腸尺寸；`Throw(world: World, speed: float)`；`Throw.advance(dt: float) -> None`；可讀 `x, y, z, status`，status 為 flying/success/short/long/edge。`speed_from_power(power: float) -> float` 接受 0..1，回傳受限初速。

- [ ] 寫 unittest：低、中、高初速分別 short/success/long；中心在桌面但香腸越界為 edge；恰好完整落在邊界為 success。使用預設世界，讓測試明列初速與預期結果。
- [ ] 執行 `python -m unittest discover -s tests -p test_game_core.py -v`，確認因尚無核心而失敗。
- [ ] 實作世界參數、解析拋體與下降交點；以香腸底部對桌高求交，再判斷完整外框。未中桌繼續至地面，成功則歸零速度、固定位置。用不同力度校核預設世界存在可成功區間。
- [ ] 加入長時間步與細時間步結果相同的測試、非有限或負 dt 的明確拒絕測試；執行同一命令確認通過。
- [ ] 檢查差異，只提交本任務新增檔案（若執行環境允許 git 寫入）。

### Task 2: 感測驗證與本機傳輸

**Files:** Create `game_input.py`, `SA_game.py`, `tests/test_game_input.py`.

**Interfaces:** `parse_axes(data: object) -> tuple[float,float,float] | None`；`send_axes(axes: tuple, port: int) -> None`；`SensorReceiver(port: int)` 提供 `poll(now: float) -> list[tuple[float,tuple]]`、`close()`。接收時間使用本機 monotonic，資料格式為 JSON 三元素陣列。

- [ ] 寫 unittest：接受直接／單層包裝三軸；拒絕布林、NaN、無限大、錯誤長度、巢狀垃圾與超出合理界限的數值。上限預設每軸絕對值 1e6，封包最多 256 bytes。
- [ ] 執行 `python -m unittest discover -s tests -p test_game_input.py -v`，確認缺少模組失敗。
- [ ] 實作標準函式庫輸入模組。預設連接埠 8765；發送與接收由環境變數 SAUSAGE_PORT 共用，可由遊戲 --port 覆寫接收端。每幀最多讀取 64 包，只交付最新有效樣本，避免舊峰值排隊；過載時清除積壓，不阻塞。
- [ ] 實作 SA_game：獨立設定 class.iottalk.tw、Dummy_Device、Dummy_Control、獨立名稱 York_Sausage_Game 和 uuid；IDF_list 為空。Dummy_Control 只驗證與發送；on_register 顯示實際裝置名及接線提示，不匯入 SA 或 DAI。
- [ ] 加入 loopback ephemeral port 往返、垃圾包忽略、遊戲未開仍可發送、連接埠衝突、過量輸入有限工作量測試。執行 Task 2 與 Task 1 測試確認通過。
- [ ] 僅提交本任務新增檔案（若可寫 git）。

### Task 3: 準備、校正與單次揮動

**Files:** Modify 新增的 `game_core.py`, `tests/test_game_core.py`.

**Interfaces:** `GestureController(threshold: float = 2.0, full_strength: float = 20.0)`；`prepare(now: float) -> None`；`feed(axes: tuple, now: float) -> None`；`update(now: float) -> float | None` 回傳一次 0..1 力道；`reset() -> None`；`state`、`baseline`、`strength`、`message` 供 UI 顯示。

- [ ] 寫測試：一秒且至少五筆才完成校正；靜止基準取中位數；波動過大回到待機。校正範圍容許值集中為具名設定，預設合成強度全距不超過 2.0。
- [ ] 執行核心測試，確認新增測試因尚無 GestureController 失敗。
- [ ] 實作 idle/calibrating/ready/capturing/consumed 狀態；超門檻後收集 0.25 秒峰值並只交付一次；動態強度扣除基準，力道映射為峰值／full_strength 並限制 0..1。
- [ ] 加入靜止不投、峰值只投一次、超過一秒斷訊取消、ready 十秒逾時、重設清除峰值、拒絕早於 prepare 時間的樣本測試；執行全部 unittest 確認通過。
- [ ] 僅提交本任務差異（若可寫 git）。

### Task 4: Pygame 畫面與鍵盤／手機遊玩

**Files:** Create `game.py`, `requirements-game.txt`, `tests/test_game_smoke.py`.

**Interfaces:** `main(argv: list[str] | None = None) -> int`；命令列支援 --port、--threshold、--full-strength、--english、--frames（有限幀 smoke test）。使用 Task 1–3 的介面，Pygame 匯入只發生於遊戲入口。

- [ ] 新增 pygame>=2.6,<3 依賴檔；先檢查 .venv 是否已有套件，再選適用直譯器，不任意改動現有依賴。
- [ ] 寫子程序 smoke test：SDL_VIDEODRIVER=dummy、SDL_AUDIODRIVER=dummy，啟動 --english --frames 5，應於十秒內正常結束；缺 pygame 時測試明確 skip，交付前必須另以可用環境實測。
- [ ] 執行 smoke test，確認入口不存在而失敗；再實作主迴圈、可關閉視窗、Esc 退出及清理 socket/pygame。
- [ ] 實作共享透視投影與繪製：天空／地面、桌腿與梯形桌面、近景鍋子、橫放香腸、陰影；以世界深度決定香腸與桌子的遮擋，成功後香腸停在桌面。
- [ ] 加入準備按鈕／R、手機狀態與數值、空白鍵按住蓄力與放開投擲；鍵盤和手機只能在可投擲狀態發射，飛行期間忽略新輸入。結果顯示成功／不足／過頭／桌邊，按 R 回鍋準備。自動尋找中文字型，失敗時整組 UI 用英文。
- [ ] 執行全部 unittest 與有限幀測試；以模擬鍵盤事件驗證一次投擲與重玩，並以本機感測封包驗證畫面迴圈能接收；存臨時截圖於 /tmp 並檢查場景布局。
- [ ] 僅提交本任務新增檔案（若可寫 git）。

### Task 5: 操作文件與交付驗證

**Files:** Create `GAME_README.md`.

**Interfaces:** 文件提供與實際 CLI、SA_game 設定完全一致的安裝／啟動／調參命令。

- [ ] 撰寫繁體中文說明：安裝 requirements-game.txt；python game.py 離線蓄力；另一終端 python DAI.py SA_game；IoTtalk 手機來源接至新裝置 Dummy_Control；準備時手機靜止；--threshold/--full-strength 與 SAUSAGE_PORT 的用法及替代連接埠。
- [ ] 說明不必同時開原 SA，原程式仍可照原方法啟動；資料未收到、缺 pygame、無中文字型、埠占用的對應處理。明列實機力道仍需現場調整。
- [ ] 執行 `python -m unittest discover -s tests -v`、`python -m py_compile game.py game_core.py game_input.py SA_game.py` 及 dummy 有限幀啟動，記錄真正執行的直譯器與結果。
- [ ] 對照開始時的 SA.py 差異，確認既有檔案未被修改；只檢查新增檔案的 whitespace，避免把原有 SA.py 尾端空白誤認本次問題。
- [ ] 審閱完整變更與設計覆蓋；若發現缺陷先修正再執行相關驗證。提交新增操作文件（若可寫 git），回報啟動方法、測試結果和未驗證的手機實機部分。

## 自我審閱

設計中的隔離、資料格式、單次揮動、斷線、固定仰角、整根落桌、透視、鍵盤、字型與驗證均有對應任務。採標準函式庫測試，不新增測試框架。所有後續介面以各任務 Interfaces 為準；若實作需調整，必須同步消費端與測試。

## 執行方式待確認

建議由目前助理在同一工作階段依序實作；五個任務共享核心介面，單人順序執行可減少交接成本。使用者亦可選擇子代理實作與獨立審查。計畫審閱及執行方式確認前不開始產品程式碼。

## 執行結果（2026-10-20）

五項任務已實作並驗證。使用 `.venv/bin/python`；完整 unittest 16/16 通過，涵蓋鍵盤投擲、重玩、本機手機封包整合、超量封包與無視窗啟動。獨立審查提出的近桌短拋提示與峰值時間窗問題，均已用先失敗後通過的回歸測試修正；也修正香腸繪圖尺寸及投影起點。

在原工作目錄新增檔案交付，未建立分支或提交；原有六個檔案 SHA256 均維持不變。Pygame 安裝於現有 .venv。手機實機與課堂 IoTtalk 接線尚未驗證，請依 GAME_README.md 操作。
