from ultralytics import YOLO
import os
import numpy as np
from enum import Enum

##########################
# BASIC INFRASTRUCTURE
##########################

# Basic type to store coordinates
class Point:
    def __init__(self, x=0, y=0) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))
    
    def __str__(self):
        return f"(x,y)= {self.x}, {self.y}"

    def __repr__(self):
        return f"(x,y)= {self.x}, {self.y}"

# container class which can be stored in a dictionary
# every keyboard button has a relative distance to the key 0 in the upper left corner
#   eg.: button q is the 2. button in the first row compared to key 0 so its relative distance: (2,1)
# and a distance from the KRP which is the lower left cross on the table.
#   this distance is determined by the module button_locator and used by the robot as a destination coordinate
class Button:
    def __init__(self, rel_from_button0_x, rel_from_button0_y) -> None:
        # relative position of the button to button 0
        self.rel_from_button0_x = rel_from_button0_x
        self.rel_from_button0_y = rel_from_button0_y

        # the position of the button to the ref point (=KRP) in mm
        self.distance_from_KRP = Point()

    def __eq__(self, other):
        return isinstance(other, Button) and self.rel_from_button0_x == other.rel_from_button0_x and self.rel_from_button0_y == other.rel_from_button0_y

    def __hash__(self):
        return hash((self.rel_from_button0_x, self.rel_from_button0_y))
    
    def __str__(self):
        return f"Button: rel pos to 0 (x,y)= {self.rel_from_button0_x}, {self.rel_from_button0_y}"

    def __repr__(self):
        return f"Button: rel pos to 0 (x,y)= {self.rel_from_button0_x}, {self.rel_from_button0_y}"
    



################################
# MODULE SPECIFIC INFRASTRUCTURE
################################

class detected_button:
    def __init__(self, x_to_pic=0, y_to_pic=0, x_to_keyboard=0, y_to_keyboard=0) -> None:
        self.midpoint_rel_to_pic = Point(x_to_pic, y_to_pic)
        self.midpoint_rel_to_keybord = Point(x_to_keyboard, y_to_keyboard)

    def __eq__(self, other):
        return isinstance(other, Point) and self.midpoint_rel_to_pic == other.midpoint_rel_to_pic and self.midpoint_rel_to_keybord == other.midpoint_rel_to_keybord

    def __hash__(self):
        return hash((self.midpoint_rel_to_pic, self.midpoint_rel_to_keybord))
    
    def __str__(self):
        return ( f"My midpoint relative to the upper left corner of the picture: {self.midpoint_rel_to_pic}\n"
                 f" and relative to the upper left corner of the keyboard: {self.midpoint_rel_to_keybord}"
        )

    def __repr__(self):
        return ( f"My midpoint relative to the upper left corner of the picture: {self.midpoint_rel_to_pic}\n"
                 f" and relative to the upper left corner of the keyboard: {self.midpoint_rel_to_keybord}"
        )
    

class keyboard_orientation(Enum):
     A = 1
     B = 2

class coordinate_transformator:
    def __init__(self) -> None:
        self.rotation_matrix = 0
        self.translation_vector = 0

    def set_rotation_matrix(self, theta_rad):
        # Create the inverse rotation matrix (rotate by -theta)
        cos_theta = np.cos(-theta_rad)
        sin_theta = np.sin(-theta_rad)
        self.rotation_matrix = np.array([
            [cos_theta, -sin_theta],
            [sin_theta, cos_theta]
        ])

        print(f"CoordinateTransformator - the inverse rotation matrix is=\n{self.rotation_matrix}\n")

    def set_translation_vector(self, x_of_keyboard_coord_sys, y_of_keyboard_coord_sys ):
        # Define the translation between the two coordinate systems
        # (the coordinate of the second coordinate system compared to the first one)
        self.translation_vector = np.array([x_of_keyboard_coord_sys, y_of_keyboard_coord_sys])

        print(f"CoordinateTransformator - the translation is=\n{self.translation_vector}\n")


    def transform_point(self, x, y) -> Point:
        # Translate point by subtracting the origin of B in A
        translated_point = (x - self.translation_vector[0], y - self.translation_vector[1])

        # Convert the translated point to a column vector
        translated_point_vector = np.array(translated_point).reshape(2, 1)
        
        # Apply the rotation matrix and convert the resulting vector to a tuple
        point_in_new_coord_system_tuple = tuple( (np.dot(self.rotation_matrix, translated_point_vector)).flatten() )
        
        # Convert the tuple to a vector and return it
        return Point(point_in_new_coord_system_tuple[0], point_in_new_coord_system_tuple[1])
    



################################
# THE MODULE
################################