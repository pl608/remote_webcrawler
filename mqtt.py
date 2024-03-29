import socket
import random
from paho.mqtt import client as mqtt_client
from hashlib import sha512, md5
from time import time
broker_ = '9fcd632e24e3417ba95802e5a6165679.s1.eu.hivemq.cloud'
port_ = 8883
def on_message_(client, userdata, msg):
    print(userdata)
    print(msg.payload.decode())

class Network:
    def __init__(self, broker=broker_, port=port_, topic=sha512(str(int(time()/60/60/24)).encode('utf-8')).hexdigest(), on_message_=on_message_, usr='webcrawler', pwd='Crawler1234') -> None:
        print(__file__)
        self.device_name = md5(f"{socket.gethostname()}{str(random.randint(1, 100))}".encode('utf-8')).hexdigest()[:4]
        self.broker = broker
        self.port = port
        self.topic = topic
        self.on_message = lambda cli, usr, msg: on_message_(self, cli, usr, msg)
        self.connect(usr, pwd)
        self.connections = 0
        #self.subscribe()
    def connect(self, usr, pwd):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.connections += 1
                if self.connections >= 2:
                    print('[WIERD ANNOYING ERROR] exiting')
                    exit()
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.device_name)
        client.on_connect = on_connect
        client.tls_set(tls_version=mqtt_client.ssl.PROTOCOL_TLS)
        client.username_pw_set(usr or self.device_name, pwd or None)
        client.connect(self.broker, self.port)
        client.publish('start')
        self.client = client

    def subscribe(self, topic=None):
        print(topic or self.topic)
        self.client.subscribe(topic or self.topic)
        self.client.on_message = self.on_message

    def publish(self, msg):
        result = self.client.publish(self.topic, self.device_name+msg)
        status = result[0]
        if status == 0:
            pass
        else:
            print(f"Failed to send message to topic {self.topic}")

    def start(self):
        self.client.loop_start()  # Start the MQTT client in the background
