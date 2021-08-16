from machine import deepsleep
from network import LoRa
from network import WLAN
from time import sleep_ms
import config
import socket
import ubinascii
import ujson

with open('settings.json') as f:
    SETTINGS = ujson.loads(f.read())

DATA_RATE   = SETTINGS.get("data_rate", 0)
RSSI        = SETTINGS.get("rssi", -70)
SCAN_TIME   = SETTINGS.get("scan_time", 10000)
SHORT_SLEEP = SETTINGS.get("short_sleep", 3000000)
LONG_SLEEP  = SETTINGS.get("long_sleep", 9000000)

APP_EUI         = ubinascii.unhexlify(config.app_eui)
APP_KEY         = ubinascii.unhexlify(config.app_key)

wlan            = WLAN(mode=WLAN.STA, antenna=WLAN.INT_ANT)
lora            = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
s               = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
mac_addresses   = set()

def update_settings_light(b=b'\x28\xcb'):
    """Set the new settings and save to JSON file.

    Parameters:
    b (short): The short (2 bytes) to extract setting parameters from.
    """
    global SETTINGS, DATA_RATE, RSSI, SCAN_TIME, SHORT_SLEEP, LONG_SLEEP
    data_rate_values   = [0, 1, 2, 4, 5]
    rssi               = [-60, -70, -80, -90]
    scan_time_values   = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    short_sleep_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    long_sleep_values  = [5, 10, 15, 20, 25, 30, 35, 40, 480, 600]
    new_settings = [int(i) for i in str(int.from_bytes(b, 'big'))]
    if len(new_settings) != 5:
        new_settings = [1, 0, 4, 4, 3]
    new_settings[0] = 1 if new_settings[0] < 1 else (5 if new_settings[0] > 5 else new_settings[0])

    SETTINGS["data_rate"]   = DATA_RATE   = data_rate_values[(new_settings[0] - 1)]
    SETTINGS["rssi"]        = RSSI        = rssi[new_settings[1]]
    SETTINGS["scan_time"]   = SCAN_TIME   = scan_time_values[new_settings[2]] * 1000
    SETTINGS["short_sleep"] = SHORT_SLEEP = short_sleep_values[new_settings[3]] * 60000
    SETTINGS["long_sleep"]  = LONG_SLEEP  = long_sleep_values[new_settings[4]] * 60000
    with open('settings.json', 'w') as f:
        f.write(ujson.dumps(SETTINGS))

def lora_join():
    '''Function for joining LoRa.'''
    lora.nvram_restore()
    if not lora.has_joined():
        lora.join(activation=LoRa.OTAA, auth=(APP_EUI, APP_KEY), timeout=0)

    # Wait for the module to join the LoRa-network.
    while not lora.has_joined():
        sleep_ms(2.5)

    # Set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, DATA_RATE)

def wifi_sniffer(pack):
    '''Sniff for WiFi devices. subtype 4 is a probe request, a device looking for wifi.'''
    global mac_addresses
    mac = bytearray(6)
    pk = wlan.wifi_packet()
    control = pk.data[0]
    subtype = (0xF0 & control) >> 4
    if subtype == 4: # 4 = probe request, 5 = probe response
        for i in range (0,6):
            mac[i] = pk.data[10 + i]
        if pk.rssi > RSSI:
            mac_addresses.add(ubinascii.hexlify(mac))

def lora_send(val):
    '''Send packet and set setblocking on and off.'''
    s.setblocking(True)
    s.send(bytes([val]))
    s.setblocking(False)

def d_sleep(ms):
    '''Deepsleep for given time. Save LoRa first.'''
    lora.nvram_save()
    deepsleep(ms)

# Sniff for WiFi. Sleep to give it some time.
wlan.callback(trigger=WLAN.EVENT_PKT_MGMT, handler=wifi_sniffer)
wlan.promiscuous(True)
sleep_ms(SCAN_TIME)
wlan.promiscuous(False)
wlan.deinit()

lora_join()
lora_send(len(mac_addresses))

# TODO: Update settings via downlinks
# downlink = s.recv(64)
# if downlink:
#     print(downlink.decode("utf-8"))

if mac_addresses:
    d_sleep(SHORT_SLEEP)
d_sleep(LONG_SLEEP)
