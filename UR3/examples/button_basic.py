import serial

# Replace 'COM3' with the appropriate serial port for your system
# On Windows, it might be 'COMx' (e.g., COM3)
# On Linux or macOS, it could be '/dev/ttyUSB0' or '/dev/ttyACM0'
ser = serial.Serial('COM5', 9600, timeout=1)
# ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

while True:
    # Read the line from the serial port
    line = ser.readline().decode('utf-8').strip()
    
    # Check if there is any data received
    if line:
        print("Received: " + line)
    
ser.close()
