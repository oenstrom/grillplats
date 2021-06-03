



from network import WLAN
from time import sleep
from machine import deepsleep
import ubinascii

TRANSMISSION_POWER = 8 #8-78, Defines wifi range. Transmission power divided by 4 equals decibel milliwatts.
wlan            = WLAN(mode=WLAN.STA, antenna=WLAN.INT_ANT, max_tx_pwr=TRANSMISSION_POWER)
mac_addresses   = set()


# Function for wifi-sniffer
def wifi_sniffer(pack):
    '''WiFi sniffer.'''
    global mac_addresses
    #global mac
    mac = bytearray(6)
    pk = wlan.wifi_packet()
    control = pk.data[0]
    subtype = (0xF0 & control) >> 4
    if subtype == 4: # 4 = probe request, 5 = probe response
        for i in range (0,6):
            mac[i] = pk.data[10 + i]
        mac_addresses.add(ubinascii.hexlify(mac))
        

# Sniff for WiFi. Sleep to give it some time.
wlan.callback(trigger=WLAN.EVENT_PKT_MGMT, handler=wifi_sniffer)
wlan.promiscuous(True)

sleep(10)
print(len(mac_addresses))
deepsleep(10)