import sys
import os
from pathlib import Path
import threading

print(os.getcwd())
sys.path.append("..")
print(os.getcwd())

from UR3.UR3_module.sigma_ur3_module import UR3
from UR3.UR3_module.sigma_ur3_module import CommandType
from MachineVision.sigma_machine_vision_module import button_locator
from MachineVision.sigma_machine_vision_module import Button
from MachineVision.sigma_machine_vision_module import Point
from MachineVision.camera import Camera

from tkinter import messagebox

KEYBOARD_HEIGHT = 5

class robot_developer:
    def __init__(self, KRP: list, camera_position: list):
        self.KRP = KRP
        self.camera_pos = camera_position
        
        self.button_collection = {
            # First row
            "0": Button(0, 0), "1": Button(1, 0), "2": Button(2, 0), "3": Button(3, 0), "4": Button(4, 0), "5": Button(5, 0),
            "6": Button(6, 0), "7": Button(7, 0), "8": Button(8, 0), "9": Button(9, 0), "oe": Button(10, 0), "ue": Button(11, 0), "oo": Button(12, 0),
            "Backspace": Button(13, 0), "Insert": Button(14, 0), "Home": Button(15, 0), "PageUp": Button(16, 0), "NumLock": Button(17, 0),
            "NumpadDivide": Button(18, 0), "NumpadMultiply": Button(19, 0), "NumpadSubtract": Button(20, 0),
            # Second row
            "Tab": Button(0, 1), "q": Button(1, 1), "w": Button(2, 1), "e": Button(3, 1), "r": Button(4, 1), "t": Button(5, 1), "z": Button(6, 1),
            "u": Button(7, 1), "i": Button(8, 1), "o": Button(9, 1), "p": Button(10, 1), "oee": Button(11, 1), "uu": Button(12, 1), "Enter": Button(13, 1),
            "Delete": Button(14, 1), "End": Button(15, 1), "PageDown": Button(16, 1), "Numpad7": Button(17, 1), "Numpad8": Button(18, 1), "Numpad9": Button(19, 1), 
            "NumpadAdd": Button(20, 1),
            # Third row
            "CapsLock": Button(0, 2), "a": Button(1, 2), "s": Button(2, 2), "d": Button(3, 2), "f": Button(4, 2), "g": Button(5, 2), "h": Button(6, 2),
            "j": Button(7, 2), "k": Button(8, 2), "l": Button(9, 2), "ae": Button(10, 2), "aa": Button(11, 2), "uee": Button(12, 2), "Numpad4": Button(13, 2),
            "Numpad5": Button(14, 2), "Numpad6": Button(15, 2),
            # Fourth row
            "Shift": Button(0, 3), "ii": Button(1, 3), "y": Button(2, 3), "x": Button(3, 3), "c": Button(4, 3), "v": Button(5, 3), "b": Button(6, 3),
            "n": Button(7, 3), "m": Button(8, 3), ",": Button(9, 3), ".": Button(10, 3), "-": Button(11, 3), "ShiftR": Button(12, 3), "ArrowUp": Button(13, 3),
            "Numpad1": Button(14, 3), "Numpad2": Button(15, 3), "Numpad3": Button(16, 3), "NumpadEnter": Button(17, 3),
            # Fifth row
            "Control": Button(0, 4), "Windows": Button(1, 4), "Alt": Button(2, 4), "Space": Button(3, 4), "AltGr": Button(4, 4), "fn": Button(5, 4), "ControlR": Button(6, 4),
            "ArrowLeft": Button(7, 4), "ArrowDown": Button(8, 4), "ArrowRight": Button(9, 4), "Numpad0": Button(10, 4), "NumpadDel": Button(11, 4)
        }

        # result of the chatgpt
        self.current_code_to_type = ""
        # a string which has been modified based on the mapping of the keyboard
        self.current_code_to_type_after_parsing = ""

        # Creating the button locator
        path_of_neural_network = Path("../MachineVision/neural_networks/best3_0_small_epoch40.pt")
        self.button_loc = button_locator(path_of_neural_network, Point(self.KRP[0] * 1000, self.KRP[1] * 1000), [1920, 1080], True, False)

        # Creating the robot
        self.robot = UR3(self.KRP, self.camera_pos)
        # Start the robot thread
        self.robot_thread = threading.Thread(target=self.robot.main_loop, args=())
        self.robot_thread.daemon = True
        self.robot_thread.start()

        # Creating the camera
        self.camera = Camera( camera_idx=0 )

        messagebox.showinfo("Info", "Please start the program on the UR3 robot!")

    def send_home(self):
        self.robot.set_command_state(CommandType.HOME)
        while self.robot.command_type != CommandType.IDLE:
            pass

    def touch_KRP(self):
        self.robot.set_command_state(CommandType.TOUCH_KRP)
        while self.robot.command_type != CommandType.IDLE:
            pass

    def send_camera_position(self):
        self.robot.set_command_state(CommandType.CAMERA)
        while self.robot.command_type != CommandType.IDLE:
            pass

    def update_krp_on_current_position(self):
        self.KRP = self.robot.set_KRP_linear_coordinates_by_current_pos()

    def update_cam_pos_on_current_position(self):
        self.camera_pos = self.robot.set_camera_pos_linear_coordinates_by_current_pos()

    def move_relative_to_current_pos(self, direction: str, magnitude: int):
        # FIXME: what is the dimension?? mm or m?
        next_position = self.robot.get_current_TCP_position()

        # we are expecting the current TCP position in a 6D vector
        if next_position is None or len(next_position) != 6:
            return
        else:
            if direction == "x":
                next_position[0] += magnitude / 1000
            elif direction == "y":
                next_position[1] += magnitude / 1000
            elif direction == "z":
                next_position[2] += magnitude / 1000
            else:
                return

            self.robot.set_next_position_TCP( next_position )
            self.robot.set_command_state(CommandType.MOVE_GENERAL)
            while self.robot.command_type != CommandType.IDLE:
                pass

    def listen_the_instruction(self) -> bool:
        print(f"MOCK MAINCLASS - I AM LISTENING THE INSTRUCTION")
        return True
    
    def get_the_instruction_from_CL(self) -> bool:
        print(f"Please enter the text which the robot will type:")
        self.current_code_to_type = input()
        print(f"I WILL TYPE: {self.current_code_to_type}")
        return True
    
    def type_the_code(self) -> bool:
        result_of_button_locator = self._determine_current_button_position()

        if not result_of_button_locator:
            return False
        
        for i in range (0, len(self.current_code_to_type_after_parsing)):
            next_coordinates = self.button_collection[self.current_code_to_type_after_parsing[i]].distance_from_KRP
        #for index, (button_name, button_properties) in enumerate(button_collection.items()):
            #next_coordinates = button_properties.distance_from_KRP
            #print(f"I will type \"{button_name} its coordinates are= {next_coordinates}\"")
            self.robot.set_next_position_TCP([-next_coordinates.x / 1000, -next_coordinates.y / 1000, KEYBOARD_HEIGHT /1000])
            self.robot.set_command_state(CommandType.PUSH_BUTTON_AT)
            while self.robot.command_type != CommandType.IDLE:
                pass

        return True

    def get_krp(self) -> list:
        return self.KRP
    
    def get_camera_pos(self) -> list:
        return self.camera_pos

    def _determine_current_button_position(self) -> bool:
        for i in range(5):
            # FIXME: this should be more sophisticated? 
            try:
                path_of_new_image = self.camera.take_image()
                self.button_loc.determine_buttons_position_in_TCP_system(path_of_new_image, self.button_collection)
                return True
            except:
                print(f"Not successful button detection, let's try it again for the {i + 2}. time!")
        
        return False