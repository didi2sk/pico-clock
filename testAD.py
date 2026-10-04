import network
import time
from umqtt.simple import MQTTClient
import machine

# Wi-Fi configuration
SSID = 'YOUR_WIFI_SSID'
PASSWORD = 'YOUR_WIFI_PASSWORD'

# MQTT configuration
BROKER = '192.168.1.10'
CLIENT_ID = 'pico_client_' + str(machine.unique_id())  # Ensure unique client ID
TOPIC = b'pico'

# Function to connect to Wi-Fi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        print('Connecting to Wi-Fi...')
        time.sleep(1)
    print('Connected to Wi-Fi:', wlan.ifconfig())

# Function to connect to MQTT broker
def connect_mqtt():
    try:
        client = MQTTClient(CLIENT_ID, BROKER)
        client.connect()
        print('Connected to MQTT broker')
        return client
    except Exception as e:
        print('Failed to connect to MQTT broker:', e)
        return None

# Function to publish a message
def publish_message(client, topic, message):
    if client:
        client.publish(topic, message)
        print(f'Message published: {message} to topic: {topic}')
    else:
        print('No client to publish message')

# Main function
def main():
    connect_wifi(SSID, PASSWORD)
    client = connect_mqtt()
    
    # Example: publish a message
    if client:
        publish_message(client, TOPIC, b'Hello from Raspberry Pi Pico')
        client.disconnect()
    else:
        print('Could not publish message due to MQTT connection issues')

# Uncomment the following line to run the main function
# main()
