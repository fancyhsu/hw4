import paho.mqtt.client as paho
import time
import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import struct

# XBee setting
serdev = '/dev/ttyUSB0'
s = serial.Serial(serdev, 9600)
s.write("+++".encode())
char = s.read(2)
print("Enter AT mode.")
print(char.decode())
s.write("ATMY 0x241\r\n".encode())
char = s.read(3)
print("Set MY <BASE_MY>.")
print(char.decode())
s.write("ATDL 0x240\r\n".encode())
char = s.read(3)
print("Set DL <BASE_DL>.")
print(char.decode())
s.write("ATID 0x0\r\n".encode())
char = s.read(3)
print("Set PAN ID <PAN_ID>.")
print(char.decode())
s.write("ATWR\r\n".encode())
char = s.read(3)
print("Write config.")
print(char.decode())
s.write("ATMY\r\n".encode())
char = s.read(4)
print("MY :")
print(char.decode())
s.write("ATDL\r\n".encode())
char = s.read(4)
print("DL : ")
print(char.decode())
s.write("ATCN\r\n".encode())
char = s.read(3)
print("Exit AT mode.")
print(char.decode())
print("start sending RPC")

samples = 10
x = np.zeros(samples)
t = np.arange(1,samples+1)

i = 0
while i<=samples:
    s.write("/rpc_call/run\r".encode())
    line = s.readline()
    line = line.decode()
    if i != 0: 
        if int(line[0]) > 1:
            if len(line) == 2:
                x[i-1] = int(line[0])
            else:
                x[i-1] = 10*int(line[0])+ int(line[1])
            print(x[i-1])
            i += 1
    if i == 0: i+=1
    time.sleep(1)

data_num = int(x.sum())
allline = []
for k in range(data_num):
    s.write("/rpc_call_alldata/run\r".encode())
    line = s.readline()
    line = line.decode()
    allline.append(line)
    time.sleep(0.1)
    print(line.split())
s.close()

tt = []
temp = 0
for k in range(samples):
    if int(x[k]) > 2:
        for l in range(int(x[k])):
            temp += 0.1
            tt.append(temp)
    else:
        for l in range(int(x[k])):
            temp += 0.5
            tt.append(temp)


mqttc = paho.Client()
# Settings for connection
# TODO: revise host to your ip
host = "192.168.0.101"
topic = "velocity"
# Callbacks
def on_connect(self, mosq, obj, rc):
      print("Connected rc: " + str(rc))
def on_message(mosq, obj, msg):
      print("[Received] Topic: " + msg.topic + ", Message: " + str(msg.payload) + "\n");
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

num = 0
while num < data_num:
      ret = mqttc.publish(topic, allline[num]+' '+str(tt[num]), qos=0)
      if (ret[0] != 0):
            print("Publish failed")
      mqttc.loop()
      time.sleep(0.1)
      num += 1
ret = mqttc.publish(topic, 'F', qos=0)

fig, ax = plt.subplots(1, 1)
ax.plot(t,x)
ax.set_xlabel('Timestamp')
ax.set_ylabel('Number')
plt.show()
