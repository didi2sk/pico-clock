import time
import ujson
import machine
import network
from machine import Pin, I2C, ADC, PWM

import config
from display import Display
from ds3231 import DS3231

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None  # nainštaluj: mip.install("umqtt.simple")

# ---------- stav ----------
mqtt_temp = None
mqtt_temp_at = 0
number = None


# ---------- čas / pásmo ----------
def _last_sunday(year, month):
    wd = time.gmtime(time.mktime((year, month, 31, 1, 0, 0, 0, 0)))[6]
    return 31 - ((wd + 1) % 7)


def local_time(utc):
    y = time.gmtime(utc)[0]
    start = time.mktime((y, 3, _last_sunday(y, 3), 1, 0, 0, 0, 0))
    end = time.mktime((y, 10, _last_sunday(y, 10), 1, 0, 0, 0, 0))
    off = config.TZ_STD_OFFSET_H + (1 if start <= utc < end else 0)
    return time.gmtime(utc + off * 3600)


# ---------- hardvér ----------
disp = Display()
i2c = I2C(config.I2C_ID, sda=Pin(config.PIN_I2C_SDA), scl=Pin(config.PIN_I2C_SCL), freq=100_000)
rtc_chip = DS3231(i2c)
light = ADC(config.PIN_LIGHT_ADC)
pico_temp_adc = ADC(4)
buzzer = PWM(Pin(config.PIN_BUZZER))
buzzer.duty_u16(0)


def beep(ms=80):
    buzzer.freq(2000)
    buzzer.duty_u16(20000)
    time.sleep_ms(ms)
    buzzer.duty_u16(0)


def pico_temperature():
    v = pico_temp_adc.read_u16() * 3.3 / 65535
    return 27 - (v - 0.706) / 0.001721


def ds_temperature():
    try:
        return rtc_chip.temperature()
    except OSError:
        return None


def own_temperature():
    if config.TEMP_FALLBACK == "ds3231":
        return ds_temperature()
    if config.TEMP_FALLBACK == "pico":
        return pico_temperature()
    return None


# ---------- sieť ----------
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
mqtt = None


def wifi_connect(timeout=15):
    if wlan.isconnected():
        return True
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    t0 = time.time()
    while not wlan.isconnected() and time.time() - t0 < timeout:
        time.sleep_ms(200)
    return wlan.isconnected()


def sync_ntp():
    import ntptime
    try:
        ntptime.settime()  # nastaví vnútorné RTC na UTC
        t = time.gmtime()
        rtc_chip.set(t[0], t[1], t[2], t[3], t[4], t[5])
        return True
    except Exception as e:
        print("NTP chyba:", e)
        return False


def on_msg(topic, msg):
    global mqtt_temp, mqtt_temp_at, number
    try:
        if topic == config.TOPIC_TEMP:
            mqtt_temp = float(msg)
            mqtt_temp_at = time.time()
        elif topic == config.TOPIC_NUMBER:
            s = msg.decode().strip()
            new = int(s) if s.lstrip("-").isdigit() and int(s) > 0 else None
            if new != number:
                number = new
                if new is not None and config.BEEP_ON_NUMBER:
                    beep()
    except Exception as e:
        print("MQTT správa:", topic, msg, e)


def mqtt_connect():
    global mqtt
    if MQTTClient is None or not wlan.isconnected():
        return False
    try:
        c = MQTTClient(config.MQTT_CLIENT_ID, config.MQTT_HOST, config.MQTT_PORT,
                       config.MQTT_USER, config.MQTT_PASSWORD, keepalive=60)
        c.set_callback(on_msg)
        c.connect()
        c.subscribe(config.TOPIC_TEMP)
        c.subscribe(config.TOPIC_NUMBER)
        mqtt = c
        return True
    except Exception as e:
        print("MQTT pripojenie:", e)
        mqtt = None
        return False


def mqtt_poll():
    global mqtt
    if mqtt is None:
        return
    try:
        mqtt.check_msg()
    except Exception as e:
        print("MQTT spojenie padlo:", e)
        mqtt = None


def mqtt_publish():
    if mqtt is None:
        return
    try:
        mqtt.publish(config.TOPIC_STATE, ujson.dumps({
            "ds3231_temp": ds_temperature(),
            "pico_temp": round(pico_temperature(), 1),
            "light": light.read_u16(),
            "number": number,
            "rssi": wlan.status("rssi") if wlan.isconnected() else None,
        }))
    except Exception as e:
        print("MQTT publish:", e)


# ---------- jas ----------
_level = 0.5


def update_brightness():
    global _level
    raw = light.read_u16()
    x = (raw - config.LIGHT_DARK) / (config.LIGHT_BRIGHT - config.LIGHT_DARK)
    x = min(1.0, max(0.0, x))
    if config.LIGHT_INVERT:
        x = 1.0 - x
    _level += (x - _level) * 0.05  # vyhladenie, aby neblikalo
    disp.brightness = int(config.BRIGHT_MIN + (config.BRIGHT_MAX - config.BRIGHT_MIN) * _level)


# ---------- vykresľovanie ----------
def current_temp():
    if mqtt_temp is not None and time.time() - mqtt_temp_at < config.TEMP_MAX_AGE_S:
        return mqtt_temp
    return own_temperature()


def pages():
    if number is not None and config.NUMBER_MODE == "always":
        return [("number", 1)]
    p = [("time", config.T_TIME_S)]
    if current_temp() is not None:
        p.append(("temp", config.T_TEMP_S))
    if number is not None:
        p.append(("number", config.T_NUMBER_S))
    return p


def render(utc):
    lt = local_time(utc)
    plist = pages()
    pos = utc % sum(d for _, d in plist)
    page = plist[0][0]
    for name, dur in plist:
        if pos < dur:
            page = name
            break
        pos -= dur
    disp.clear()
    if page == "time":
        disp.time(lt[3], lt[4], colon=(time.ticks_ms() // 500) % 2 == 0)
    elif page == "temp":
        disp.text("%dC" % round(current_temp()))
    else:
        disp.text(str(number)[-4:])
    disp.show()


# ---------- štart ----------
def boot():
    disp.start()
    if rtc_chip.present():
        try:
            y, mo, d, h, mi, s = rtc_chip.get()
            machine.RTC().datetime((y, mo, d, 0, h, mi, s, 0))
        except Exception as e:
            print("DS3231:", e)
    if wifi_connect():
        sync_ntp()
        mqtt_connect()


def main():
    boot()
    last_pub = last_net = last_ntp = time.time()
    while True:
        now = time.time()
        update_brightness()
        render(now)
        mqtt_poll()
        if now - last_net > 30:
            last_net = now
            if not wlan.isconnected():
                wifi_connect(5)
            if wlan.isconnected() and mqtt is None:
                mqtt_connect()
        if now - last_pub >= config.PUBLISH_EVERY_S:
            last_pub = now
            mqtt_publish()
        if now - last_ntp > 86400 and wlan.isconnected():
            last_ntp = now
            sync_ntp()
        time.sleep_ms(50)


main()
