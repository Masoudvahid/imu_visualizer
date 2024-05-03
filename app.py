import dash
from dash.dependencies import Output, Input
from dash import dcc, html, dcc
from datetime import datetime
import json
import plotly.graph_objs as go
from collections import deque
from flask import Flask, request
import logging
from flask.logging import default_handler
import math


server = Flask(__name__)
app = dash.Dash(__name__, server=server)
app.logger.removeHandler(default_handler)
app.logger.setLevel(logging.ERROR)

MAX_DATA_POINTS = 1000
UPDATE_FREQ_MS = 1000

time = deque(maxlen=MAX_DATA_POINTS)

accel_x = deque(maxlen=MAX_DATA_POINTS)
accel_y = deque(maxlen=MAX_DATA_POINTS)
accel_z = deque(maxlen=MAX_DATA_POINTS)

gyro_x = deque(maxlen=MAX_DATA_POINTS)
gyro_y = deque(maxlen=MAX_DATA_POINTS)
gyro_z = deque(maxlen=MAX_DATA_POINTS)

qw = deque(maxlen=MAX_DATA_POINTS)
qx = deque(maxlen=MAX_DATA_POINTS)
qy = deque(maxlen=MAX_DATA_POINTS)
qz = deque(maxlen=MAX_DATA_POINTS)

app.layout = html.Div(
    [
        dcc.Graph(id="live_graph"),
        dcc.Graph(id="gyro_graph"),  # New gyroscope graph
        dcc.Interval(id="counter", interval=UPDATE_FREQ_MS),
    ]
)


def euler_from_quaternion(x, y, z, w):
    """
    Convert a quaternion into euler angles (roll, pitch, yaw)
    roll is rotation around x in radians (counterclockwise)
    pitch is rotation around y in radians (counterclockwise)
    yaw is rotation around z in radians (counterclockwise)
    """
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = math.atan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = math.asin(t2)

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = math.atan2(t3, t4)

    return roll_x, pitch_y, yaw_z  # in radians

@app.callback(
    [Output("live_graph", "figure"), Output("gyro_graph", "figure")],
    Input("counter", "n_intervals"),
)
def update_graph(_counter):
    accel_data = [
        go.Scatter(x=list(time), y=list(d), name=name)
        for d, name in zip([accel_x, accel_y, accel_z], ["X", "Y", "Z"])
    ]

    gyro_data = [
        go.Scatter(x=list(time), y=list(d), name=name)
        for d, name in zip([gyro_x, gyro_y, gyro_z], ["X", "Y", "Z"])
    ]

    accel_graph = {
        "data": accel_data,
        "layout": go.Layout(
            {
                "xaxis": {"type": "date"},
                "yaxis": {"title": "Acceleration ms<sup>-2</sup>"},
            }
        ),
    }

    gyro_graph = {
        "data": gyro_data,
        "layout": go.Layout(
            {
                "xaxis": {"type": "date"},
                "yaxis": {"title": "Gyroscope data"},
            }
        ),
    }

    if len(time) > 0:
        accel_graph["layout"]["xaxis"]["range"] = [min(time), max(time)]
        accel_graph["layout"]["yaxis"]["range"] = [
            min(accel_x + accel_y + accel_z),
            max(accel_x + accel_y + accel_z),
        ]

        gyro_graph["layout"]["xaxis"]["range"] = [min(time), max(time)]
        gyro_graph["layout"]["yaxis"]["range"] = [
            min(gyro_x + gyro_y + gyro_z),
            max(gyro_x + gyro_y + gyro_z),
        ]

    return accel_graph, gyro_graph


@server.route("/data", methods=["POST"])
def data():  # listens to the data streamed from the sensor logger
    if str(request.method) == "POST":
        # print(f'received data: {request.data}')
        data = json.loads(request.data)
        for d in data["payload"]:
            if d.get("name", None) == "accelerometer":
                ts = datetime.fromtimestamp(d["time"] / 1000000000)
                if len(time) == 0 or ts > time[-1]:
                    time.append(ts)
                    accel_x.append(d["values"]["x"])
                    accel_y.append(d["values"]["y"])
                    accel_z.append(d["values"]["z"])

            elif d.get("name", None) == "orientation":  # Process gyroscope data
                qw.append(d["values"]["qw"])
                qx.append(d["values"]["qx"])
                qy.append(d["values"]["qy"])
                qz.append(d["values"]["qz"])
                print(qw[-1], qx[-1], qy[-1], qz[-1])
                x, y, z = euler_from_quaternion(qx[-1], qy[-1], qz[-1], qw[-1])
                print(x, y, z)
                with open(r"C:\Users\Admin\Desktop\phone_angles.txt", 'a') as f:
                    txt = ';'.join([str(x), str(y), str(z)])
                    txt += '\n'
                    f.write(txt)

            elif d.get("name", None) == "gyroscope":  # Process gyroscope data
                gyro_x.append(d["values"]["x"])
                gyro_y.append(d["values"]["y"])
                gyro_z.append(d["values"]["z"])
                gyroscope.update_orientation(gyro_x[-1], gyro_y[-1], gyro_z[-1])
                x, y, z = gyroscope.get_g()
                print(gyro_x[-1], gyro_y[-1], gyro_z[-1])
                with open(r"C:\Users\Admin\Desktop\phone_angles.txt", 'a') as f:
                    txt = ';'.join([str(x), str(y), str(z)])
                    txt += '\n'
                    f.write(txt)

    return "success"

class GyroscopeOrientation:
    def __init__(self):
        self.dt = 0.01  # Time interval in seconds
        self.x_angle = 0  # Initial orientation angle around x-axis
        self.y_angle = 0  # Initial orientation angle around y-axis
        self.z_angle = 0  # Initial orientation angle around z-axis

    def update_orientation(self, gyro_x, gyro_y, gyro_z):
        # Integrate the gyroscope data to update the orientation angles
        self.x_angle += gyro_x * self.dt
        self.y_angle += gyro_y * self.dt
        self.z_angle += gyro_z * self.dt

        # Normalize the angles to keep them within the range of 0 to 2*pi
        self.x_angle = self.x_angle % (2 * math.pi)
        self.y_angle = self.y_angle % (2 * math.pi)
        self.z_angle = self.z_angle % (2 * math.pi)

    def get_g(self):
        return self.x_angle, self.y_angle, self.z_angle

if __name__ == "__main__":
    gyroscope = GyroscopeOrientation()
    app.run_server(port=8000, host="0.0.0.0")
