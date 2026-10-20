"""Run with: python DAI.py SA_game. Does not modify or import SA.py."""
from uuid import uuid4
from game_input import configured_port, parse_axes, send_axes

ServerURL = 'https://class.iottalk.tw/'
MQTT_broker = None
MQTT_port = 1883
MQTT_encryption = False
MQTT_User = 'ID'
MQTT_PW = 'PW'
device_model = 'Dummy_Device'
IDF_list = []
ODF_list = ['Dummy_Control']
device_id = uuid4().hex
device_name = 'York_Sausage_Game'
exec_interval = .05
GAME_PORT = configured_port()


def Dummy_Control(data):
    axes = parse_axes(data)
    if axes is not None:
        send_axes(axes, GAME_PORT)


def on_register(result):
    print(f'Game device: {result["d_name"]}')
    print(f'Connect phone acceleration to Dummy_Control; local game port: {GAME_PORT}')
