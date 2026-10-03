# Skopíruj ako config.py na Pico a uprav.

WIFI_SSID = "moja-siet"
WIFI_PASSWORD = "heslo"

# --- MQTT ---
MQTT_HOST = "192.168.1.10"
MQTT_PORT = 1883
MQTT_USER = None            # alebo "user"
MQTT_PASSWORD = None
MQTT_CLIENT_ID = "pico-clock"

TOPIC_TEMP = b"hodiny/teplota"        # prichádza: vonkajšia/izbová teplota (číslo, napr. 21.5)
TOPIC_NUMBER = b"hodiny/cislo"        # prichádza: číslo vyvolávacieho systému (voliteľné)
TOPIC_STATE = b"hodiny/stav"          # odchádza: JSON s vlastnými teplotami a svetlom
TEMP_MAX_AGE_S = 600                  # po tejto dobe bez správy sa MQTT teplota nepoužije
PUBLISH_EVERY_S = 60

# --- Zobrazenie ---
TZ_STD_OFFSET_H = 1                   # Bratislava: UTC+1 (letný čas +1 sa pridá automaticky)
T_TIME_S = 8                          # ako dlho sa ukazuje čas
T_TEMP_S = 3                          # ako dlho teplota
T_NUMBER_S = 5                        # ako dlho číslo (NUMBER_MODE = "alternate")
NUMBER_MODE = "alternate"             # "alternate" = strieda s hodinami, "always" = len číslo
BEEP_ON_NUMBER = True                 # pípnutie pri zmene čísla
TEMP_FALLBACK = "ds3231"              # ak nie je MQTT teplota: "ds3231" | "pico" | None

# --- Svetlo ---
LIGHT_DARK = 2000                     # ADC (0..65535) pri tme   <- vykalibruj
LIGHT_BRIGHT = 40000                  # ADC pri plnom svetle     <- vykalibruj
LIGHT_INVERT = False                  # True ak má fotosenzor opačný smer
BRIGHT_MIN = 1
BRIGHT_MAX = 15

# --- PINY: !!! NEOVERENÉ, skontroluj podľa schémy / dema Waveshare Pico-Clock-Green !!!
PIN_SDI = 18
PIN_CLK = 19
PIN_LE = 20
PIN_OE = 21
PIN_ROW_ADDR = (16, 17, 22)           # A0, A1, A2 dekodéra riadkov
MIRROR_X = False
FLIP_Y = False

PIN_I2C_SDA = 6
PIN_I2C_SCL = 7
I2C_ID = 1
PIN_LIGHT_ADC = 26
PIN_BUZZER = 14
