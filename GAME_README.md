# 香腸投擲遊戲

獨立的 Pygame 小遊戲：近景鍋子、遠方桌面，用手機揮動或鍵盤蓄力把香腸送上桌。原有 SA.py、DAI.py 等程式不需修改。

## 安裝與離線試玩

在專案目錄執行（Linux 可使用 python3；現有虛擬環境可直接用以下命令）：

```bash
.venv/bin/python -m pip install -r requirements-game.txt
.venv/bin/python game.py
```

Windows 啟用虛擬環境後改用 `python`。

- 按住空白鍵蓄力，放開投擲。約半條力道可落上桌。
- R 或「準備／再玩一次」按鈕：重玩並準備手機投擲。
- 手機準備：保持靜止一秒，提示可揮動後向前拋；每次準備只投一次。
- 飛行中不接受新的投擲，落地後按 R 再玩。
- Esc 或關閉視窗離開。

香腸必須完整落入桌面範圍才成功；桌上的內框只是視覺參考。第一版固定正前方與仰角，不提供左右瞄準或旋轉。

## 接手機／IoTtalk

保留遊戲視窗，另一個終端執行：

```bash
.venv/bin/python DAI.py SA_game
```

連線程式使用原專案已有的 requests、paho-mqtt；若新建環境尚未安裝，執行 `python -m pip install requests 'paho-mqtt~=2.1.0'`。

在 `https://class.iottalk.tw/` 的專案中加入終端顯示的新遊戲裝置（預設名稱 York_Sausage_Game），把手機三軸加速度來源連到它的 Dummy_Control。回傳支援 `[x,y,z]` 與 `[[x,y,z]]`，若 IoTtalk 中間函式已把三軸轉成單一強度，請改回傳送三軸。來源裝置和手機權限操作沿用課堂既有方式。

不必同時啟動原本的 `DAI.py`；原 SA 的裝置連線不會自動轉給遊戲。每次重啟 SA_game 會用新的裝置 ID，請確認接到本次註冊的裝置。

遊戲顯示手機已連線後按 R，靜止校正再揮動。校正扣除靜止合成強度（例如重力），超過門檻後收集 250 毫秒峰值。若力道不合適，可調整：

```bash
.venv/bin/python game.py --threshold 2 --full-strength 20
```

threshold 是扣除基準後的觸發強度，full-strength 是對應滿力道的強度；前者須大於 0 且小於後者。數值依手機回傳單位而異：容易滿力道就提高 full-strength；不易觸發可降低 threshold。校正最多等待五秒，使用最近兩秒的穩定資料；至少五筆、涵蓋一秒且強度波動不超過 2 才完成。按準備時短暫晃動可在穩定後自動恢復；逾時會分別提示資料不足或手機仍在晃動。校正畫面顯示樣本數與變動值；斷訊超過一秒、等待揮動超過十秒也需重新準備。實際手機揮動仍需現場調參。

## 排除問題

- 缺 pygame：用啟動遊戲的同一個 Python 安裝 requirements-game.txt。
- 沒有中文字型：自動用英文，也可 `--english`；可安裝 Noto Sans CJK 系統字型後再啟動。
- 等待手機：確認接線指向本次註冊裝置、手機有送三軸、兩程序在同一台電腦及連接埠相同。
- 連接埠占用：遊戲用 `--port 8766`，Linux 接收程式用 `SAUSAGE_PORT=8766 .venv/bin/python DAI.py SA_game`；PowerShell 先設 `$env:SAUSAGE_PORT='8766'`。
- 無圖形顯示環境：不能互動遊玩，但可以做以下無視窗測試。

## 驗證

```bash
.venv/bin/python -m unittest discover -s tests -v
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python game.py --english --frames 5 --port 0
```

測試只收發 127.0.0.1，不連課堂服務。`--frames` 是有限幀驗證選項；正常遊玩不加。核心邏輯可在沒有 Pygame 時單獨測：`python -m unittest discover -s tests -p test_game_core.py -v`。
