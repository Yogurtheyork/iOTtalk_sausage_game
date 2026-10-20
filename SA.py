from uuid import uuid4
import random 
import math 
import time

ServerURL = 'https://class.iottalk.tw/' #For example: 'https://DomainName'
MQTT_broker = None # MQTT Broker address, for example: 'DomainName' or None = no MQTT support
MQTT_port = 1883
MQTT_encryption = False
MQTT_User = 'ID'
MQTT_PW = 'PW'

device_model = 'Dummy_Device'
IDF_list = ['Dummy_Sensor']
ODF_list = ['Dummy_Control']
device_id = uuid4().hex #if None, device_id = MAC address
device_name = 'York_Dummy_Test'
exec_interval = 0.1  # IDF/ODF interval

def Dummy_Sensor():
    #After obtaining the IDF value (e.g., a sensor value), simply use return value to send the value back to the IoTtalk platform.
    value = random.randint(0, 100), random.randint(0, 100)  #Multidimensional data can be returned as "," comma-separated values.
    return value


last_recieved = None

def Dummy_Control(data:list):
    #The ODF value from IoTtalk is automatically assigned to the "data" variable.
    #The "data" variable is then used in the required actuator function.
    #The type of "data" variable is LIST.
    global last_recieved
    value = data[0]
    x, y, z = value  #Assuming the data is a list of three values representing x, y, z coordinates.
    strength = math.sqrt(x**2 + y**2 + z**2)

    now = time.monotonic()

    if last_recieved is None:
        print(f"動作強度:{strength:.2f}")
    else:
        interval = now - last_recieved
        print(f"動作強度:{strength:.2f}, 時間間隔:{interval:.2f}秒")

    last_recieved = now

def on_register(r):
    print(f'Device name: {r["d_name"]}')    
    '''
    #You can write some SA routine code here, for example: 
    import time, DAI
    while True:
        DAI.push('Dummy_Sensor', [100, 200])  
        time.sleep(exec_interval)    
    '''


