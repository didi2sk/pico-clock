from utime import sleep
from display import Display
from pico_temperature import PicoTemperature
from scheduler import Scheduler
from clock import Clock
from apps import Apps, App
from pomodoro import Pomodoro
from temperature import Temperature
from time_set import TimeSet
from wifi import WLAN
from mqtt import MQTT
from configuration import Configuration
import machine
import uasyncio
import _thread
import my_globals
#import network
#import picoweb

machine.freq(250_000_000)  # type: ignore

APP_CLASSES = [
    Clock,
    Pomodoro,
    TimeSet
]

print("-" * 10)
print("PICO CLOCK")
print("-" * 10)

print("Configuring...")
config = Configuration()

scheduler = Scheduler()
wlan = WLAN(scheduler)
mqtt = MQTT(scheduler)
display = Display(scheduler)
pico_temperature = PicoTemperature(scheduler, mqtt)
temperature = Temperature(mqtt)
apps = Apps(scheduler)

# register apps
for App in APP_CLASSES:
    apps.add(App(scheduler))

# HTTP Server Configuration
#app = picoweb.WebApp(__name__)

# @app.route('/')
# def index(req, resp):
#     yield from picoweb.start_response(resp)
#     yield from resp.awrite("Pico Clock is running!")
# 
# @app.route('/temperature')
# def get_temperature(req, resp):
#     temp = pico_temperature.read()  # Assuming read() is a method to get the current temperature
#     yield from picoweb.start_response(resp)
#     yield from resp.awrite(f"Current temperature: {temp}°C")

async def start():
    print("STARTING...")

    # start async scheduler
    scheduler.start()

    # create thread for UI updates.
    _thread.start_new_thread(display.enable_leds, ())

    # start apps
    await apps.start()
    
    # Start HTTP server
    print("Starting HTTP server...")
    #import asyncio
   # asyncio.create_task(app.run(host='0.0.0.0', port=80)) 

uasyncio.run(start())
loop = uasyncio.get_event_loop()
loop.run_forever()
