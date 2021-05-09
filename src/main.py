#V2
from machine import deepsleep
from network import LoRa
from network import WLAN
from pycom import heartbeat
from time import sleep
import config
import socket
import ubinascii


# Deactivate LED
heartbeat(False)

# Conf
APP_EUI         = ubinascii.unhexlify(config.app_eui)
APP_KEY         = ubinascii.unhexlify(config.app_key)
LONG_SLEEP      = 600 #seconds
SHORT_SLEEP     = 600 #seconds
SCAN_TIME       = 5

# Variables
wlan            = WLAN(mode=WLAN.STA, antenna=WLAN.INT_ANT)
lora            = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
s               = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
mac_addresses   = set()

def lora_join():
    '''Function for joining LoRa.'''
    lora.nvram_restore()
    if not lora.has_joined():
        lora.join(activation=LoRa.OTAA, auth=(APP_EUI, APP_KEY), timeout=0)

    # Wait for the module to join the LoRa-network.
    while not lora.has_joined():
        sleep(2.5)

    # Set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 0)

# Function for wifi-sniffer
def wifi_sniffer(pack):
    '''WiFi sniffer.'''
    global mac_addresses
    mac = bytearray(6)
    pk = wlan.wifi_packet()
    control = pk.data[0]
    subtype = (0xF0 & control) >> 4
    if subtype == 4: # 4 = probe request, 5 = probe response
        for i in range (0,6):
            mac[i] = pk.data[10 + i]
        mac_addresses.add(ubinascii.hexlify(mac))

def lora_send(val):
    '''Send packet and set setblocking on and off.'''
    s.setblocking(True)
    s.send(bytes([val]))
    s.setblocking(False)


def d_sleep(s):
    '''Deepsleep for given time. Save LoRa first.'''
    lora.nvram_save()
    deepsleep(s * 1000)

# Sniff for WiFi. Sleep to give it some time.
wlan.callback(trigger=WLAN.EVENT_PKT_MGMT, handler=wifi_sniffer)
wlan.promiscuous(True)
sleep(SCAN_TIME)
wlan.promiscuous(False)
wlan.deinit()

lora_join()
lora_send(len(mac_addresses))

if mac_addresses:
    d_sleep(SHORT_SLEEP)
d_sleep(LONG_SLEEP)