from ultralytics import YOLO
import os
import numpy as np
from enum import Enum
#from IPython.display import display, Image
#from IPython import display
#display.clear_output()

class KeyboardOrientation(Enum):
     A = 1
     B = 2

class CoordinateTransformator():
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
print(os.path.isfile(r'neural_networks\best2_1.pt'))
model = YOLO(r"neural_networks\best2_1.pt")

results = model.predict(r'C:\Users\Z004KZJX\Documents\MUNKA\ROBOREVO\ObjectDetection\Images\v2\raw_images\both\c6.jpg', show = True, save=True, imgsz=1472, conf=0.5, show_labels=False)

# stores the midpoints of the detected objects in listst
buttons = []
refs = []

print("\nDetected objects")
print("----------------\n")
for i in range(len(results[0].boxes)):
        objname = results[0].names[int(results[0].boxes.cls[i])]
        confid = results[0].boxes.cpu().numpy().conf[i]
        midpoint = convert_box_corners_to_midpoint( results[0].boxes.cpu().numpy().xyxy[i] )
        
        # position in YOLO format (top-left, bottom-right)
        # more position format: xywh,xywhn; xyxy,xyxyn; I think "n" means normalized
        # check the pixel coordinates with openning of the imgae in paint
        print(f"{objname} {confid:.2f} position: {midpoint}")
        if objname == "button":
            buttons.append( midpoint )
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
    print(f"The midpoint of the {i}. button is {buttons[i]}")

print("")
    
p_xmin = min(buttons, key=lambda x: x[0])
p_xmax = max(buttons, key=lambda x: x[0])

p_ymin = min(buttons, key=lambda x: x[1])
p_ymax = max(buttons, key=lambda x: x[1])
print(f"P_xmin= {p_xmin}, P_xmax = {p_xmax}, P_ymin= {p_ymin}, P_ymax= {p_ymax}")


print("---------- COORDINATE TRANSFORMATION ----------")
orientation = KeyboardOrientation.A

# Note: in the pixel coordinate system, the origo is the upper left corner!!
# TODO: this method is not take into account that the stickers on the keyboard are not in a strict line!
#       it can happen that in certain cases numlock will be P_ymin!!! BE AWARE
#       maybe the stickers should be redone, or more clever method should be implemented to determine the orientation!
#       c6.jpg in C:\Users\Z004KZJX\Documents\MUNKA\ROBOREVO\URSim_shared\RoboRevo\MachineVision\runs\detect\predict13 was used....
if p_ymin[0] > p_ymax[0]:
    print("Case A, so left ctrl is the lowest key!")
    orientation = KeyboardOrientation.A
elif p_ymin[0] < p_ymax[0]:
    print("Case B, so numpad enter is the lowest key!")
    orientation = KeyboardOrientation.B
else:
    print("Exactly horizontal???? No way....")

theta_rad = 0
t = np.array([0, 0])

if orientation == KeyboardOrientation.A:
    theta_rad = - np.arctan( ( p_ymax[0] - p_xmin[0] ) / ( p_ymax[1] - p_xmin[1] ) )
    t = np.array([p_xmin[0], p_xmin[1]])
else:
    theta_rad = np.arctan( ( p_ymin[0] - p_xmin[0] ) / ( p_ymin[1] - p_xmin[1] ) )
    t = np.array([p_ymin[0], p_ymin[1]])

print(f"The rotational angle is= {theta_rad}")
print(f"The translation is= {t}")

transformator = CoordinateTransformator(theta_rad, t[0], t[1])

# Define the point in homogeneous coordinates
point_x, point_y = transformator.transform_point(buttons[0][0], buttons[0][1])
point_x2, point_y2 = transformator.transform_point(p_xmin[0], p_xmin[1])
point_x5, point_y5 = transformator.transform_point(buttons[5][0], buttons[5][1])
point_x6, point_y6 = transformator.transform_point(623, 568)
point_x7, point_y7 = transformator.transform_point(577, 630)

print(f"From point x= {buttons[0][0]}, y= {buttons[0][1]} End result is, x'= {point_x}, y'= {point_y}")
print(f"From point x= {p_xmin[0]}, y= {p_xmin[1]} End result is, x'= {point_x2}, y'= {point_y2}")
print(f"From point x= {buttons[5][0]}, y= {buttons[5][1]} End result is, x'= {point_x5}, y'= {point_y5}")
print(f"From point x= {623}, y= {568} End result is, x'= {point_x6}, y'= {point_y6}")
print(f"From point x= {577}, y= {630} End result is, x'= {point_x7}, y'= {point_y7}")








