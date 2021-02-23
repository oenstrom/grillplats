from machine import Pin
from machine import deepsleep
from machine import pin_sleep_wakeup
from machine import WAKEUP_ANY_HIGH
from machine import WAKEUP_ALL_LOW
from network import LoRa
from network import WLAN
from socket import socket
from socket import AF_LORA
from socket import SOCK_RAW
from socket import SOL_LORA
from socket import SO_DR
from time import sleep
import ubinascii
import config
import pycom
#import struct


# Deactivate LED
pycom.heartbeat(False)


# Variables
pin_str         = 'P18'
pir             = Pin(pin_str,mode=Pin.IN, pull=None)
device_found    = False
wlan            = WLAN(mode=WLAN.STA, antenna=WLAN.EXT_ANT)
lora            = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

#OTAA
app_eui         = ubinascii.unhexlify(config.app_eui)
app_key         = ubinascii.unhexlify(config.app_key)

#ABP
# dev_addr = struct.unpack(">l", ubinascii.unhexlify(config.dev))[0]
# nwk_swkey = ubinascii.unhexlify(config.nwk)
# app_swkey = ubinascii.unhexlify(config.app)

s               = socket(AF_LORA, SOCK_RAW)
# True if motion's been detected. False if not.
high            = True if pir.value() == 1 else False
lora.nvram_restore()

# Function for wifi-sniffer
def pack_cb(pack):
    global device_found
    pk = wlan.wifi_packet()
    control = pk.data[0]
    subtype = (0xF0 & control) >> 4
    #print("Control:{}, subtype:{}, type:{}".format(control, subtype, type))
    if subtype == 4:
        device_found = True


# If no motion is detected.
if not high:
    print('No motion')
    s.send(bytes([0x00]))
    pin_sleep_wakeup((pir,), mode=WAKEUP_ANY_HIGH)
    lora.nvram_save()
    deepsleep(86400000)

# Wifi-sniffer
wlan.callback(trigger=WLAN.EVENT_PKT_MGMT, handler=pack_cb)
wlan.promiscuous(True)


if not lora.has_joined():
    # Join LoRa
    lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

while not lora.has_joined():
    sleep(2.5)
    print('Not yet joined...')

print('Joined')
for _ in range(10):
    sleep(2)
    if device_found:
        break

# Set the LoRaWAN data rate and setblocking
s.setsockopt(SOL_LORA, SO_DR, 0)
s.setblocking(True)

# If wifi units are nearby
if device_found:
    print('Motion')
    s.send(bytes([0x01]))
# If motion is detected and no wifi units are nearby.
else:
    print('No Wifi')
    s.send(bytes([0x02]))
# Go to sleep for 15 minutes. Interrupts if no motion's detected.
pin_sleep_wakeup((pir,), mode=WAKEUP_ALL_LOW)
lora.nvram_save()
deepsleep(86400000)
