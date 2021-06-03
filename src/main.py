from machine import deepsleep
from pycom import heartbeat
from time import sleep
import ujson

# Deactivate LED
heartbeat(False)

with open('settings.json') as f:
    SETTINGS = ujson.loads(f.read())

DATA_RATE   = SETTINGS.get("data_rate", 0)
TRANS_POWER = SETTINGS.get("trans_power", 8)
SCAN_TIME   = SETTINGS.get("scan_time", 5000)
SHORT_SLEEP = SETTINGS.get("short_sleep", 300000)
LONG_SLEEP  = SETTINGS.get("long_sleep", 1200000)

def update_settings(b=b'\x28\xcb'):
    """Set the new settings and save to JSON file.
    
    Parameters:
    b (short): The short (2 bytes) to extract setting parameters from.
    """
    global SETTINGS, DATA_RATE, TRANS_POWER, SCAN_TIME, SHORT_SLEEP, LONG_SLEEP
    data_rate_values   = [0, 1, 2, 4, 5]
    trans_power_values = [8, 12, 16, 20, 24, 28, 32, 36, 48, 78]
    scan_time_values   = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    short_sleep_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    long_sleep_values  = [5, 10, 15, 20, 25, 30, 35, 40, 480, 600]
    new_settings = [int(i) for i in str(int.from_bytes(b, 'big'))]
    if len(new_settings) != 5:
        new_settings = [1, 0, 4, 4, 3]
    new_settings[0] = 1 if new_settings[0] < 1 else (5 if new_settings[0] > 5 else new_settings[0])

    SETTINGS["data_rate"]   = DATA_RATE   = data_rate_values[(new_settings[0] - 1)]
    SETTINGS["trans_power"] = TRANS_POWER = trans_power_values[new_settings[1]]
    SETTINGS["scan_time"]   = SCAN_TIME   = scan_time_values[new_settings[2]] * 1000 
    SETTINGS["short_sleep"] = SHORT_SLEEP = short_sleep_values[new_settings[3]] * 60000
    SETTINGS["long_sleep"]  = LONG_SLEEP  = long_sleep_values[new_settings[4]] * 60000
    with open('settings.json', 'w') as f:
        f.write(ujson.dumps(SETTINGS))

update_settings(b'\xd9\x03')
# update_settings()

print("DATA RATE: ", DATA_RATE)
print("TRANS POW: ", TRANS_POWER)
print("SCAN TIME: ", SCAN_TIME)
print("SHORT SLEEP: ", SHORT_SLEEP)
print("LONG SLEEP: ", LONG_SLEEP)

print()
print(SETTINGS)