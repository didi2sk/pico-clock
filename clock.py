from apps import App
from constants import APP_CLOCK, SCHEDULER_CLOCK_SECOND
from display import Display
from rtc import RTC
from buttons import Buttons
from configuration import Configuration
import helpers
import my_globals
import time

NUMBER_SHOW_MS = 8000  # how long the queue number stays on the display
NUMBER_REPEAT_SECOND = 40  # second of the minute when the number is shown again

class Clock(App):
    def __init__(self, scheduler):
        App.__init__(self, APP_CLOCK)
        self.config = Configuration()
        self.display = Display(scheduler)
        self.rtc = RTC()
        self.enabled = True
        self.buttons = Buttons(scheduler)
        self.hour = 0
        self.minute = 0
        self.second = 0
        self.number_until = 0  # ticks_ms until which the queue number is shown (0 = not shown)
        scheduler.schedule(SCHEDULER_CLOCK_SECOND, 1000, self.secs_callback)

    async def enable(self):
        self.enabled = True
        self.buttons.add_callback(2, self.temp_callback, max=500)
        self.buttons.add_callback(
            2, self.switch_temperature_callback, min=500, max=5000)
        self.buttons.add_callback(3, self.backlight_callback, max=500)
        self.buttons.add_callback(
            3, self.switch_blink_callback, min=500, max=5000)
        await self.update_time()
        await self.show_time()
        #self.display.show_temperature_icon()

    def disable(self):
        self.enabled = False

    async def secs_callback(self):
        if self.enabled:
            await self.update_time()
            if self.should_blink():
                if self.second % 2 == 0:
                    # makes : display
                    self.display.show_char(":", pos=10)
                else:
                    # makes : not display
                    self.display.show_char(" :", pos=10)

    def should_blink(self):
        return self.config.blink_time_colon and not self.display.animating and self.display.showing_time

    async def update_time(self):
        t = self.rtc.get_time()
        self.second = t[5]

        if my_globals.queue_number_new:
            my_globals.queue_number_new = False
            await self.show_number()
            return
        if self.number_until:
            if time.ticks_diff(time.ticks_ms(), self.number_until) < 0:
                return  # number is still being shown
            self.number_until = 0
            self.hour = t[3]
            self.minute = t[4]
            await self.show_time()
            self.display.hide_temperature_icon()
            return
        if t[5] == NUMBER_REPEAT_SECOND and my_globals.queue_number is not None:
            await self.show_number()
            return

        if self.hour != t[3] or self.minute != t[4]:
            self.hour = t[3]
            self.minute = t[4]
            self.show_time_icon()
            self.display.show_day(t[6])
            await self.show_time()
            self.display.hide_temperature_icon()
            
        elif t[5] == 20 and self.config.show_temp and my_globals.mqtt_temp > -90:
            await self.show_mqtt_temperature()
            self.display.show_temperature_icon()
            
        elif t[5] == 30 and self.config.show_temp:
            await self.show_time()
            self.display.hide_temperature_icon()
        
        elif t[5] == 50 and self.config.show_temp and my_globals.mqtt_temp > -90:
            await self.show_mqtt_temperature()
            self.display.show_temperature_icon()

            

    async def show_number(self):
        self.number_until = time.ticks_add(time.ticks_ms(), NUMBER_SHOW_MS) or 1
        await self.display.show_queue_number(my_globals.queue_number)

    async def show_time(self):
        hour = self.hour
        if self.config.clock_type == "12":
            hour = helpers.convert_twenty_four_to_twelve_hour(hour)
        await self.display.show_time("%02d:%02d" % (hour, self.minute))

    def show_time_icon(self):
        if self.config.clock_type == "12":
            if self.hour >= 12:
                self.display.show_icon("PM")
                self.display.hide_icon("AM")
            else:
                self.display.show_icon("AM")
                self.display.hide_icon("PM")

    async def show_temperature(self):
        temp = self.rtc.get_temperature()
        await self.display.show_temperature(temp)
        
    async def show_mqtt_temperature(self):
        temp = my_globals.mqtt_temp 
        print(f"Displaying mqtt_temp: {temp}")
        await self.display.show_mqtt_temperature(temp)    

    async def temp_callback(self):
        await self.show_temperature()

    async def switch_temperature_callback(self):
        self.config.switch_temp_value()
        self.display.show_temperature_icon()

    async def backlight_callback(self):
        self.display.switch_backlight()

    async def switch_blink_callback(self):
        self.config.switch_blink_time_colon_value()
