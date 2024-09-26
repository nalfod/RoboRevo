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
        return f"   Button: rel pos to 0 (x,y)= {self.rel_from_button0_x}, {self.rel_from_button0_y}"

    def __repr__(self):
        return f"   Button: rel pos to 0 (x,y)= {self.rel_from_button0_x}, {self.rel_from_button0_y}"
    



################################
# MODULE SPECIFIC INFRASTRUCTURE
################################

class KeyboardOrientation(Enum):
     A = 1
     B = 2

class detected_button:
    def __init__(self, x_to_pic=0, y_to_pic=0, x_to_keyboard=0, y_to_keyboard=0) -> None:
        self.midpoint_rel_to_pic = Point(x_to_pic, y_to_pic)
        self.midpoint_rel_to_keybord = Point(x_to_keyboard, y_to_keyboard)

    def __eq__(self, other):
        return isinstance(other, Point) and self.midpoint_rel_to_pic == other.midpoint_rel_to_pic and self.midpoint_rel_to_keybord == other.midpoint_rel_to_keybord

    def __hash__(self):
        return hash((self.midpoint_rel_to_pic, self.midpoint_rel_to_keybord))
    
    def __str__(self):
        return ( f"     My midpoint relative to the upper left corner of the picture: {self.midpoint_rel_to_pic}\n"
                 f"     and relative to the upper left corner of the keyboard: {self.midpoint_rel_to_keybord}"
        )

    def __repr__(self):
        return ( f"     My midpoint relative to the upper left corner of the picture: {self.midpoint_rel_to_pic}\n"
                 f"     and relative to the upper left corner of the keyboard: {self.midpoint_rel_to_keybord}"
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

        print(f"    CoordinateTransformator - the inverse rotation matrix is=\n{self.rotation_matrix}\n")

    def set_translation_vector(self, x_of_keyboard_coord_sys, y_of_keyboard_coord_sys ):
        # Define the translation between the two coordinate systems
        # (the coordinate of the second coordinate system compared to the first one)
        self.translation_vector = np.array([x_of_keyboard_coord_sys, y_of_keyboard_coord_sys])

        print(f"    CoordinateTransformator - the translation is=\n{self.translation_vector}\n")


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

class button_locator:
    def __init__(self, path_of_pt_file, refs_width_in_mm, refs_height_in_mm):
        self.model = YOLO(path_of_pt_file)
        self.coord_trafo = coordinate_transformator()

        # real life distance of the two crosses, have to be measured manually!
        self.refs_width_in_mm = refs_width_in_mm
        self.refs_height_in_mm = refs_height_in_mm

        # Containers of detected objects
        self.detected_references: list[Point] = []
        self.detected_buttons: list[detected_button] = []
        self.detected_buttons_in_rows: list[list[detected_button]] = []

    def determine_buttons_position_in_TCP_system(self, image_path, target_dictionary):
        self._reset_myself()

        results = self.model.predict(image_path, show = True, save=True, imgsz=720, conf=0.5, show_labels=False)
        
        self._sort_detected_objects_to_lists(results)

        self._refresh_coordinate_transformator()

        self._determine_button_coordinates_relative_to_keyboard()

        self._organize_detected_to_buttons_into_rows()
        
        self._determine_button_pos_in_KRP_into_dict(target_dictionary)

    def _sort_detected_objects_to_lists(self, results):
        print("\n-------------------------------")
        print("BEGIN: Sorting detected objects")
        print("-------------------------------\n")
        for i in range(len(results[0].boxes)):
            objname = results[0].names[int(results[0].boxes.cls[i])]
            confid = results[0].boxes.cpu().numpy().conf[i]
            midpoint = self._convert_box_corners_to_midpoint( results[0].boxes.cpu().numpy().xyxy[i] )
            
            # position in YOLO format (top-left, bottom-right)
            # more position format: xywh,xywhn; xyxy,xyxyn; I think "n" means normalized
            # check the pixel coordinates with openning of the image in paint
            print(f"{objname} {confid:.2f} position: {midpoint}")
            if objname == "button":
                self.detected_buttons.append( detected_button(midpoint.x, midpoint.y))
            elif objname == "ref":
                self.detected_references.append( midpoint )
            else:
                print("NOT DEFINED OBJECT THROW AN EXCEPTION HERE.....")
        
        if len(self.detected_buttons) != 92 and len(self.detected_references) != 2:
            print("ERROR: NUMBER OF DETECTED OBJECTS DOES NOT MATCH UP!!!")
            print(f"There should be 92 buttons, instead we have {len(self.detected_buttons)}")
            print(f"There should be 2 references, instead we have {len(self.detected_references)}")
            # TODO: throw an exception here and catch it in the main block
        else:
            print("---------- REFS ----------")
            for i in range( len(self.detected_references) ):
                print(f"The midpoint of the {i}. ref is {self.detected_references[i]}")

            print("")

            print("---------- BUTTONS ----------")
            for i in range( len(self.detected_buttons) ):
                print(f"The midpoint of the {i}. button is {self.detected_buttons[i]}")

        print("\n-------------------------------")
        print("END: Sorting detected objects")
        print("-------------------------------\n")

    def _convert_box_corners_to_midpoint(self, detected_box_corners) -> Point:
        #print(f"The corners in yolo format= {yolo_result}")

        midpoint = Point()

        midpoint.x = ( (detected_box_corners[0] + detected_box_corners[2]) / 2 )
        midpoint.y = ( (detected_box_corners[1] + detected_box_corners[3]) / 2 )

        #print(f"The midpoint xy format= {midpoint}")

        return midpoint
    
    def _refresh_coordinate_transformator(self) -> None:
        print("\n-------------------------------")
        print("BEGIN: Refresh the coordinate transformator")
        print("-------------------------------\n")
        # FIXME: for this method, keyboard should be quite horizontal. Insted this, implement the following solution:
        #        determine the distance in case of every button pairs, and the four ref points will be the ones 
        #        which belongs to the two longest distances

        # Buttons are sorted based on the x coordinates in the picture. In this row, the first two one will be the
        # references on the keyboard on left, the last two one will be the references on the right
        buttons_sorted_based_on_x = sorted(self.detected_buttons, key=lambda x: x.midpoint_rel_to_pic.x)
        upper_left_corner = min(buttons_sorted_based_on_x[:2], key=lambda x: x.midpoint_rel_to_pic.y)
        lower_left_corner = max(buttons_sorted_based_on_x[:2], key=lambda x: x.midpoint_rel_to_pic.y)

        upper_right_corner = min(buttons_sorted_based_on_x[-2:], key=lambda x: x.midpoint_rel_to_pic.y)
        lower_right_corner = max(buttons_sorted_based_on_x[-2:], key=lambda x: x.midpoint_rel_to_pic.y)
        print(f"upper_left_corner= {upper_left_corner}, lower_left_corner = {lower_left_corner}, upper_right_corner= {upper_right_corner}, lower_right_corner= {lower_right_corner}")

        orientation = KeyboardOrientation.A

        # Note: in the pixel coordinate system, the origo is the upper left corner!!
        if upper_right_corner.midpoint_rel_to_pic.y > upper_left_corner.midpoint_rel_to_pic.y:
            print("Case A, so left ctrl is the lowest key!")
            orientation = KeyboardOrientation.A
        elif upper_right_corner.midpoint_rel_to_pic.y < upper_left_corner.midpoint_rel_to_pic.y:
            print("Case B, so numpad enter is the lowest key!")
            orientation = KeyboardOrientation.B
        else:
            print("Exactly horizontal???? No way.... :)")

        theta_rad = 0
        if orientation == KeyboardOrientation.A:
            theta_rad = - np.arctan( ( upper_left_corner.midpoint_rel_to_pic.y - upper_right_corner.midpoint_rel_to_pic.y ) / ( upper_right_corner.midpoint_rel_to_pic.x - upper_left_corner.midpoint_rel_to_pic.x ) )
            
        else:
            theta_rad = np.arctan( ( upper_right_corner.midpoint_rel_to_pic.y - upper_left_corner.midpoint_rel_to_pic.y ) / ( upper_right_corner.midpoint_rel_to_pic.x - upper_left_corner.midpoint_rel_to_pic.x ) )

        t = np.array([upper_left_corner.midpoint_rel_to_pic.x, upper_left_corner.midpoint_rel_to_pic.y])

        print(f"The rotational angle is= {theta_rad}")
        print(f"The translation is= {t}")

        self.coord_trafo.set_rotation_matrix(theta_rad)
        self.coord_trafo.set_translation_vector(t[0], t[1])
        print("\n-------------------------------")
        print("END: Refresh the coordinate transformator")
        print("-------------------------------\n")

    def _determine_button_coordinates_relative_to_keyboard(self):
        print("\n--------------------------------------------------------------")
        print("BEGIN: Determine button position in keyboard coordinate system")
        print("--------------------------------------------------------------\n")

        for i in range( len(self.detected_buttons) ):
            midpoint_compared_to_0 = self.coord_trafo.transform_point(self.detected_buttons[i].midpoint_rel_to_pic.x, self.detected_buttons[i].midpoint_rel_to_pic.y)
            self.detected_buttons[i].midpoint_rel_to_keybord.x = midpoint_compared_to_0.x
            self.detected_buttons[i].midpoint_rel_to_keybord.y = midpoint_compared_to_0.y

            print(f"The midpoint of the {i}. button on the picture= {self.detected_buttons[i].midpoint_rel_to_pic} relativ to upper left ref= {self.detected_buttons[i].midpoint_compared_to_0}")

        print("\n--------------------------------------------------------------")
        print("END: Determine button position in keyboard coordinate system")
        print("--------------------------------------------------------------\n")

    def _organize_detected_to_buttons_into_rows(self):
        print("\n--------------------------------------------------------------")
        print("BEGIN: Organizing the detected buttons into rows")
        print("--------------------------------------------------------------\n")
        self.detected_buttons = sorted(self.detected_buttons, key=lambda x: x.midpoint_rel_to_keybord.y)

        for i in range(5):
            self.detected_buttons_in_rows.append(list())

        # BEWARE: first to elements would be the two references on the upper side of the keyboard
        # 21 elements in the first row
        self._determine_one_row_based_on_indexes(2, 22, self.detected_buttons_in_rows[0])
        # 21 elements in the second row
        self._determine_one_row_based_on_indexes(23, 43, self.detected_buttons_in_rows[1])
        # 16 elements in the third row
        self._determine_one_row_based_on_indexes(44, 59, self.detected_buttons_in_rows[2])
        # 18 elements in the fourth row
        self._determine_one_row_based_on_indexes(60, 77, self.detected_buttons_in_rows[3])
        # 12 elements in the fifth row
        self._determine_one_row_based_on_indexes(78, 89, self.detected_buttons_in_rows[4])

        for i in range( len(self.detected_buttons_in_rows) ):
            print(f"---------- ROW {i}.----------")
            for j in range( len(self.detected_buttons_in_rows[i]) ):
                print(self.detected_buttons_in_rows[i][j])

        print("\n--------------------------------------------------------------")
        print("END: Organizing the detected buttons into rows")
        print("--------------------------------------------------------------\n")

    def _determine_one_row_based_on_indexes(self, first_index_of_row_element, last_index_of_row_element, empty_target_list):
        current_row = self.detected_buttons[first_index_of_row_element:last_index_of_row_element+1]

        # we sort the row based on midpoint_to0_x, so we got exactly the row order!
        current_row_sorted = sorted(current_row, key=lambda x: x.midpoint_rel_to_keybord.x)

        # fill the results to the target list
        for i in range( len(current_row_sorted) ):
            empty_target_list.append(current_row_sorted[i])

    def _determine_button_pos_in_KRP_into_dict(self, target_dictionary):
        pass