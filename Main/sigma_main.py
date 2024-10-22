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
from GPT.gpt import GPT

# TODO: always measure these!!
# KRP is the l button of the keyboard
KRP = [146.5/1000, -262.8/1000, 20/1000]

# replace this parameter by calculating it from the KRP!! So the robots moves always that letter l is kind of in the middle of the pic
CAMERA_POSITION = [KRP[0] - 5/1000, KRP[1] + 17/1000, 195/1000]
KEYBOARD_HEIGHT = 5

def main():
    button_collection = {
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

    # TODO: here should be the source code generator
    chat_bot = GPT("GPT/key.txt")
    string_to_type = chat_bot.request(message) # FIXME: voice recognition result should go here

    path_of_neural_network = Path("../MachineVision/neural_networks/best3_0_small_epoch40.pt")
    button_loc = button_locator(path_of_neural_network, Point(KRP[0] * 1000, KRP[1] * 1000), [1920, 1080], True, False)
    robot = UR3(KRP, CAMERA_POSITION)

    # Start the robot thread
    robot_thread = threading.Thread(target=robot.main_loop, args=(), daemon=True)
    robot_thread.start()

    # robot start procedure
    robot.set_command_state(CommandType.HOME)
    while robot.command_type != CommandType.IDLE:
        pass
    
    robot.set_command_state(CommandType.TOUCH_KRP)
    while robot.command_type != CommandType.IDLE:
        pass

    # taking a pic and determining the button's location
    robot.set_command_state(CommandType.CAMERA)
    while robot.command_type != CommandType.IDLE:
        pass

    camera = Camera(camera_idx=0)
    # path_of_new_image = Path("C:/Users/Z004KZJX/Pictures/Camera Roll/WIN_20241015_08_18_58_Pro.jpg") # TODO: for this image (WIN_20241011_16_38_54_Pro.jpg), position of one of the button has been photod by my phone!!!!

    while True:
        # FIXME: this should be more sophisticated? 
        try:
            path_of_new_image = camera.take_image()
            button_loc.determine_buttons_position_in_TCP_system(path_of_new_image, button_collection)
            break
        except:
            if counter == 5:
                print("It seems that button detection does not work... change the keyboard or camera position or lightning...")
                sys.exit()
            else:
                counter += 1
                print(f"Not successful button detection, let's try it again for the {counter + 1}th time!")


    for c in string_to_type:
        next_coordinates = button_collection[c].distance_from_KRP
    #for index, (button_name, button_properties) in enumerate(button_collection.items()):
        #next_coordinates = button_properties.distance_from_KRP
        #print(f"I will type \"{button_name} its coordinates are= {next_coordinates}\"")
        robot.set_next_position_TCP([-next_coordinates.x / 1000, -next_coordinates.y / 1000, KEYBOARD_HEIGHT /1000])
        robot.set_command_state(CommandType.PUSH_BUTTON_AT)
        while robot.command_type != CommandType.IDLE:
            pass

    print("Finished")


if __name__ == "__main__":
    main()