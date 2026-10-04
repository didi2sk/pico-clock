import time
import uasyncio
from configuration import Configuration
from constants import SCHEDULER_WIFI_CHECK
from util import singleton

import network
from rtc import RTC
import ntptime
import localPTZtime

CONNECT_WAIT_S = 20
CHECK_EVERY_MS = 30000


@singleton
class WLAN:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.configuration = Configuration().wifi_config
        self.wlan = network.WLAN(network.STA_IF)
        self.rtc = RTC()
        if self.configuration.enabled:
            try:
                self.connect_to_wifi()
            except Exception as e:
                # the clock must work without WiFi (time comes from the DS3231)
                print("WiFi:", e)
            scheduler.schedule(SCHEDULER_WIFI_CHECK, CHECK_EVERY_MS,
                               self.check_callback, initial_delay=CHECK_EVERY_MS)

    def _begin(self):
        print("Connecting to WiFi")
        #network.hostname(self.configuration.hostname)
        self.wlan.active(True)
        self.wlan.config(pm=0xa11140)  # type: ignore - Disable powersave mode
        self.wlan.connect(self.configuration.ssid,
                          self.configuration.passphrase)

    def _finished(self):
        status = self.wlan.status()
        return status < 0 or status >= 3

    def connect_to_wifi(self):
        self._begin()

        # Wait for connect or fail
        for _ in range(CONNECT_WAIT_S):
            if self._finished():
                break
            print('Waiting for connection...')
            time.sleep(1)

        if not self.wlan.isconnected():
            raise RuntimeError('WiFi connection failed')
        print('IP = ' + self.wlan.ifconfig()[0])
        self.sync_time()

    async def check_callback(self):
        """Reconnect after a WiFi outage, without blocking the other tasks."""
        if self.wlan.isconnected():
            return
        print("WiFi is down, reconnecting")
        self.wlan.disconnect()
        self._begin()
        for _ in range(CONNECT_WAIT_S):
            if self._finished():
                break
            await uasyncio.sleep(1)
        if self.wlan.isconnected():
            print('IP = ' + self.wlan.ifconfig()[0])
            self.sync_time()

    def sync_time(self):
        if not self.configuration.ntp_enabled:
            return
        try:
            ntptime.settime()
            local_time = localPTZtime.tztime(time.time(), self.configuration.ntp_ptz)
            self.rtc.save_time(local_time[:8])
        except Exception as e:
            print("NTP:", e)
