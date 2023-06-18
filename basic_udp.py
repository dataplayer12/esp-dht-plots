import socket
import numpy as np
import matplotlib.pyplot as plt
import time

host_addr = '192.168.50.60'
host_port = 6000
buffer_size=1024


udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp.bind((host_addr, host_port))

print('UDP Server started')
times=[]
temps=[]
humid=[]

while True:
	msg_addr = udp.recvfrom(buffer_size)
	msg = str(msg_addr[0])
	print(msg)
	addr = msg_addr[1]
	if 'Error' in msg:
		cur_temp=np.nan
		cur_humid=np.nan
	else:
		tstr = msg.split(':')[2].strip()
		hstr = msg.split(':')[3].strip()
		tsplit=tstr.rfind('°C')
		hsplit=hstr.rfind('%')
		cur_temp = float(tstr[:5])
		cur_humid = float(hstr[:hsplit])

		temps.append(cur_temp)
		humid.append(cur_humid)
		print(cur_temp, cur_humid)
