# pico-clock

MicroPython firmvér pre **Waveshare Pico-Clock-Green** s **Raspberry Pi Pico W**
(hodiny s DS3231, WiFi/NTP, MQTT teplota) s pridaným číslom pre vyvolávací systém.

Základ je pôvodný kód zo zariadenia; zmeny proti nemu sú v druhom commite.

## Piny (overené z pôvodného kódu)

| Funkcia | GPIO |
|---|---|
| Displej: A0 / A1 / A2 | 16 / 18 / 22 |
| Displej: OE / SDI / CLK / LE | 13 / 11 / 10 / 12 |
| Fotosenzor (ADC) | 26 |
| DS3231 SDA / SCL (SoftI2C) | 6 / 7 |
| Buzzer | 14 |
| Tlačidlá 1 / 2 / 3 | 2 / 17 / 15 |

## Nahratie na Pico W (Thonny)

1. **Najprv si zálohuj** pôvodný obsah Pico (View → Files → označ všetko → Download).
2. Skopíruj `config.example.json` ako **`config.json`** a vyplň WiFi (`ssid`, `passphrase`),
   MQTT (`broker`, `prefix`) a časovú zónu `ntpPTZ`
   (Slovensko: `CET-1CEST,M3.5.0,M10.5.0/3`). `config.json` je v `.gitignore`, heslo sa nenahrá na GitHub.
3. Na Pico nahraj všetky `*.py` zo zložky (vrátane nového `watchdog.py`), `config.json` a `lib/umqtt/simple.py`
   (zložku `lib/umqtt` zachovaj). Súbory `test.py` a `testAD.py` netreba.
4. Reštartuj Pico (alebo F5 na `main.py`). Výpisy sú v konzole Thonny.

## MQTT

`prefix` je z `config.json` (napr. `picoW001`).

| Topic | Obsah |
|---|---|
| `<prefix>` | teplota ako číslo, napr. `21.5` (zobrazí sa v 20. a 50. sekunde minúty) |
| `<prefix>/number` | **číslo vyvolávacieho systému** (voliteľné), napr. `42` |
| `<prefix>/beep` | správa `beep` zapípa |
| `clock` | hodiny publikujú stav (teploty) každú minútu |

### Číslo vyvolávacieho systému

- Pošli kladné celé číslo na `<prefix>/number`: číslo sa hneď zobrazí na 8 s, hodiny pípnu
  a potom sa číslo zobrazuje znova vždy v 40. sekunde minúty, kým ho nezmeníš.
- Zrušenie čísla: pošli `0` (alebo akýkoľvek text, ktorý nie je kladné číslo).
- Čísla dlhšie ako 4 cifry sa posúvajú.
- Nepoužívaj `retain` s prázdnou správou na zrušenie, prázdna retained správa sa nedoručí.
  Na zrušenie pošli `0`.
- Ak nič neprišlo, číslo sa nezobrazuje a hodiny fungujú ako predtým.

Test: `mosquitto_pub -h BROKER -t picoW001/number -m 42`

## Stabilita

- `scheduler.py`: chyba v úlohe sa vypíše a úloha beží ďalej (predtým sa ukončila navždy).
- `wifi.py`: hodiny sa spustia aj bez WiFi (čas z DS3231); WiFi sa pripája znova každých 30 s
  na pozadí a po pripojení sa znova nastaví čas z NTP.
- `mqtt.py`: automatické opätovné pripojenie (pokus každých 10 s), unikátne client ID,
  keepalive 120 s, ping každých 60 s.
- `lib/umqtt/simple.py`: timeout 3 s pri pripájaní (nedostupný broker už nezablokuje hodiny).
- `display.py`: vlákno displeja sa po chybe nezastaví.
- `main.py`: `gc.collect()` každú minútu a voliteľný **watchdog**.

**Watchdog** je predvolene vypnutý (`ENABLE_WATCHDOG = False` v `main.py`). Po zapnutí Pico samo
reštartuje, ak sa program zasekne na viac ako 8 s. Zapni ho až keď je všetko odladené:
watchdog sa nedá zastaviť, takže pri ladení v Thonny by Ctrl+C reštartoval Pico po 8 s.

## Zmeny oproti pôvodnému kódu

- `mqtt.py`: odber `<prefix>/number`, spracovanie podľa topicu (predtým sa každá správa čítala ako teplota).
- `clock.py`, `display.py`: zobrazenie čísla.
- `clock.py`: teplota sa nezobrazí, kým neprišla prvá hodnota (predtým `-99.0`).
- Opravy stability (sekcia vyššie): `scheduler.py`, `wifi.py`, `mqtt.py`, `display.py`, `main.py`, `watchdog.py`, `constants.py`, `lib/umqtt/simple.py`.
- Kontrola MQTT správ každých 200 ms namiesto 1 ms, plynulá regulácia jasu.
- WiFi heslá z `config.json`, `test.py` a `testAD.py` sú odstránené.
