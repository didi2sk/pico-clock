# pico-clock

MicroPython firmvér pre **Waveshare Pico-Clock-Green** s **Raspberry Pi Pico W**.

- hodiny z DS3231, synchronizácia cez NTP (Bratislava, letný čas automaticky)
- automatický jas podľa fotosenzora
- teplota: z MQTT (`hodiny/teplota`), inak z DS3231 alebo teplomera Pico
- voliteľné číslo pre vyvolávací systém (`hodiny/cislo`), pri zmene pípne
- každú minútu publikuje stav (teploty, svetlo, RSSI) na `hodiny/stav`

## Inštalácia

1. Na Pico W nahraj MicroPython pre **Pico W** (nie obyčajné Pico).
2. Nainštaluj MQTT knižnicu (cez Thonny alebo REPL):
   ```python
   import network, mip
   w = network.WLAN(network.STA_IF); w.active(True); w.connect("ssid", "heslo")
   mip.install("umqtt.simple")
   ```
3. Skopíruj `config.example.py` ako `config.py` a vyplň WiFi/MQTT.
4. **Skontroluj piny v `config.py`** podľa wiki/dema Waveshare. Sú neoverené.
5. Nahraj na Pico: `main.py`, `display.py`, `canvas.py`, `ds3231.py`, `config.py`.

## MQTT

| Topic | Smer | Obsah |
|---|---|---|
| `hodiny/teplota` | → hodiny | číslo, napr. `21.5` (po 10 min bez správy sa nepoužije) |
| `hodiny/cislo` | → hodiny | číslo (1..9999); prázdne alebo `0` ho skryje |
| `hodiny/stav` | hodiny → | JSON `{ds3231_temp, pico_temp, light, number, rssi}` |

Test: `mosquitto_pub -h BROKER -t hodiny/cislo -m 42`

`NUMBER_MODE = "always"` v configu zobrazuje číslo trvalo, `"alternate"` ho strieda s hodinami.

## Stav overenia

Rozloženie displeja (`canvas.py`) je otestované na PC. **Ovládač displeja
(`display.py`) a piny neboli skúšané na hardvéri.** Ak je obraz zrkadlený alebo
prevrátený, prepni `MIRROR_X` / `FLIP_Y`. Ak nesvieti nič, skontroluj piny.
Kalibruj `LIGHT_DARK` / `LIGHT_BRIGHT` podľa hodnôt zo `hodiny/stav` (`light`).
