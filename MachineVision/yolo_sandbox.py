from ultralytics import YOLO
import os
import numpy as np
from enum import Enum

keys = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", 
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", 
    "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", 
    "u", "v", "w", "x", "y", "z", 
    "Tab", "CapsLock", "Shift", "Control", "Windows", "Alt", "Space",
    "AltGr", "fn", "ControlR", "ShiftR",  "Enter", 
    "Backspace", "Insert", "Delete", "Home", "End", "PageUp", "PageDown", 
    "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", 
    "oe", "ue", "oo", "oee", "uu", "ae", "aa", "uee", ",", ".", "-", # oe = ö, ue = ü.... 
    "NumLock", "Numpad0", "Numpad1", "Numpad2", "Numpad3", "Numpad4", 
    "Numpad5", "Numpad6", "Numpad7", "Numpad8", "Numpad9", "NumpadDel", 
    "NumpadAdd", "NumpadSubtract", "NumpadMultiply", "NumpadDivide", "NumpadEnter"
]

class Button:
    def __init__(self, rel_from_0_x, rel_from_0_y) -> None:
        # relative position of the button to button 0
        self.rel_from_0_x = rel_from_0_x
        self.rel_from_0_y = rel_from_0_y

        # the position of the button in pixels on the current image
        self.pixels_from_0_x = 0
        self.pixels_from_0_y = 0

        # the position of the button to the ref point in mm
        self.x = 0
        self.y = 0

    def __eq__(self, other):
        return isinstance(other, Button) and self.rel_from_0_x == other.rel_from_0_x and self.rel_from_0_y == other.rel_from_0_y

    def __hash__(self):
        return hash((self.rel_from_0_x, self.rel_from_0_y))
    
    def __str__(self):
        return f"Button: rel pos to 0 (x,y)= {self.rel_from_0_x}, {self.rel_from_0_y}"

    def __repr__(self):
        return f"Button: rel pos to 0 (x,y)= {self.rel_from_0_x}, {self.rel_from_0_y}"

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
    "ArrowDown": Button(7, 4), "ArrowLeft": Button(8, 4), "ArrowRight": Button(9, 4), "Numpad0": Button(10, 4), "NumpadDel": Button(11, 4)
}

#print(button_collection)

class KeyboardOrientation(Enum):
     A = 1
     B = 2

class CoordinateTransformator:
    def __init__(self, theta_rad, x_of_origin_button, y_of_origin_button):
        # Create the inverse rotation matrix (rotate by -theta)
        cos_theta = np.cos(-theta_rad)
        sin_theta = np.sin(-theta_rad)
        self.rotation_matrix = np.array([
            [cos_theta, -sin_theta],
            [sin_theta, cos_theta]
        ])

        # Define the translation between the two coordinate systems
        # (the coordinate of the second coordinate system compared to the first one)
        self.t = np.array([x_of_origin_button, y_of_origin_button])

        print(f"CoordinateTransformator - the inverse rotation matrix is=\n{self.rotation_matrix}\n")
        print(f"CoordinateTransformator - the translation is=\n{self.t}\n")

    def transform_point(self, x, y):
        # Translate point by subtracting the origin of B in A
        translated_point = (x - self.t[0], y - self.t[1])

        # Convert the translated point to a column vector
        translated_point_vector = np.array(translated_point).reshape(2, 1)
        
        # Apply the rotation matrix
        point_B_vector = np.dot(self.rotation_matrix, translated_point_vector)
        
        # Flatten the resulting vector and return as a tuple
        return tuple(point_B_vector.flatten())

def convert_box_corners_to_midpoint(yolo_result):
        #print(f"The corners in yolo format= {yolo_result}")

        midpoint = []

        midpoint.append( (yolo_result[0] + yolo_result[2]) / 2 )
        midpoint.append( (yolo_result[1] + yolo_result[3]) / 2 )

        #print(f"The midpoint xy format= {midpoint}")

        return midpoint

os.chdir(r'C:\Users\Z004KZJX\Documents\MUNKA\ROBOREVO\URSim_shared\RoboRevo\MachineVision')
print(os.getcwd())
print(os.path.isfile(r'neural_networks\best3_0_small_epoch40.pt'))
model = YOLO(r"neural_networks\best3_0_small_epoch40.pt")

results = model.predict(r'C:\Users\Z004KZJX\Documents\MUNKA\ROBOREVO\INPUTS\ObjectDetection_input\Images\v3\raw_images3\to_test\IMG_4223.jpg', show = True, save=True, imgsz=720, conf=0.5, show_labels=False)

# stores the midpoints of the detected objects in listst
# buttons looks like this: [[midpoint_pixel_x, midpoint_pixel_y],[midpoint_to0_x, midpoint_to0_y]]
buttons = []
refs = []

print("\nDetected objects")
print("----------------\n")
button_index = 0
for i in range(len(results[0].boxes)):
    objname = results[0].names[int(results[0].boxes.cls[i])]
    confid = results[0].boxes.cpu().numpy().conf[i]
    midpoint = convert_box_corners_to_midpoint( results[0].boxes.cpu().numpy().xyxy[i] )
    
    # position in YOLO format (top-left, bottom-right)
    # more position format: xywh,xywhn; xyxy,xyxyn; I think "n" means normalized
    # check the pixel coordinates with openning of the imgae in paint
    print(f"{objname} {confid:.2f} position: {midpoint}")
    if objname == "button":
        buttons.append( list() )
        buttons[button_index].append( midpoint )
        print(f"PROBA= {buttons[button_index]}")
        button_index += 1
    elif objname == "ref":
        refs.append( midpoint )
    else:
        print("NOT DEFINED OBJECT THROW AN EXCEPTION HERE.....")
print("")

print("---------- REFS ----------")
for i in range( len(refs) ):
    print(f"The midpoint of the {i}. ref is {refs[i]}")

print("")

print("---------- BUTTONS ----------")
for i in range( len(buttons) ):
    print(f"The midpoint of the {i}. button is {buttons[i][0]}")

print("")

# FIXME: this is not a good method to determine the orientation.....   
# p_xmin = min(buttons, key=lambda x: x[0][0])[0]
# p_xmax = max(buttons, key=lambda x: x[0][0])[0]

# p_ymin = min(buttons, key=lambda x: x[0][1])[0]
# p_ymax = max(buttons, key=lambda x: x[0][1])[0]
# print(f"P_xmin= {p_xmin}, P_xmax = {p_xmax}, P_ymin= {p_ymin}, P_ymax= {p_ymax}")

# FIXME: for this method, keyboard should be quite horizontal. Find a better way to determine the orientation
buttons_sorted_based_on_x = sorted(buttons, key=lambda x: x[0][0]) 
upper_left_corner = min(buttons_sorted_based_on_x[:2], key=lambda x: x[0][1])[0]
lower_left_corner = max(buttons_sorted_based_on_x[:2], key=lambda x: x[0][1])[0]

upper_right_corner = min(buttons_sorted_based_on_x[-2:], key=lambda x: x[0][1])[0]
lower_right_corner = max(buttons_sorted_based_on_x[-2:], key=lambda x: x[0][1])[0]
print(f"upper_left_corner= {upper_left_corner}, lower_left_corner = {lower_left_corner}, upper_right_corner= {upper_right_corner}, lower_right_corner= {lower_right_corner}")

print("---------- COORDINATE TRANSFORMATION ----------")
orientation = KeyboardOrientation.A

# Note: in the pixel coordinate system, the origo is the upper left corner!!
# TODO: this method is not take into account that the stickers on the keyboard are not in a strict line!
#       it can happen that in certain cases numlock will be P_ymin!!! BE AWARE
#       maybe the stickers should be redone, or more clever method should be implemented to determine the orientation!
#       c6.jpg in C:\Users\Z004KZJX\Documents\MUNKA\ROBOREVO\URSim_shared\RoboRevo\MachineVision\runs\detect\predict13 was used....
if upper_right_corner[1] > upper_left_corner[1]:
    print("Case A, so left ctrl is the lowest key!")
    orientation = KeyboardOrientation.A
elif upper_right_corner[1] < upper_left_corner[1]:
    print("Case B, so numpad enter is the lowest key!")
    orientation = KeyboardOrientation.B
else:
    print("Exactly horizontal???? No way....")

theta_rad = 0
t = np.array([0, 0])

if orientation == KeyboardOrientation.A:
    # Note: the first method uses the vector between 0 and left control, not so precise
    # theta_rad = - np.arctan( ( p_ymax[0] - p_xmin[0] ) / ( p_ymax[1] - p_xmin[1] ) )
    # Note: this method uses the vector between 0 and NumPad subtraction --> much better!
    theta_rad = - np.arctan( ( upper_left_corner[1] - upper_right_corner[1] ) / ( upper_right_corner[0] - upper_left_corner[0] ) )
    t = np.array([upper_left_corner[0], upper_left_corner[1]])
else:
    # Note: the first method uses the vector between 0 and left control, not so precise
    # theta_rad = np.arctan( ( p_ymin[0] - p_xmin[0] ) / ( p_ymin[1] - p_xmin[1] ) )
    theta_rad = np.arctan( ( upper_right_corner[1] - upper_left_corner[1] ) / ( upper_right_corner[0] - upper_left_corner[0] ) )
    t = np.array([upper_left_corner[0], upper_left_corner[1]])

print(f"The rotational angle is= {theta_rad}")
print(f"The translation is= {t}")

transformator = CoordinateTransformator(theta_rad, t[0], t[1])

# Define the point in homogeneous coordinates
#point_x, point_y = transformator.transform_point(buttons[0][0][0], buttons[0][0][1])
#point_x2, point_y2 = transformator.transform_point(p_xmin[0], p_xmin[1])
#point_x5, point_y5 = transformator.transform_point(buttons[5][0][0], buttons[5][0][1])
#point_x6, point_y6 = transformator.transform_point(623, 568)
#point_x7, point_y7 = transformator.transform_point(577, 630)
#print(f"From point x= {buttons[0][0][0]}, y= {buttons[0][0][1]} End result is, x'= {point_x}, y'= {point_y}")
#print(f"From point x= {p_xmin[0]}, y= {p_xmin[1]} End result is, x'= {point_x2}, y'= {point_y2}")
#print(f"From point x= {buttons[5][0][0]}, y= {buttons[5][0][1]} End result is, x'= {point_x5}, y'= {point_y5}")
#print(f"From point x= {623}, y= {568} End result is, x'= {point_x6}, y'= {point_y6}")
#print(f"From point x= {577}, y= {630} End result is, x'= {point_x7}, y'= {point_y7}")

print("---------- BUTTONS MIDPOINT COMPARED TO UPPER LEFT REF ----------")
for i in range( len(buttons) ):
    midpoint_compared_to_0 = list( transformator.transform_point(buttons[i][0][0], buttons[i][0][1]) )
    buttons[i].append( midpoint_compared_to_0 )
    #buttons[i][1].append( midpoint_compared_to_0 )

for i in range( len(buttons) ):
    print(f"The midpoint of the {i}. button on the picture= {buttons[i][0]} relativ to upper left ref= {buttons[i][1]}")


print("---------- DETERMINING THE ROWS OF BUTTONS ----------")

# In one row, every button is 
def determine_row(first_index_of_row_element, last_index_of_row_element, buttons, empty_target_list):
    # buttons looks like this: [[midpoint_pixel_x, midpoint_pixel_y],[midpoint_to0_x, midpoint_to0_y]]
    # so first we sort based on the midpoint_to0_y --> rows in ascending order
    #print(f"PROBA= {buttons[0]}")
    #print(f"PROBA= {buttons[0][0]}")
    #print(f"PROBA= {buttons[0][0][0]}")
    #print(f"PROBA= {buttons[0][0][1]}")
    #print(f"PROBA= {buttons[0][1]}")
    #print(f"PROBA= {buttons[0][1][0]}")
    #print(f"PROBA= {buttons[0][1][1]}")
    buttons_rows_sorted = sorted(buttons, key=lambda x: x[1][1])
    current_row = buttons_rows_sorted[first_index_of_row_element:last_index_of_row_element+1]

    # we sort the row based on midpoint_to0_x, so we got exactly the row order!
    current_row_sorted = sorted(current_row, key=lambda x: x[1][0])

    # fill the results to the target list
    for i in range( len(current_row_sorted) ):
        empty_target_list.append(current_row_sorted[i])


rows = []

for i in range(5):
    rows.append(list())

# 21 elements in the first row
determine_row(2, 22, buttons, rows[0])
# 21 elements in the second row
determine_row(23, 43, buttons, rows[1])
# 16 elements in the third row
determine_row(44, 59, buttons, rows[2])
# 18 elements in the fourth row
determine_row(60, 77, buttons, rows[3])
# 12 elements in the fifth row
determine_row(78, 89, buttons, rows[4])

for i in range( len(rows) ):
    print(f"---------- ROW {i}.----------")
    for j in range( len(rows[i]) ):
        print(rows[i][j])

print("---------- DETERMINING WHICH BUTTON IS WHICH POINT ----------")

for index, (button_name, button_properties) in enumerate(button_collection.items()):
    button_properties.pixels_from_0_x = rows[button_properties.rel_from_0_y][button_properties.rel_from_0_x][0][0]
    button_properties.pixels_from_0_y = rows[button_properties.rel_from_0_y][button_properties.rel_from_0_x][0][1]
    print(f"{button_name} is on pixels x= {button_properties.pixels_from_0_x}, y= {button_properties.pixels_from_0_y}")







