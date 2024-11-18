import sys
import os
import math
import threading
import socket
import time
from enum import Enum
import copy
from pathlib import Path

if __name__ == "__main__":
    sys.path.append("..")
    from rtde import rtde as rtde
    from rtde import rtde_config as rtde_config
else:
    from ..rtde import rtde as rtde
    from ..rtde import rtde_config as rtde_config

class CommandType(Enum):
    IDLE = 0
    HOME = 1
    MOVE_GENERAL = 2
    PUSH_BUTTON_AT = 3
    NOD = 4
    LISTENING = 5
    NOPE = 6

class UR3:
    def __init__(self):
        self.home_pos_of_joints = [ math.radians(90), math.radians(-90), math.radians(65), math.radians(-65), math.radians(-90), math.radians(0)  ]

        # the keyboard reference point in the base coordinate system of the robot, has to be measured by the robot before startup!
        # NOTE: KRP and camera pos have been extended by the rotation coordinates, might cause error!
        # self.KRP = [ KRP[0], KRP[1], KRP[2] ] + [-0.0, 3.14159, -0.0] 
        # self.camera_pos_in_TCP = [ camera_pos[0], camera_pos[1], camera_pos[2] ] + [-0.0, 3.14159, -0.0]

        self.command_type = CommandType.IDLE
        self.next_position_TCP = []
        self.next_position_joint = []

        # self.ROBOT_HOST = "192.168.56.101" # FOR SIMULATION
        self.ROBOT_HOST = "192.168.0.125" # FOR REAL
        self.ROBOT_PORT = 30004

        script_dir = Path(__file__).parent
        self.config_filename = script_dir / "control_loop_configuration.xml"

        self.conf = rtde_config.ConfigFile(str(self.config_filename))
        state_names, state_types = self.conf.get_recipe("state")
        setp_names, setp_types = self.conf.get_recipe("setp")
        mode_names, mode_types = self.conf.get_recipe("mode")
        watchdog_names, watchdog_types = self.conf.get_recipe("watchdog")

        self.con = rtde.RTDE(self.ROBOT_HOST, self.ROBOT_PORT)
        print("----------------------------------------------\n")
        print("Trying to connect to IP= " + str(self.ROBOT_HOST) + " PORT= " + str(self.ROBOT_PORT) )
        self.con.connect()
        print("Connection is successful!")
        print("\n----------------------------------------------\n\n")

        # setup recipes
        self.con.send_output_setup(state_names, state_types)
        self.setp = self.con.send_input_setup(setp_names, setp_types)
        self.mode = self.con.send_input_setup(mode_names, mode_types)
        self.watchdog = self.con.send_input_setup(watchdog_names, watchdog_types)

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

    def set_command_state(self, new_command_state: CommandType):
        self.command_type = new_command_state

    # input unit should be m!!
    def set_next_position_TCP(self, new_position: list):
        self.next_position_TCP = copy.deepcopy(new_position)
        for i in range(len(self.next_position_TCP), 6):
            self.next_position_TCP.append(None)

        print(f"My new next TCP position is (unit= m)= {self.next_position_TCP}")

    def set_next_position_joint(self, new_position: list):
        self.next_position_joint = copy.deepcopy(new_position)
        for i in range(len(self.next_position_joint), 6):
            self.next_position_joint.append(None)

        print(f"My new next joint position is= {self.next_position_joint}")
    
    # returned in m
    def get_current_TCP_position(self):
        state = self.con.receive()
        if state is None:
            print("Recieved state is None, aborting method...")
            return None
        current_TCP_pos = state.actual_TCP_pose

        print(f"My current TCP position is= {current_TCP_pos}")
        return current_TCP_pos

    def main_loop(self):
        while True:
            match self.command_type:
                case CommandType.IDLE:
                    state = self.con.receive()
                    if state is None:
                        print("Recieved state is None, trying to reconnect...")
                        self.con.connect()
                    else:
                        self.con.send(self.watchdog)
                    #time.sleep(0.1) # to avoid the overflow of the robot's receiving buffer?
                case CommandType.HOME:
                    print("Send the robot home")
                    self._move_to_home()
                    self.command_type = CommandType.IDLE
                case CommandType.MOVE_GENERAL:
                    print("Moving to position= " + str(self.next_position_TCP))
                    self._move_robot("TCP", self.next_position_TCP)
                    self.command_type = CommandType.IDLE
                case CommandType.PUSH_BUTTON_AT:
                    print("Moving to position= " + str(self.next_position_TCP) + " and pushing a button")
                    self._move_robot("TCP", self.next_position_TCP)
                    self._push_button()
                    self.command_type = CommandType.IDLE
                case CommandType.NOD:
                    print("Nodding")
                    self._nod()
                    self.command_type = CommandType.IDLE
                case CommandType.LISTENING:
                    print("Send the robot to listening mode")
                    self._move_to_listening_pos()
                    self.command_type = CommandType.IDLE
                case CommandType.NOPE:
                    print("Head-shaking")
                    self._head_shake()
                    self.command_type = CommandType.IDLE

    def _move_to_home(self):
        self._move_robot("joint", self.home_pos_of_joints)

    def _move_to_listening_pos(self):
        self._move_robot("joint", [ math.radians(180), math.radians(-90), math.radians(25), math.radians(-120), math.radians(-90), math.radians(0) ])

    # Move the robot to a given coordinate in TCP coordinate system or based on the joint positions
    def _move_robot(self, type_of_movement, list_of_sp):
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
                        # None given -> use the current position!
                        target_position_list[i] = (current_position[i])

                print("I will move the joints to position= ")
                UR3.print_position_from_list(target_position_list, type_of_movement)
                UR3.list_to_setp(self.setp, target_position_list)

                # changing the movement mode
                self._send_movement_mode_to_robot()
                # sending new setpoint!
                self._send_setp_to_robot()

                # input_int_register_0 == 1 --> new command is sent!
                self.watchdog.input_int_register_0 = 1
                self._send_sync_flag_to_robot()
 
            elif not self.move_completed and state.output_int_register_0 == 0:
                self.move_completed = True
                self.watchdog.input_int_register_0 = 0
                self._send_sync_flag_to_robot()
                print("I finished the movement, and currently in= ")            
                if type_of_movement == "joint":
                    UR3.print_position_from_list(state.actual_q, type_of_movement)
                else:
                    UR3.print_position_from_list(state.actual_TCP_pose, type_of_movement)
                print("*****END\n")
                return

            # kick watchdog
            self.con.send(self.watchdog)

    def _push_button(self):
        print( "*****BEGIN - push_button *****")
        self._execute_general_movement_mode( 2 )

    def _nod(self):
        print( "*****BEGIN - NOD WITH HEAD *****")
        self._execute_general_movement_mode( 3 )

    def _head_shake(self):
        print( "*****BEGIN - HEAD SHAKE *****")
        self._execute_general_movement_mode( 4 )


    def _execute_general_movement_mode(self, movement_mode : int):
        self.move_completed = True

        while True:
            state = self.con.receive()
            if state is None:
                print("Recieved state is None, aborting method...")
                break

            if self.move_completed and state.output_int_register_0 == 1:
                # output_int_register_0 == 1 --> robot ready to recieve a new command
                self.move_completed = False

                self.mode.input_int_register_1 = movement_mode

                print("I am currently in the following TCP positions: ")
                UR3.print_position_from_list(state.actual_TCP_pose, "TCP")

                # changing the movement mode
                self._send_movement_mode_to_robot()

                # input_int_register_0 == 1 --> new command is sent!
                self.watchdog.input_int_register_0 = 1
                self._send_sync_flag_to_robot()
 
            elif not self.move_completed and state.output_int_register_0 == 0:
                self.move_completed = True
                self.watchdog.input_int_register_0 = 0
                self._send_sync_flag_to_robot()
                print("*****END\n")
                return

            # kick watchdog
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

    def _send_movement_mode_to_robot(self):
        while True:
            self.con.send(self.mode)
            time.sleep(5/1000)
            state = self.con.receive()

            target_value = self.mode.input_int_register_1
            actual_value = state.input_int_register_1

            if target_value == actual_value:
                break
            else:
                # print("Target value is= " + str(target_value) + " but input_int_register_1 is= " + str(actual_value) )
                pass

    def _send_sync_flag_to_robot(self):
        while True:
            self.con.send(self.watchdog)
            time.sleep(5/1000)
            state = self.con.receive()

            target_value = self.watchdog.input_int_register_0
            actual_value = state.input_int_register_0

            if target_value == actual_value:
                break
            else:
                # print("Target value is= " + str(target_value) + " but input_int_register_0 is= " + str(actual_value) )
                pass

    def _send_setp_to_robot(self):
        while True:
            self.con.send(self.setp)
            time.sleep(5/1000)
            state = self.con.receive()

            register_has_been_updated = True
            
            for i in range(0, 6):
                target_value = self.setp.__dict__["input_double_register_%i" % i]
                actual_value = state.__dict__["input_double_register_%i" % i]
                if abs(target_value - actual_value) > 1e-4:
                    # print("Target value is= " + str(target_value) + " but input_double_register_" + str(i) + " is= " + str(actual_value))
                    register_has_been_updated = False
                    break

            if register_has_been_updated:
                break


# Note: this function emulates the input point of the robot program
def get_user_input(input_list, new_data):
    while True:
        # Read three numbers from the user
        numbers = input("Enter the three coordinates relative to KRP: ").split()
        
        if len(numbers) == 3 and all(n.lstrip('-').isdigit() for n in numbers):
            # Update the list with new numbers
            input_list.clear()
            input_list.extend(map(int, numbers))
            for i in range(0, len(input_list)):
                input_list[i] /= 1000
            new_data[0] = 1
        else:
            print("Please enter exactly three numbers.")
    

if __name__ == "__main__":
    
    # KRP = [-0.085, -0.250, 0.01] + [-0.0, 3.14159, -0.0] # for simulation purpose
    # KRP = [115/1000, -420/1000, 25/1000] + [-0.0, 3.14159, -0.0] # first working version in real life
    KRP = [368/1000, -250/1000, 3/1000] + [-0.0, 3.14159, -0.0] # This is how it will probably look like in final version
    camera_position = [132/1000, -310/1000, 195/1000] + [-0.0, 3.14159, -0.0]
    robot = UR3()
    # Start the robot thread
    robot_thread = threading.Thread(target=robot.main_loop, args=())
    robot_thread.daemon = True
    robot_thread.start()

    robot.set_command_state(CommandType.HOME)
    while robot.command_type != CommandType.IDLE:
        pass
    
    # TOUCHING KRP:
    robot.set_next_position_TCP(KRP)
    robot.set_command_state(CommandType.MOVE_GENERAL)
    while robot.command_type != CommandType.IDLE:
        pass

    #robot.set_command_state(CommandType.CAMERA)
    #while robot.command_type != CommandType.IDLE:
    #    pass
    

    input_list = []
    new_data = [0]

    # Start a thread to get user input
    input_thread = threading.Thread(target=get_user_input, args=(input_list, new_data,))
    input_thread.daemon = True
    input_thread.start()

    # Start the main loop
    while True:
        if new_data[0] == 1 and robot.command_type == CommandType.IDLE:
            for i in range(3):
                input_list[i] += KRP[i]

            robot.set_next_position_TCP(input_list)
            robot.set_command_state(CommandType.MOVE_GENERAL)
            new_data[0] = 0
        
        