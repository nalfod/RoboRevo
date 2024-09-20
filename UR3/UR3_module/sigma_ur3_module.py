import sys
import math
import threading
import socket

sys.path.append("..")
# import logging

import rtde.rtde as rtde
import rtde.rtde_config as rtde_config

class UR3:
    def __init__(self, KRP):
        # the keyboard reference point in the base coordinate system of the robot
        # TODO: note, that KRP is 3 dimensions now, but it has to be four! The keyboard is not strictly alligned with the robot's coordinate system
        #       Z axis should be parallel, but the other two can deviate!! FIXME
        self.KRP = KRP
        self.home_pos_of_joints = [ math.radians(90), math.radians(-90), math.radians(65), math.radians(-65), math.radians(-90), math.radians(0)  ]

        self.ROBOT_HOST = "192.168.56.101"
        self.ROBOT_PORT = 30004
        self.config_filename = "control_loop_configuration.xml"

        self.conf = rtde_config.ConfigFile(self.config_filename)
        state_names, state_types = self.conf.get_recipe("state")
        setp_names, setp_types = self.conf.get_recipe("setp")
        mode_names, mode_types = self.conf.get_recipe("mode")
        watchdog_names, watchdog_types = self.conf.get_recipe("watchdog")
        #pushbutton_names, pushbutton_types = self.conf.get_recipe("pushbutton")

        self.con = rtde.RTDE(self.ROBOT_HOST, self.ROBOT_PORT)
        print("----------------------------------------------\n")
        print("Trying to connect to IP= " + str(self.ROBOT_HOST) + " PORT= " + str(self.ROBOT_PORT) )
        self.con.connect()
        print("Connection is successful!")
        print("\n----------------------------------------------\n\n")

        # setup recipes
        # TODO: revise, which member variable can be a stack variable!! and change them
        self.con.send_output_setup(state_names, state_types)
        self.setp = self.con.send_input_setup(setp_names, setp_types)
        self.mode = self.con.send_input_setup(mode_names, mode_types)
        self.watchdog = self.con.send_input_setup(watchdog_names, watchdog_types)
        #self.pushbutton = self.con.send_input_setup(pushbutton_names, pushbutton_types)

        # setpoints
        self.setp.input_double_register_0 = 0
        self.setp.input_double_register_1 = 0
        self.setp.input_double_register_2 = 0
        self.setp.input_double_register_3 = 0
        self.setp.input_double_register_4 = 0
        self.setp.input_double_register_5 = 0

        # 0: joint movement, 1: pose movement, 2: push button movement
        self.mode.input_int_register_1 = 0

        # The function "rtde_set_watchdog" in the "rtde_control_loop.urp" creates a 1 Hz watchdog
        self.watchdog.input_int_register_0 = 0

        # start data synchronization
        if not self.con.send_start():
            sys.exit()

        self.move_completed = True
        self.con.send(self.watchdog)

    # static function that converts a dict to a list
    @staticmethod
    def setp_to_list(sp):
        sp_list = []
        for i in range(0, 6):
            sp_list.append(sp.__dict__["input_double_register_%i" % i])
        return sp_list


    # static function that converts a list to dict
    @staticmethod
    def list_to_setp(sp, list):
        for i in range(0, 6):
            sp.__dict__["input_double_register_%i" % i] = list[i]
        return sp
    
    @staticmethod
    def print_position_from_list(position, type_of_movement):
        for i in range(0, 6):
            if type_of_movement == "joint":
                print("     My " + str(i) + ". value is= " + str(round(math.degrees(round(position[i], 2)), 2)) + " deg" )
            else:
                print("     My " + str(i) + ". value is= " + str( round(position[i] * 1000, 2) ) + " mm")

    def move_robot(self, type_of_movement, list_of_sp):
        print( "*****BEGIN - move_robot *****")
        print("My type of movement is= " + str(type_of_movement) + " My position is= " + str(list_of_sp) )
        if type_of_movement != "joint" and type_of_movement != "TCP":
            print("Invalid arg")
            return

        self.move_completed = True

        while True:
            state = self.con.receive()
            if state is None:
                print("Recieved state is None, aborting method...")
                break

            if self.move_completed and state.output_int_register_0 == 1:
                # output_int_register_0 == 1 --> robot ready to recieve a new command
                self.move_completed = False

                if type_of_movement == "joint":
                    current_position = state.actual_q
                    self.mode.input_int_register_1 = 0
                else:
                    current_position = state.actual_TCP_pose
                    self.mode.input_int_register_1 = 1
                print("I am currently in the following " + type_of_movement + " positions: ")
                UR3.print_position_from_list(current_position, type_of_movement)

                target_position_list = [None, None, None, None, None, None]
                for i in range(0, 6):
                    if list_of_sp[i] is not None:
                        target_position_list[i] = (list_of_sp[i])
                    else:
                        # None given -> use the current joint position!
                        target_position_list[i] = (current_position[i])

                print("I will move the joints to position= ")
                UR3.print_position_from_list(target_position_list, type_of_movement)
                UR3.list_to_setp(self.setp, target_position_list)

                # changing the mode
                self.con.send(self.mode)
                # sending new setpoint!
                self.con.send(self.setp)

                # input_int_register_0 == 1 --> new command is sent!
                self.watchdog.input_int_register_0 = 1
 
            elif not self.move_completed and state.output_int_register_0 == 0:
                self.move_completed = True
                self.watchdog.input_int_register_0 = 0
                self.con.send(self.watchdog)
                print("I finished the movement, and currently in= ")            
                if type_of_movement == "joint":
                    UR3.print_position_from_list(state.actual_q, type_of_movement)
                else:
                    UR3.print_position_from_list(state.actual_TCP_pose, type_of_movement)
                print("*****END\n")
                return

            # kick watchdog
            self.con.send(self.watchdog)

    def push_button(self, button_is_pushed):
        print( "*****BEGIN - push_button *****")
        self.move_completed = True

        while True:
            state = self.con.receive()
            if state is None:
                print("Recieved state is None, aborting method...")
                break

            if button_is_pushed[0] == 1:
                # self.pushbutton.standard_digital_output_0 = 1
                button_is_pushed[0] = 0

            if self.move_completed and state.output_int_register_0 == 1:
                # output_int_register_0 == 1 --> robot ready to recieve a new command
                self.move_completed = False

                # number of push button mode in the program of the robot!
                self.mode.input_int_register_1 = 2

                print("I am currently in the following TCP positions: ")
                UR3.print_position_from_list(state.actual_TCP_pose, "TCP")

                # changing the mode
                self.con.send(self.mode)

                # input_int_register_0 == 1 --> new command is sent!
                self.watchdog.input_int_register_0 = 1
 
            elif not self.move_completed and state.output_int_register_0 == 0:
                self.move_completed = True
                self.watchdog.input_int_register_0 = 0
                #self.pushbutton.standard_digital_output_0 = 0
                self.con.send(self.watchdog)
                #self.con.send(self.pushbutton)
                print("*****END\n")
                return

            # kick watchdog
            self.con.send(self.watchdog)

    def home(self):
        robot.move_robot("joint", [ self.home_pos_of_joints[0], None, None, None, None, None ])
        robot.move_robot("joint", [ None, self.home_pos_of_joints[1], None, None, None, None ])
        robot.move_robot("joint", [ None, None, self.home_pos_of_joints[2], None, None, None ])
        robot.move_robot("joint", [ None, None, None, self.home_pos_of_joints[3], None, None ])
        robot.move_robot("joint", [ None, None, None, None, self.home_pos_of_joints[4], None ])
        robot.move_robot("joint", [ None, None, None, None, None, self.home_pos_of_joints[5] ])

    def touch_KRP(self):
        state = self.con.receive()
        if state is None:
            print("Recieved state is None, aborting method...")
            return
        # a position to return
        current_position = state.actual_TCP_pose
        robot.move_robot("TCP", self.KRP + [None, None, None])
        robot.move_robot("TCP", current_position)

    def init_myself(self):
        self.home()
        self.touch_KRP()

    # NOTE: this is only for testing!!! final version may be more sofisticated...
    def main_loop(self, input_list, new_data, button_is_pushed):
        while True:
            # Do something with the input_list
            if new_data[0] == 1:
                print("Moving to position= " + str(input_list) + " and pushing a button")
                robot.move_robot("TCP", [input_list[0] + self.KRP[0], input_list[1] + self.KRP[1], input_list[2] + self.KRP[2]] + [None, None, None])
                robot.push_button(button_is_pushed)
                new_data[0] = 0
            else:
                # kick watchdog
                self.con.send(self.watchdog)


# Note: this function emulates the input point of the robot program
def get_user_input(input_list, new_data):
    while True:
        # Read three numbers from the user
        numbers = input("Enter the three coordinates relative to KRP: ").split()
        
        if len(numbers) == 3 and all(n.isdigit() for n in numbers):
            # Update the list with new numbers
            input_list.clear()
            input_list.extend(map(int, numbers))
            for i in range(0, len(input_list)):
                input_list[i] /= 1000
            new_data[0] = 1
        else:
            print("Please enter exactly three numbers.")

# Note: this function should be replaced to one which listens on the serial part for arduino
def create_server_to_listen_pushbutton(button_is_pushed):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))  # Bind to localhost on port 12345
    server_socket.listen(1)  # Allow only one connection at a time

    print("Server is listening for incoming connections...")

    # Accept the connection
    conn, addr = server_socket.accept()
    # print(f"Connected by {addr}")

    while True:
        data = conn.recv(1024)  # Receive up to 1024 bytes of data
        if not data:
            break
        #print(f"Received from client: {data.decode()}")

        button_is_pushed[0] = 1
        # Echo the received message back to the client
        conn.sendall("Got it.".encode())

    conn.close()
    server_socket.close()

    

if __name__ == "__main__":
    
    KRP = [-0.085, -0.250, 0.01]
    # KRP = [130/1000, -430/1000, -390/1000]
    robot = UR3(KRP)
    robot.init_myself()

    input_list = []
    new_data = [0]
    button_is_pushed = [0]

    # Start the server side
    # server_thread = threading.Thread(target=create_server_to_listen_pushbutton, args=(button_is_pushed,))
    # server_thread.daemon = True
    # server_thread.start()

    # Start a thread to get user input
    input_thread = threading.Thread(target=get_user_input, args=(input_list, new_data,))
    input_thread.daemon = True
    input_thread.start()

    # Start the main loop
    robot.main_loop(input_list, new_data, button_is_pushed)


    #robot.move_robot("joint", [ math.radians(-90), None, None, None, None, None ])
    #robot.move_robot("joint", [ None, math.radians(-90), None, None, None, None ])
    #robot.move_robot("joint", [ None, None, math.radians(-130), None, None, None ])
    #robot.move_robot("joint", [ None, None, None, math.radians(-50), None, None ])
    #robot.move_robot("joint", [ None, None, None, None, math.radians(90), None ])
    #robot.move_robot("joint", [ None, None, None, None, None, math.radians(0) ])

    #robot.move_robot("joint", [ 0, 0, 0, 0, 0, 0 ])
    #robot.move_robot("joint", [ math.radians(-90), math.radians(-90), math.radians(-130), math.radians(-50), math.radians(90), math.radians(0)  ])
    #robot.move_robot("TCP", [ None, None, 0.166, None, None, None ])
    #robot.move_robot("TCP", [ None, -0.208, None, None, None, None ])
    #robot.push_button()
    #robot.move_robot("TCP", [ -0.101, None, None, None, None, None ])
    #robot.push_button()
    #robot.move_robot("TCP", [ None, -0.268, None, None, None, None ])
    #robot.push_button()
    #robot.move_robot("TCP", [ -0.151, None, None, None, None, None ])
    #robot.push_button()