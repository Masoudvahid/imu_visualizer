import math

import websocket
import json


def on_message(ws, message):
    values = json.loads(message)['values']
    x = values[0]
    y = values[1]
    z = values[2]
    # gyroscope.update_orientation(x, y, z)
    # x, y, z = gyroscope.get_g()
    with open(r"C:\Users\Admin\Desktop\phone_angles.txt", 'a') as f:
        txt = ';'.join([str(x), str(y), str(z)])
        txt += '\n'
        f.write(txt)
    print("x = ", x, "y = ", y, "z = ", z)


def on_error(ws, error):
    print("error occurred ", error)


def on_close(ws, close_code, reason):
    print("connection closed : ", reason)


def on_open(ws):
    print("connected")
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

def connect(url):
    ws = websocket.WebSocketApp(url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever()

gyroscope = GyroscopeOrientation()
connect("ws://192.168.0.140:8080/sensor/connect?type=android.sensor.orientation")
