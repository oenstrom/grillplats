from machine import deepsleep
from network import LoRa
from network import WLAN
import socket
import time
import ubinascii
import config
import pycom


# Deactivate LED
pycom.heartbeat(False)

# Constants
APP_EUI         = ubinascii.unhexlify(config.app_eui)
APP_KEY         = ubinascii.unhexlify(config.app_key)
LONG_SLEEP      = 15 #900
SHORT_SLEEP     = 5 #300
SCAN_TIME       = 60

# Variables
wlan            = WLAN(mode=WLAN.STA, antenna=WLAN.EXT_ANT)
lora            = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
s               = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
device_found    = False
mac_addresses   = set()
counter         = 0

def lora_join():
    '''Function for joining LoRa.'''
    lora.nvram_restore()
    if lora.has_joined() == False:
        lora.join(activation=LoRa.OTAA, auth=(APP_EUI, APP_KEY), timeout=0)

    # Wait for the module to join the LoRa-network.
    while not lora.has_joined():
        print('Not yet joined...')
        time.sleep(2.5)
    print('Joined')

    # Set the LoRaWAN data rate and setblocking
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 0)
    s.setblocking(True)

# Function for wifi-sniffer
def pack_cb(pack):
    '''WiFi sniffer.'''
    global device_found, mac_addresses
    mac = bytearray(6)
    pk = wlan.wifi_packet()
    control = pk.data[0]
    subtype = (0xF0 & control) >> 4
    if subtype == 4:
        for i in range (0,6):
            mac[i] = pk.data[10 + i]
        mac_addresses.add(ubinascii.hexlify(mac))
        device_found = True

def lora_send(val):
    '''Send packet.'''
    s.send(bytes([val]))

def sleep(s):
    '''Deepsleep for given time. Save LoRa first.'''
    lora.nvram_save()
    deepsleep(s*1000)

# Sniff for WiFi. Sleep to give it some time.
wlan.callback(trigger=WLAN.EVENT_PKT_MGMT, handler=pack_cb)
wlan.promiscuous(True)
time.sleep(SCAN_TIME)


if not device_found:
    lora_join()
    lora_send(0)
    sleep(LONG_SLEEP)

for mac in mac_addresses:
    try:
        pycom.nvs_get(mac)
        counter += 1
    except ValueError:
        pass

pycom.nvs_erase_all()

for mac in mac_addresses:
    pycom.nvs_set(mac, 1)

lora_join()
lora_send(counter)
sleep(SHORT_SLEEP)
