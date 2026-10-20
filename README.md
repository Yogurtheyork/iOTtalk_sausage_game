# IoTtalk 香腸體感投擲遊戲

使用手機三軸加速度控制力道，把眼前鍋子裡的香腸丟到遠方桌上。以 Pygame 呈現 2.5D 透視，也支援鍵盤離線試玩。

- [遊戲示範影片（YouTube）](https://youtu.be/sKtNctkk2Lg)
- [完整安裝、手機連線與操作說明](GAME_README.md)

## 快速開始

使用 Python 3 建立並啟用虛擬環境後執行：

```bash
python -m pip install -r requirements-game.txt requests 'paho-mqtt~=2.1.0'
python game.py
```

按住空白鍵蓄力、放開投擲，R 準備／重玩，Esc 離開。

手機模式請另開終端執行 `python DAI.py SA_game`，在 IoTtalk 將手機三軸資料連到 `York_Sausage_Game` 的 `Dummy_Control`。遊戲顯示手機已連線後按 R，保持靜止直到出現揮動提示，再向前揮動。

## 原始 Dummy_Device 使用說明

#### Before using this example, please install the python modules 'requests' and 'paho-mqtt (~=2.1.0)' correctly.


  `pip install requests paho-mqtt~=2.1.0`
    

Modify your user-defined code in "SA.py", and execute "DAI.py" to run the DA by `python DAI.py`

If you change the file name of SA.py to i.e., "new_SA.py", you can execute it by `python DAI.py new_SA`.

#### SA's routine jobs can be written in on_register().
https://github.com/IoTtalk/Dummy_Device_IoTtalk_v1_py/blob/7591046a34a7e3f5b6855eec51f67946c051c8ee/SA.py#L23C5-L23C20

#### For long-running applications, Agent.py can assistant you to run and monitor DAI.py. Agent.py has three abilities.
1. Monitor the execution state of DAI.py. If DAI.py is dead or crash, Agent.py executes DAI.py again.
2. Restart DAI.py at a specified time everyday.
3. If the server is out of service for a while (longer than 15 seconds),  once the server is back, Agent.py will restart DAI.py to make sure the connection is good.

To execute DAI.py by Agent.py, you just run Agent.py by `python Agent.py`.
