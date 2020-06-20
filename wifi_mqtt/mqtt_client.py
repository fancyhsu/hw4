import paho.mqtt.client as paho
import time
import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import struct
# https://os.mbed.com/teams/mqtt/wiki/Using-MQTT#python-client
# MQTT broker hosted on local machine
mqttc = paho.Client()
# Settings for connection
# TODO: revise host to your ip
host = "192.168.0.101"
topic = "velocity"
xx = []
yy = []
zz = []
tt = []
# Callbacks
def on_connect(self, mosq, obj, rc):
      print("Connected rc: " + str(rc))
def on_message(mosq, obj, msg):
      print("[Received] Topic: " + msg.topic + ", Message: " + str(msg.payload) + "\n")
      line = str(msg.payload).split()
      global xx
      global yy
      global zz
      global tt
      if line[0].split("'")[1] == 'F': 
            print(xx)
            print(yy)
            print(zz)
            print(tt)
            plt.figure()
            plt.plot(tt,xx,'g',label = 'x')
            plt.plot(tt,yy,'r',label = 'y')
            plt.plot(tt,zz,'b',label = 'z')
            plt.title("hw4")
            plt.xlabel('Timestamp')
            plt.ylabel('acc value')
            plt.show()
      else:
            x = float((line[0].split("b'"))[1])
            y = float(line[1])
            z = float((line[2].split("\\n"))[0])
            t = float((line[3].split("'"))[0])
            xx.append(x)
            yy.append(y)
            zz.append(z)
            tt.append(t)
            print(x,y,z,t)

def on_subscribe(mosq, obj, mid, granted_qos):
      print("Subscribed OK")
def on_unsubscribe(mosq, obj, mid, granted_qos):
      print("Unsubscribed OK")
# Set callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe
# Connect and subscribe
print("Connecting to " + host + "/" + topic)
mqttc.connect(host, port=1883, keepalive=60)
mqttc.subscribe(topic, 0)
# Publish messages from Python
# num = 0
# while num != 5:
#       ret = mqttc.publish(topic, "Message from Python!\n", qos=0)
#       if (ret[0] != 0):
#             print("Publish failed")
#       mqttc.loop()
#       time.sleep(1.5)
#       num += 1
# Loop forever, receiving messages
mqttc.loop_forever()