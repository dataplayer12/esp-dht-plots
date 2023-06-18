import base64
import io
import random
import time
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import socket
from datetime import datetime
import threading
import matplotlib.dates as mdates


host_addr = '192.168.50.60'
host_port = 6000
buffer_size=1024
polling_frequency = 3
history_in_minutes = 8*60 #12 hours

smiley_face="\U0001F600"

emoji=smiley_face

udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp.bind((host_addr, host_port))
udp.settimeout(2*polling_frequency + 0.5)

app = Flask(__name__)
socketio = SocketIO(app)
latest_figure = None
lock=threading.Lock()

time_values=[]
temp_values=np.zeros(history_in_minutes*60//polling_frequency)
humid_values=np.zeros(history_in_minutes*60//polling_frequency)

fig, (ax1,ax2) = plt.subplots(2,1)
fig.set_facecolor('black')

ax1.set_facecolor('black')
ax2.set_facecolor('black')


ax1.spines['bottom'].set_color('white')
ax1.spines['top'].set_color('white')
ax1.spines['left'].set_color('white')
ax1.spines['right'].set_color('white')

# Set the color of the tick labels
ax1.xaxis.label.set_color('white')
ax1.yaxis.label.set_color('white')

# Set the color of the ticks
ax1.tick_params(colors='white')

## Axis 2

ax2.spines['bottom'].set_color('white')
ax2.spines['top'].set_color('white')
ax2.spines['left'].set_color('white')
ax2.spines['right'].set_color('white')

# Set the color of the tick labels
ax2.xaxis.label.set_color('white')
ax2.yaxis.label.set_color('white')

# Set the color of the ticks
ax2.tick_params(colors='white')


fig.set_figwidth(8)

count=0
hbcount=0
max_index = history_in_minutes*60//polling_frequency

def read_sensor_data(udp):
    msg_addr = udp.recvfrom(buffer_size)
    msg = str(msg_addr[0])
    addr = msg_addr[1]
    cur_time = datetime.now()

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

    return cur_time, cur_temp, cur_humid


@app.route("/")
def index():
    return render_template("index.html")

def create_figure(times):
    global temp_values, humid_values, count, hbcount

    #times = [s[0] for s in sensor_data]
    #temperatures= [s[1] for s in sensor_data]
    #humidities = [s[2] for s in sensor_data]
    ax1t = "DHT22 sensor data"
    if hbcount%2==0:
        ax1t = f"{emoji}" + ax1t
        ax1t += f"{emoji}"

    hbcount += 1

    if len(ax1.lines):
        del ax1.lines[-1]
        del ax2.lines[-1]

    ax1.plot(times, temp_values[:count], 'g')
    ax1.set_ylabel("Temperature [°C]")
    ax1.set_title(ax1t, color='white')

    ax1.title.set_fontname("Noto Color Emoji")
    ax2.plot(times, humid_values[:count], 'g')
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Humidity [%]")

    date_format = mdates.DateFormatter('%H:%M:%S')
    ax1.xaxis.set_major_formatter(date_format)
    ax2.xaxis.set_major_formatter(date_format)
    ax1.set_xlim(times[0], times[-1])
    ax2.set_xlim(times[0], times[-1])
    fig.autofmt_xdate()
    
    buf = io.BytesIO()
    plt.savefig(buf, facecolor=fig.get_facecolor(), format='png')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def update_figure():
    global latest_figure, count, temp_values, humid_values
    sensor_data = []

    while True:
        stime =  time.time()

        if count == max_index:
            temp_values[:-1] = temp_values[1:]
            humid_values[:-1]= humid_values[1:]
            time_values.pop(0)
            with lock:
                count=max_index - 1

        newdata = read_sensor_data(udp)

        time_values.append(newdata[0])
        temp_values[count]=newdata[1]
        humid_values[count]=newdata[2]

        with lock:
            count+=1
            latest_figure = create_figure(time_values)

        wtime = polling_frequency - (time.time() - stime)


@socketio.on("request_data")
def send_data():
    
    while True:
        with lock:
            figure_data = latest_figure

        emit("update_figure", figure_data)        
        time.sleep(polling_frequency)

if __name__ == "__main__":
    fig_updater = threading.Thread(target=update_figure)
    fig_updater.start()
    socketio.run(app, host="192.168.50.60", port=5100)

