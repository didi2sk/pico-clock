import time
import json
from configuration import Configuration
from constants import SCHEDULER_MQTT_CHECK, SCHEDULER_MQTT_HEARTBEAT, SCHEDULER_MQTT_STATE
from scheduler import Scheduler
from util import singleton
import my_globals
from speaker import Speaker

@singleton
class MQTT:
    class MQTT_Callback:
        def __init__(self, topic: str, callback: function) -> None:
            self.topic = topic
            self.callback = callback
            self.mqtt_base_topic = "clock"
         

    class MQTT_State:
        def __init__(self, name: str, callback: function) -> None:
            self.name = name
            self.callback = callback

    def __init__(self, scheduler: Scheduler):
        self.scheduler = scheduler
        self.lastping = 0
        self.registered_callbacks = []
        self.state_callbacks = []
        self.configuration = Configuration().mqtt_config
        self.speaker = Speaker(scheduler)
        if self.configuration.enabled:
            from umqtt.simple import MQTTClient
            self.client = MQTTClient(self.configuration.prefix, self.configuration.broker, user=None,
                                     password=None, keepalive=300, ssl=False, ssl_params={})
            self.connect()
            scheduler.schedule(SCHEDULER_MQTT_HEARTBEAT, 250,
                               self.scheduler_heartbeat_callback)
            scheduler.schedule(SCHEDULER_MQTT_CHECK, 200,
                               self.scheduler_mqtt_callback)
            scheduler.schedule(SCHEDULER_MQTT_STATE, 60000,
                               self.scheduler_mqtt_state)

    def connect(self):
        try:
            print("Connecting to MQTT")
            topic = self.configuration.prefix + ""
            print("Subscribed to " + topic)
            self.client.connect()
            print("Connected to MQTT Broker")
            self.heartbeat(True)
            self.client.set_callback(self.mqtt_callback)            
            self.client.subscribe(topic)
            self.client.subscribe(topic + "/beep")
            self.client.subscribe(topic + "/backlight")
            self.client.subscribe(topic + "/alarm")
            self.client.subscribe(topic + "/number")
            print("Subscribed to " + topic)
        except Exception as e:
            print(f"Error during MQTT connect: {e}")
            
#     def connect(self):
#         try:
#             self.client.connect()
#             print("Connected to MQTT Broker")
#             topic = self.configuration.prefix + "#"
#             self.client.set_callback(self.on_message)
#             for callback in self.registered_callbacks:
#                 self.client.subscribe(callback.topic)
#                 print(f"Subscribed to {callback.topic}")
#             self.client.subscribe(self.configuration.topic)
#             print(f"Subscribed to {self.configuration.topic}")
#             self.scheduler.add(SCHEDULER_MQTT_CHECK, 10, self.check, cycle=True)
#             self.scheduler.add(SCHEDULER_MQTT_HEARTBEAT, self.configuration.heartbeat, self.ping, cycle=True)
#             self.scheduler.add(SCHEDULER_MQTT_STATE, self.configuration.state, self.update_state, cycle=True)
#             self.scheduler.run()
#         except Exception as e:
#             print(f"Error during MQTT connect: {e}")
            
#     def on_message(self, topic, msg):
#         print(f"Received message on topic {topic}: {msg}")
#         for callback in self.registered_callbacks:
#             if callback.topic == topic:
#                 callback.callback(msg)        

    def heartbeat(self, first=False):
        if first:
            self.client.ping()
            self.lastping = time.ticks_ms()
        if time.ticks_diff(time.ticks_ms(), self.lastping) >= 300000:
            self.client.ping()
            self.lastping = time.ticks_ms()
        return

    async def scheduler_heartbeat_callback(self):
        self.heartbeat(False)

    async def scheduler_mqtt_callback(self):
        try:
            self.client.check_msg()
        except Exception as e:
            print(f"Error during MQTT connect: {e}")

    async def scheduler_mqtt_state(self):
        self.send_state()

    def mqtt_callback(self, topic, msg):
        t = topic.decode()
        print(t)

        msg_str = msg.decode().strip()
        if t.endswith("/number"):
            self.set_queue_number(msg_str)
        elif msg_str == "beep":
            self.speaker.beep(500)
        else:
            try:
                my_globals.mqtt_temp = float(msg_str)  # Ensure the value is correctly converted to a float
            except ValueError:
                print(f"Received invalid temperature value: {msg_str}")

    def set_queue_number(self, text):
        # empty text, "0" or anything that is not a positive integer clears the number
        number = int(text) if text.isdigit() and int(text) > 0 else None
        if number != my_globals.queue_number:
            my_globals.queue_number = number
            if number is not None:
                my_globals.queue_number_new = True
                self.speaker.beep(300)

    def send_event(self, topic: str, msg: str):
        #topic = mqtt_prefix + topic
        print(topic)
        self.client.publish(topic, msg)


    def send_state(self):
        self.client.publish("clock", self.build_state())
        

    def build_state(self):
        state = dict()
        for s in self.state_callbacks:
            item_name = s.name
            item_state = s.callback()
            state[item_name] = item_state
        return json.dumps(state)

    def register_topic_callback(self, topic, callback):
        self.registered_callbacks.append(self.MQTT_Callback(topic, callback))

    def register_state_callback(self, name, callback):
        self.state_callbacks.append(self.MQTT_State(name, callback))
