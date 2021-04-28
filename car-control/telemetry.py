import socket
from struct import unpack
from time import sleep
import select

# https://github.com/martijnvankekem/f1_telemetry_python/blob/master/F1Telemetry/ArrayStructure.py
returnData = []  # Create an empty array


# Initialize data array -- BEGIN FUNCTION
def initArray():
    global returnData  # Access the global variable returnData
    # FLOATS
    returnData.append(["m_time", 0, 'f'])  # Total session time (in seconds)
    returnData.append(["m_lapTime", 0, 'f'])  # Current lap time (in seconds)
    returnData.append(["m_lapDistance", 0, 'f'])  # Current lap distance (in meters)
    returnData.append(["m_totalDistance", 0, 'f'])  # Total distance (in meters)
    returnData.append(["m_x", 0, 'f'])  # World space X-position
    returnData.append(["m_y", 0, 'f'])  # World space Y-position
    returnData.append(["m_z", 0, 'f'])  # World space Z-position
    returnData.append(["m_speed", 0, 'f'])  # Car speed in meters per second
    returnData.append(["m_xv", 0, 'f'])  # World space X-velocity
    returnData.append(["m_yv", 0, 'f'])  # World space Y-velocity
    returnData.append(["m_zv", 0, 'f'])  # World space Z-velocity
    returnData.append(["m_xr", 0, 'f'])  # World space right X-direction
    returnData.append(["m_yr", 0, 'f'])  # World space right Y-direction
    returnData.append(["m_zr", 0, 'f'])  # World space right Z-direction
    returnData.append(["m_xd", 0, 'f'])  # World space forward X-direction
    returnData.append(["m_yd", 0, 'f'])  # World space forward Y-direction
    returnData.append(["m_zd", 0, 'f'])  # World space forward Z-direction
    returnData.append(["m_susp_pos_rl", 0, 'f'])  # Suspension position - Rear left wheel
    returnData.append(["m_susp_pos_rr", 0, 'f'])  # Suspension position - Rear right wheel
    returnData.append(["m_susp_pos_fl", 0, 'f'])  # Suspension position - Front left wheel
    returnData.append(["m_susp_pos_fr", 0, 'f'])  # Suspension position - Front right wheel
    returnData.append(["m_susp_vel_rl", 0, 'f'])  # Suspension velocity - Rear left wheel
    returnData.append(["m_susp_vel_rr", 0, 'f'])  # Suspension velocity - Rear right wheel
    returnData.append(["m_susp_vel_fl", 0, 'f'])  # Suspension velocity - Front left wheel
    returnData.append(["m_susp_vel_fr", 0, 'f'])  # Suspension velocity - Front right wheel
    returnData.append(["m_wheel_speed_rl", 0, 'f'])  # Wheel speed - Rear left wheel
    returnData.append(["m_wheel_speed_rr", 0, 'f'])  # Wheel speed - Rear right wheel
    returnData.append(["m_wheel_speed_fl", 0, 'f'])  # Wheel speed - Front left wheel
    returnData.append(["m_wheel_speed_fr", 0, 'f'])  # Wheel speed - Front right wheel
    returnData.append(["m_throttle", 0, 'f'])  # Throttle value (min: 0, max: 1)
    returnData.append(["m_steer", 0, 'f'])  # Steering rotation (min: 1, max: -1)
    returnData.append(["m_brake", 0, 'f'])  # Brake value (min: 0, max: 1)
    returnData.append(["m_clutch", 0, 'f'])  # Clutch value (min: 0, max: 1)
    returnData.append(["m_gear", 0, 'f'])  # Current gear (0 => R, 1 => N, 2 => ...)
    returnData.append(["m_gforce_lat", 0, 'f'])  # G-Force latitude
    returnData.append(["m_gforce_lon", 0, 'f'])  # G-Force longitude
    returnData.append(["m_lap", 0, 'f'])  # Current lap
    returnData.append(["m_engineRate", 0, 'f'])  # Current RPM
    returnData.append(["m_sli_pro_native_support", 0, 'f'])  # SLI Pro support
    returnData.append(["m_car_position", 0, 'f'])  # Car race position
    returnData.append(["m_kers_level", 0, 'f'])  # KERS energy left
    returnData.append(["m_kers_max_level", 0, 'f'])  # KERS maximum energy
    returnData.append(["m_drs", 0, 'f'])  # DRS state, 0 = off, 1 = on
    returnData.append(["m_traction_control", 0, 'f'])  # Traction control enabled (off: 0, high: 2)
    returnData.append(["m_anti_lock_brakes", 0, 'f'])  # Anti lock brakes enabled (off: 0, on: 1)
    returnData.append(["m_fuel_in_tank", 0, 'f'])  # Current fuel mass
    returnData.append(["m_fuel_capacity", 0, 'f'])  # Fuel capacity
    returnData.append(["m_in_pits", 0, 'f'])  # Car in pit (0: no, 1: pitting, 2: in pit area)
    returnData.append(["m_sector", 0, 'f'])  # Current sector car is in (0: sector 1, 1: sector 2, 2: sector 3)
    returnData.append(["m_sector1_time", 0, 'f'])  # Current first sector time
    returnData.append(["m_sector2_time", 0, 'f'])  # Current second sector time
    returnData.append(["m_brakes_temp_rl", 0, 'f'])  # Brake temperature - Rear left wheel
    returnData.append(["m_brakes_temp_rr", 0, 'f'])  # Brake temperature - Rear right wheel
    returnData.append(["m_brakes_temp_fl", 0, 'f'])  # Brake temperature - Front left wheel
    returnData.append(["m_brakes_temp_fr", 0, 'f'])  # Brake temperature - Front right wheel


# Initialize data array -- END FUNCTION

initArray()  # Execute the function

DIRT_IP = "127.0.0.1"
DIRT_PORT = 20777

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1)

sock.bind((DIRT_IP, DIRT_PORT))

print('Connecting telemetry socket')


def reset():
    global returnData
    returnData = []  # Create an empty array
    initArray()


def update():
    global returnData  # Access the global variable returnData
    index = 0  # Set starting index
    ready = select.select([sock], [], [], 1)
    if ready[0]:
        data, addr = sock.recvfrom(4096)  # Receive value from UDP socket
        for x in range(0, len(returnData)):  # Do for every item in the received array
            size = 4 if returnData[x][2] == 'f' else 1  # Set size based on if it's a byte or float
            returnData[x][1] = unpack('<' + returnData[x][2], data[index:index + size])[0]  # Add float to the array
            index += size  # Increase starting index with the size


# Get UDP value by it's name
def get_telemetry_value(name):
    global returnData  # Access the global variable returnData
    for x in range(0, len(returnData)):  # Do for every item in returnData
        if returnData[x][0] == name:  # If this item matches the name
            return returnData[x][1]  # Return the value of this item
    return -1  # Nothing found, return -1


# Run continuously
def test():
    while True:
        index = 0;  # Set starting index
        data, addr = sock.recvfrom(4096)  # Receive value from UDP socket
        for x in range(0, len(returnData)):  # Do for every item in the received array
            size = 4 if returnData[x][2] == 'f' else 1  # Set size based on if it's a byte or float
            returnData[x][1] = unpack('<' + returnData[x][2], data[index:index + size])[0]  # Add float to the array
            index += size  # Increase starting index with the size

        speed = get_telemetry_value('m_speed')
        laptime = get_telemetry_value('m_lapTime')
        gforce_lat = get_telemetry_value('m_gforce_lat')
        gforce_lon = get_telemetry_value('m_gforce_lon')
        parsed = 'm_speed:' + str(speed) + ',m_lapTime:' + str(laptime) + ',m_gforce_lat:' + str(
            gforce_lat) + ',m_gforce_lon:' + str(gforce_lon)
        print(parsed)
        sleep(0.05)


if __name__ == '__main__':
    while True:
        update()
        print(get_telemetry_value('m_speed'))
    # test()
