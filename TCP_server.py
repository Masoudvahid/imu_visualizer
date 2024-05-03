import json
import math
import socket

import numpy as np
from scipy import integrate
from scipy.spatial.transform import Rotation as R


class GyroscopeOrientation:
    def __init__(self):
        self.dt = 0.02  # Time interval in seconds (10 ms - 0.02)
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

    def get_gyro(self):
        return self.x_angle, self.y_angle, self.z_angle


class RotationVector:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.w = 0
        self.roll_x = 0
        self.pitch_y = 0
        self.yaw_z = 0

    def update(self, x, y, z, w):
        self.x = x
        self.y = y
        self.z = z
        self.w = w
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.degrees(math.atan2(t0, t1))
        t2 = +2.0 * (w * y - z)
        if t2 > 1.0:
            t2 = 1.0
        if t2 < -1.0:
            t2 = -1.0
        pitch_y = math.degrees(math.asin(t2))
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.degrees(math.atan2(t3, t4))
        self.roll_x = roll_x
        self.pitch_y = pitch_y
        self.yaw_z = yaw_z

    def get_orientation(self):
        return self.x, self.y, self.z, self.w
        # return self.roll_x, self.pitch_y, self.yaw_z


class LinearAcceleration:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.velocity = 0
        self.position = (0, 0, 0)
        self.time_interval = 0
        self.prev_time_stamp = 0

    def update(self, acc_x, acc_y, acc_z, time_stamp):
        if self.prev_time_stamp == 0:
            self.prev_time_stamp = time_stamp / 1e9
            return
        else:
            self.time_interval = abs(self.prev_time_stamp - time_stamp / 1e9)
            self.prev_time_stamp = time_stamp / 1e9

        # # Integrate each component of the acceleration to get the velocity.
        # velocity_x = integrate.cumtrapz(acc_x, self.time_interval, initial=0)
        # velocity_y = integrate.cumtrapz(acc_y, self.time_interval, initial=0)
        # velocity_z = integrate.cumtrapz(acc_z, self.time_interval, initial=0)
        #
        # # Integrate each component of the velocity to get the position.
        # position_x = integrate.cumtrapz(velocity_x, self.time_interval, initial=0)
        # position_y = integrate.cumtrapz(velocity_y, self.time_interval, initial=0)
        # position_z = integrate.cumtrapz(velocity_z, self.time_interval, initial=0)
        #
        # self.velocity = [velocity_x, velocity_y, velocity_z]
        # self.position = [position_x, position_y, position_z]

        self.x = (acc_x)
        self.y = (acc_y)
        self.z = (acc_z)

        self.velocity += np.array([acc_x, acc_y, acc_z]) * self.time_interval
        self.position += self.velocity * self.time_interval
        self.position /= 5
        # print(self.position)

        # self.velocity = np.cumsum(acceleration_array * self.time_intervals, axis=0)
        # self.position = np.cumsum(self.velocity * self.time_intervals, axis=0)

    def get_data(self):
        return [self.x, self.y, self.z, self.prev_time_stamp]

    def get_position(self):
        return self.position


class TrajectoryCalculator:
    def __init__(self, initial_position=(0, 0, 0), initial_velocity=(0, 0, 0), time_interval=0.01):
        self.initial_position = initial_position
        self.initial_velocity = initial_velocity
        self.time_interval = time_interval
        # self.new_pos =

    def calculate_new_position(self, linear_acceleration):
        new_x = self.initial_position[0] + self.initial_velocity[0] * self.time_interval + 0.5 * linear_acceleration[
            0] * self.time_interval ** 2
        new_y = self.initial_position[1] + self.initial_velocity[1] * self.time_interval + 0.5 * linear_acceleration[
            1] * self.time_interval ** 2
        new_z = self.initial_position[2] + self.initial_velocity[2] * self.time_interval + 0.5 * linear_acceleration[
            2] * self.time_interval ** 2
        return new_x, new_y, new_z

    def get_pos(self):
        return


class TrajectoryReconstructor:
    def __init__(self):
        self.velocity = np.array([0, 0, 0])
        self.position = np.array([0, 0, 0])
        self.last_time = None

    def update(self, time, acceleration):
        if self.last_time is None:
            self.last_time = float(time) / 1e6
            return

        dt = float(time) - self.last_time / 1e6
        self.velocity += acceleration * dt
        self.position += self.velocity * dt
        self.last_time = time


class TCP_server:
    def __init__(self):
        # Set up the server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = socket.gethostname()
        self.IPAddr = socket.gethostbyname(self.host)
        self.port = 9885
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.client_socket = None
        self.addr = None
        self.received_data = list()
        self.gyro = GyroscopeOrientation()
        self.rot_vec = RotationVector()
        self.linear_acc = LinearAcceleration()
        self.tr = TrajectoryReconstructor()

        self.__init_connection()
        self.__transmit_data()

    def __init_connection(self):
        print(f"Server Listening on, {self.IPAddr} | {self.host}, port {self.port}")
        # Accept incoming connections
        self.client_socket, self.addr = self.server_socket.accept()
        print("Successfully Connected to ", self.addr)

    def __transmit_data(self):
        # Receive data from the client (your Android app)
        while True:
            data = self.client_socket.recv(256)
            if not data:
                break

            print(data)
            self.extract_sensor_data(data)
            # x, y, z, w = self.rot_vec.get_orientation()
            # print(x, y, z, w)
            quaternion = self.rot_vec.get_orientation()
            position = self.linear_acc.get_position()
            # position = self.tr.position

            if all(quaternion):
                with open(r"C:\Users\Admin\Desktop\orientation.txt", 'a') as f:
                    txt = ';'.join([str(item) for item in quaternion])
                    txt += '\n'
                    f.write(txt)
            if all(position):
                with open(r"C:\Users\Admin\Desktop\position.txt", 'a') as f:
                    txt = ';'.join([str(item) for item in position])
                    txt += '\n'
                    f.write(txt)
                with open(r"C:\Users\Admin\Desktop\graphics.txt", 'a') as f:
                    txt = ','.join([str(item) for item in self.linear_acc.get_data()])
                    txt += '\n'
                    f.write(txt)

        self.client_socket.close()

    def extract_gyro(self, data):
        entries = data.decode('utf-8').split('\n')
        for entry in entries:
            try:
                json_data = json.loads(entry)
                if 'gyroscope' in json_data:
                    gyroscope_value = json_data['gyroscope'].get('value')
                    if gyroscope_value:
                        self.gyro.update_orientation(*gyroscope_value)
            except json.JSONDecodeError:
                pass

    def extract_sensor_data(self, data):
        entries = data.decode('utf-8').split('\n')
        # print(entries)
        for entry in entries:
            try:
                json_data = json.loads(entry)
                if 'rotationVectorData' in json_data:
                    self.rot_vec.update(*json_data['rotationVectorData'][:-1])
                if 'linearAccelerationData' in json_data:
                    # self.tr.update(json_data['timestamp'], json_data['linearAccelerationData'])
                    self.linear_acc.update(*json_data['linearAccelerationData'], json_data['timestamp'])
            except json.JSONDecodeError:
                pass

    def extract_rotation_vector(self, data):
        entries = data.decode('utf-8').split('\n')
        for entry in entries:
            try:
                json_data = json.loads(entry)
                if 'value' in json_data:
                    self.rot_vec.update(*json_data['value'][:-1])
            except json.JSONDecodeError:
                pass

if __name__ == '__main__':
    server = TCP_server()
