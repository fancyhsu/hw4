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
# while i<=10:
#     s.write("/rpc_call/run\r".encode())
#     line = s.readline()
#     line = line.decode()
#     if i != 0: 
#         if int(line[0]) > 1:
#             if len(line) == 2:
#                 x[i-1] = int(line[0])
#             else:
#                 x[i-1] = 10*int(line[0])+ int(line[1])
#             print(x[i-1])
#             i += 1
#     if i == 0: i+=1
#     time.sleep(1)
while i<=10:
    s.write("/rpc_call/run\r".encode())
    line = s.readline()
    line = line.decode()
    print(line)
    time.sleep(1)
    
s.close()

# for j in range(samples):
#     print(x[j])
#     print(t[j])

fig, ax = plt.subplots(1, 1)
ax.plot(t,x)

ax.set_xlabel('Timestamp')
ax.set_ylabel('Number')

plt.show()