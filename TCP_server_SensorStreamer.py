import json
import math
import socket
import numpy as np
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

    def update(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        r = R.from_rotvec([x, y, z])
        self.z, self.x, self.y = r.as_euler('x,y,z', degrees=True)

    def get_rotation_vec(self):
        return self.x, self.y, self.z


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
            data = self.client_socket.recv(1024)  # Change the buffer size as needed
            print(data)
            if not data:
                break
            # self.extract_gyro(data)
            # x, y, z = self.gyro.get_gyro()
            self.extract_rotation_vector(data)
            x, y, z = self.rot_vec.get_rotation_vec()
            # print(x, y, z)
            with open(r"C:\Users\Admin\Desktop\phone_angles.txt", 'a') as f:
                txt = ';'.join([str(x), str(y), str(z)])
                txt += '\n'
                f.write(txt)
        # self.client_socket.close()

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

    def extract_rotation_vector(self, data):
        entries = data.decode('utf-8').split('\n')
        for entry in entries:
            try:
                json_data = json.loads(entry)
                if 'rotationVector' in json_data:
                    rot_vec_value = json_data['rotationVector'].get('value')
                    if rot_vec_value:
                        self.rot_vec.update(*rot_vec_value)
                elif 'value' in json_data:
                    self.rot_vec.update(*json_data['value'])
            except json.JSONDecodeError:
                pass


if __name__ == '__main__':
    server = TCP_server()
