from ultralytics import YOLO
import os
import numpy as np
from enum import Enum
from pathlib import Path
import math

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
        return f"(x,y)= {self.x} {self.y}"

    def __repr__(self):
        return f"(x,y)= {self.x} {self.y}"

# container class which can be stored in a dictionary
# every keyboard button has a relative distance to the key 0 in the upper left corner
#   eg.: button q is the 2. button in the first row compared to key 0 so its relative distance: (2,1)
# and a distance from the KRP which is the lower left cross on the table.
#   this distance is determined by the module button_locator and used by the robot as a destination coordinate
class Button:
    def __init__(self, rel_from_button0_x, rel_from_button0_y) -> None:
        # relative position of the button to button 0 (unit: -)
        self.rel_from_button0_x = rel_from_button0_x
        self.rel_from_button0_y = rel_from_button0_y

        # the position of the button to the ref point (=KRP) in mm
        self.distance_from_KRP = Point()

        # on which pixel is the button's midpoint
        self.pixel_pos_on_pic = Point()

    def __eq__(self, other):
        return isinstance(other, Button) and self.rel_from_button0_x == other.rel_from_button0_x and self.rel_from_button0_y == other.rel_from_button0_y

    def __hash__(self):
        return hash((self.rel_from_button0_x, self.rel_from_button0_y))
    
    def __str__(self):
        return f"   Button: rel pos to 0 (x,y)= {self.rel_from_button0_x} {self.rel_from_button0_y}"

    def __repr__(self):
        return f"   Button: rel pos to 0 (x,y)= {self.rel_from_button0_x} {self.rel_from_button0_y}"
    



################################
# MODULE SPECIFIC INFRASTRUCTURE
################################

class KeyboardOrientation(Enum):
     A = 1
     B = 2

class detected_button:
    def __init__(self, x_to_pic=0, y_to_pic=0, x_to_keyboard=0, y_to_keyboard=0) -> None:
        # the unit of these two point are pixels!
        self.midpoint_rel_to_pic = Point(x_to_pic, y_to_pic)
        self.midpoint_rel_to_keyboard = Point(x_to_keyboard, y_to_keyboard)

    def __eq__(self, other):
        return isinstance(other, Point) and self.midpoint_rel_to_pic == other.midpoint_rel_to_pic and self.midpoint_rel_to_keyboard == other.midpoint_rel_to_keybord

    def __hash__(self):
        return hash((self.midpoint_rel_to_pic, self.midpoint_rel_to_keyboard))
    
    def __str__(self):
        return ( f"     My midpoint relative to the upper left corner of the picture in pixels: {self.midpoint_rel_to_pic}\n"
                 f"     and relative to the upper left corner of the keyboard in pixels: {self.midpoint_rel_to_keyboard}"
        )

    def __repr__(self):
        return ( f"     My midpoint relative to the upper left corner of the picture in pixels: {self.midpoint_rel_to_pic}\n"
                 f"     and relative to the upper left corner of the keyboard in pixels: {self.midpoint_rel_to_keyboard}"
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
    def __init__(self, path_of_pt_file: Path, position_of_KRP_rel_to_robot: Point, image_resolution: list, verbose_mode = False, test_mode = False) -> None:
        self.model = YOLO(path_of_pt_file)
        self.coord_trafo = coordinate_transformator()

        self.image_resolution = image_resolution

        # determined based on the resolution of the image, the distance between the camera and the keyboard and the DFOV of the camera!
        self.mm_per_pixel_ratio = 0.32795

        # KRP is letter L
        self.position_of_KRP_rel_to_robot = position_of_KRP_rel_to_robot

        # Containers of detected objects
        self.detected_references: list[Point] = []
        self.detected_buttons: list[detected_button] = []
        self.detected_buttons_in_rows: list[list[detected_button]] = []

        self.verbose_mode = verbose_mode
        # In this mode the distance to KRP is not determined, but the relative distance to key0 in mm and it is printed out
        self.test_mode = test_mode

    def determine_buttons_position_in_TCP_system(self, image_path, target_dictionary: dict[str, Button]):
        self._reset_my_containers()

        # 1. using YOLO to detect all the objects (buttons and references) on the captured picture
        results = self.model.predict(image_path, show = True, save=True, imgsz=720, conf=0.5, show_labels=False)
        
        # 2. separates the detected object into member variables detected_references and detected_buttons
        self._sort_detected_objects_to_lists(results)

        # 3. determine the necessary coordinate transformation to be able to convert the coordinates of the midpoints
        #    into a coordinate system which is determined by the 4 reference stickers on the keyboard 
        self._refresh_coordinate_transformator()

        # 4. determine all the coordinates of the buttons relative to the keyboard coordinate system
        self._determine_button_coordinates_relative_to_keyboard()

        # 5. organise the buttons into the 5 rows of the keyboard itself. After this, we will be able to tell, that
        #    the pixel midpoint coordinates of a certain button belongs to which row and in the row to which index on the keyboard
        #    eg.: in row 2 the third button has pixel coordinates (604,423) in the coordinate system determined by the picture
        self._organize_detected_to_buttons_into_rows()
        
        # 6. The target dictionary should contains the relative positions of the buttons to eachother. Based on that we can determine
        #    the position of every button compared to the KRP (which is the left reference cross)
        #    eg.: button s is (120, 80) mm in KRP system
        if not self.test_mode:
            self._determine_button_pos_in_KRP_into_dict(target_dictionary)
        else:
            self.__determine_button_pos_compared_to_button0(445, 125, target_dictionary)

    def _sort_detected_objects_to_lists(self, results):
        if self.verbose_mode:
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
            if self.verbose_mode:
                print(f"{objname} {confid:.2f} position: {midpoint}")

            if objname == "button":
                self.detected_buttons.append( detected_button(midpoint.x, midpoint.y))
            elif objname == "ref":
                self.detected_references.append( midpoint )
            else:
                print("NOT DEFINED OBJECT THROW AN EXCEPTION HERE.....")
        
        if len(self.detected_buttons) != 90:
            print("ERROR: NUMBER OF DETECTED BUTTONS DOES NOT MATCH UP!!!")
            print(f"There should be 90 buttons, instead we have {len(self.detected_buttons)}")
            # print(f"There should be 2 references, instead we have {len(self.detected_references)}")
            raise ValueError("Not all of the/too many buttons has been captured!")
        else:
            if self.verbose_mode:
                print("---------- REFS ----------")
                for i in range( len(self.detected_references) ):
                    print(f"The midpoint of the {i}. ref is {self.detected_references[i]}")

                print("")

                print("---------- BUTTONS ----------")
                for i in range( len(self.detected_buttons) ):
                    print(f"The midpoint of the {i}. button is {self.detected_buttons[i]}")

        if self.verbose_mode:
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
        if self.verbose_mode:
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
        upper_right_corner = min(buttons_sorted_based_on_x[-2:], key=lambda x: x.midpoint_rel_to_pic.y)

        #lower_right_corner = max(buttons_sorted_based_on_x[-2:], key=lambda x: x.midpoint_rel_to_pic.y)
        #lower_left_corner = max(buttons_sorted_based_on_x[:2], key=lambda x: x.midpoint_rel_to_pic.y)
        if self.verbose_mode:
            print(f"upper_left_corner= {upper_left_corner}, \nupper_right_corner= {upper_right_corner}")
            #print(f"lower_left_corner = {lower_left_corner}, \nlower_right_corner= {lower_right_corner}")

        orientation = KeyboardOrientation.A

        # Note: in the pixel coordinate system, the origo is the upper left corner!!
        if upper_right_corner.midpoint_rel_to_pic.y > upper_left_corner.midpoint_rel_to_pic.y:
            if self.verbose_mode:
                print("Case A, so left ctrl is the lowest key!")
            orientation = KeyboardOrientation.A
        elif upper_right_corner.midpoint_rel_to_pic.y < upper_left_corner.midpoint_rel_to_pic.y:
            if self.verbose_mode:
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

        if self.verbose_mode:
            print(f"The rotational angle is= {theta_rad}")
            print(f"The translation is= {t}")

        self.coord_trafo.set_rotation_matrix(theta_rad)
        self.coord_trafo.set_translation_vector(t[0], t[1])

        if self.verbose_mode:
            print("\n-------------------------------")
            print("END: Refresh the coordinate transformator")
            print("-------------------------------\n")

    def _determine_button_coordinates_relative_to_keyboard(self):
        if self.verbose_mode:
            print("\n--------------------------------------------------------------")
            print("BEGIN: Determine button position in keyboard coordinate system")
            print("--------------------------------------------------------------\n")

        for i in range( len(self.detected_buttons) ):
            midpoint_compared_to_0 = self.coord_trafo.transform_point(self.detected_buttons[i].midpoint_rel_to_pic.x, self.detected_buttons[i].midpoint_rel_to_pic.y)
            self.detected_buttons[i].midpoint_rel_to_keyboard.x = midpoint_compared_to_0.x
            self.detected_buttons[i].midpoint_rel_to_keyboard.y = midpoint_compared_to_0.y

            if self.verbose_mode:
                print(f"The midpoint of the {i}. button on the picture= {self.detected_buttons[i].midpoint_rel_to_pic} relativ to upper left ref= {self.detected_buttons[i].midpoint_rel_to_keyboard}")

        if self.verbose_mode:
            print("\n--------------------------------------------------------------")
            print("END: Determine button position in keyboard coordinate system")
            print("--------------------------------------------------------------\n")

    def _organize_detected_to_buttons_into_rows(self):
        if self.verbose_mode:
            print("\n--------------------------------------------------------------")
            print("BEGIN: Organizing the detected buttons into rows")
            print("--------------------------------------------------------------\n")
        self.detected_buttons = sorted(self.detected_buttons, key=lambda x: x.midpoint_rel_to_keyboard.y)

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

        if self.verbose_mode:
            for i in range( len(self.detected_buttons_in_rows) ):
                print(f"---------- ROW {i}.----------")
                for j in range( len(self.detected_buttons_in_rows[i]) ):
                    print(self.detected_buttons_in_rows[i][j])

        if self.verbose_mode:
            print("\n--------------------------------------------------------------")
            print("END: Organizing the detected buttons into rows")
            print("--------------------------------------------------------------\n")

    def _determine_one_row_based_on_indexes(self, first_index_of_row_element, last_index_of_row_element, empty_target_list):
        current_row = self.detected_buttons[first_index_of_row_element:last_index_of_row_element+1]

        # we sort the row based on midpoint_to0_x, so we got exactly the row order!
        current_row_sorted = sorted(current_row, key=lambda x: x.midpoint_rel_to_keyboard.x)

        # fill the results to the target list
        for i in range( len(current_row_sorted) ):
            empty_target_list.append(current_row_sorted[i])

    def _load_pixel_data_of_detected_buttons_into_dict(self, target_dictionary: dict[str, Button]):
        if self.verbose_mode:
            print("\n--------------------------------------------------------------")
            print("BEGIN: Loading the detected buttons to the buttons of the keyboard")
            print("--------------------------------------------------------------\n")

        for index, (button_name, button_properties) in enumerate(target_dictionary.items()):
            button_properties.pixel_pos_on_pic = self.detected_buttons_in_rows[button_properties.rel_from_button0_y][button_properties.rel_from_button0_x].midpoint_rel_to_pic

            if self.verbose_mode:
                print(f"{button_name} pixels on picture is= {button_properties.pixel_pos_on_pic}")

        if self.verbose_mode:
            print("\n--------------------------------------------------------------")
            print("END: Loading the detected buttons to the buttons of the keyboard")
            print("--------------------------------------------------------------\n")

    def _calculate_x_distance_compensation(self, x_position):
        # return ( 0.0137 * x_position - 12.47 )
        return 0
    
    def _calculate_y_distance_compensation(self, x_position, y_position):
        # return ( ( -0.0133 * y_position + 7.4536 ) + ( 0.0013 * x_position - 1.3247 ) )
        return 0

    def _determine_button_pos_in_KRP_into_dict(self, target_dictionary: dict[str, Button]):
        if self.verbose_mode:
            print("\n--------------------------------------------------------------")
            print("BEGIN: Determining the buttons position in KRP")
            print("--------------------------------------------------------------\n")

        self._load_pixel_data_of_detected_buttons_into_dict(target_dictionary)

        midpoint_of_image = Point(abs(self.image_resolution[0]) / 2, abs(self.image_resolution[1]) / 2)

        # determining KRP, which is letter "l" now
        KRP_mm_distance_from_midpoint_of_pic_x = self.mm_per_pixel_ratio * ( target_dictionary["l"].pixel_pos_on_pic.x - midpoint_of_image.x ) - self._calculate_x_distance_compensation(target_dictionary["l"].pixel_pos_on_pic.x)
        KRP_mm_distance_from_midpoint_of_pic_y = -1 * ( self.mm_per_pixel_ratio * ( target_dictionary["l"].pixel_pos_on_pic.y - midpoint_of_image.y ) - self._calculate_y_distance_compensation(target_dictionary["l"].pixel_pos_on_pic.x, target_dictionary["l"].pixel_pos_on_pic.y) )

        if self.verbose_mode:
            print(f"The pixel midpoint of the image= {midpoint_of_image}")
            print(f"mm_per_pixel_coeff= {self.mm_per_pixel_ratio}")
            print(f"KRP (button l) distance from the midpoint of image (mm)= {KRP_mm_distance_from_midpoint_of_pic_x} {KRP_mm_distance_from_midpoint_of_pic_y}")

        for index, (button_name, button_properties) in enumerate(target_dictionary.items()):
            button_pixel_distance_from_midpoint_of_pic_x = target_dictionary[button_name].pixel_pos_on_pic.x - midpoint_of_image.x
            button_pixel_distance_from_midpoint_of_pic_y = -1 * ( target_dictionary[button_name].pixel_pos_on_pic.y - midpoint_of_image.y )
            button_mm_distance_from_midpoint_of_pic_x = self.mm_per_pixel_ratio * button_pixel_distance_from_midpoint_of_pic_x - self._calculate_x_distance_compensation(button_properties.pixel_pos_on_pic.x)
            button_mm_distance_from_midpoint_of_pic_y = self.mm_per_pixel_ratio * button_pixel_distance_from_midpoint_of_pic_y - self._calculate_y_distance_compensation(button_properties.pixel_pos_on_pic.x, button_properties.pixel_pos_on_pic.y)

            # TODO: is another coordinate trafo needed? probably not if the picutre is well alligned with the robot's coordinate system
            # transformed_distance_from_KRP_in_pixels = self.coord_trafo.transform_point(pixel_distance_from_KRP_x, - pixel_distance_from_KRP_y)

            button_properties.distance_from_KRP.x = button_mm_distance_from_midpoint_of_pic_x - KRP_mm_distance_from_midpoint_of_pic_x
            button_properties.distance_from_KRP.y = button_mm_distance_from_midpoint_of_pic_y - KRP_mm_distance_from_midpoint_of_pic_y

            if self.verbose_mode and button_name != "Enter" and button_name != "NumpadAdd" and button_name != "CapsLock" and button_name != "a" and button_name != "Shift" and button_name != "ii" and button_name != "y" and button_name != "NumpadEnter" and button_name != "Control":
                print(f"{button_name} pixels on picture is= {target_dictionary[button_name].pixel_pos_on_pic} distance from KRP is= {button_properties.distance_from_KRP}")

        if self.verbose_mode:
            print("\n--------------------------------------------------------------")
            print("END: Determining the buttons position in KRP")
            print("--------------------------------------------------------------\n")

    def _reset_my_containers(self):
        # Reseting the containers of detected objects
        self.detected_references: list[Point] = []
        self.detected_buttons: list[detected_button] = []
        self.detected_buttons_in_rows: list[list[detected_button]] = []

        # FIXME: probably it is not the most efficient way to clear totally all of the containers at the beginning of every cycle...
        #        but whatever, it is easier this way :)
    
    # ONLY FOR TESTING
    def __determine_button_pos_compared_to_button0(self, measured_w, measured_h, target_dictionary: dict[str, Button]):
        print("\n--------------------------------------------------------------")
        print("BEGIN TEST: Determining the buttons position compared to 0")
        print("--------------------------------------------------------------\n")
        buttons_sorted_based_on_x = sorted(self.detected_buttons, key=lambda x: x.midpoint_rel_to_pic.x)
        upper_left_corner = min(buttons_sorted_based_on_x[:2], key=lambda x: x.midpoint_rel_to_pic.y)
        lower_left_corner = max(buttons_sorted_based_on_x[:2], key=lambda x: x.midpoint_rel_to_pic.y)

        upper_right_corner = min(buttons_sorted_based_on_x[-2:], key=lambda x: x.midpoint_rel_to_pic.y)
        lower_right_corner = max(buttons_sorted_based_on_x[-2:], key=lambda x: x.midpoint_rel_to_pic.y)
        if self.verbose_mode:
            print(f"upper_left_corner= {upper_left_corner}, \nlower_left_corner = {lower_left_corner}, \nupper_right_corner= {upper_right_corner}, \nlower_right_corner= {lower_right_corner}")

        w_coeff = measured_w / (upper_right_corner.midpoint_rel_to_keyboard.x - upper_left_corner.midpoint_rel_to_keyboard.x)
        h_coeff = measured_h / (lower_left_corner.midpoint_rel_to_keyboard.y - upper_left_corner.midpoint_rel_to_keyboard.y)

        key0 = self.detected_buttons_in_rows[0][0]

        for index, (button_name, button_properties) in enumerate(target_dictionary.items()):
            pixel_position_of_current_key_rel_to_keyboard_x = self.detected_buttons_in_rows[button_properties.rel_from_button0_y][button_properties.rel_from_button0_x].midpoint_rel_to_keyboard.x
            pixel_position_of_current_key_rel_to_keyboard_y = self.detected_buttons_in_rows[button_properties.rel_from_button0_y][button_properties.rel_from_button0_x].midpoint_rel_to_keyboard.y

            pixel_distance_from_key0_x = pixel_position_of_current_key_rel_to_keyboard_x - key0.midpoint_rel_to_keyboard.x
            pixel_distance_from_key0_y = pixel_position_of_current_key_rel_to_keyboard_y - key0.midpoint_rel_to_keyboard.y

            relative_distance_from_key0_x = pixel_distance_from_key0_x * w_coeff
            relative_distance_from_key0_y= pixel_distance_from_key0_y * h_coeff
            if self.verbose_mode:
                pixel_position_of_current_key_x = self.detected_buttons_in_rows[button_properties.rel_from_button0_y][button_properties.rel_from_button0_x].midpoint_rel_to_pic.x
                pixel_position_of_current_key_y = self.detected_buttons_in_rows[button_properties.rel_from_button0_y][button_properties.rel_from_button0_x].midpoint_rel_to_pic.y
                print(f"{button_name} distance from key 0 is (x,y)= {relative_distance_from_key0_x} , {relative_distance_from_key0_y} on pixels (x,y) = {pixel_position_of_current_key_x}, {pixel_position_of_current_key_y} ")
            else:
                print(f"{button_name} {relative_distance_from_key0_x} {relative_distance_from_key0_y}")

        print("\n--------------------------------------------------------------")
        print("END TEST: Determining the buttons position compared to 0")
        print("--------------------------------------------------------------\n")


if __name__ == "__main__":
    print(os.getcwd())
    os.chdir(r'C:\Users\Z004KZJX\Documents\MUNKA\ROBOREVO\URSim_shared\RoboRevo\MachineVision')
    print(os.getcwd())

    # this dictionary will be on the main level
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

    path_of_neural_network = Path("neural_networks/best3_0_small_epoch40.pt")
    #path_of_image1 = Path("C:/Users/Z004KZJX/Documents/MUNKA/ROBOREVO/INPUTS/ObjectDetection_input/Images/v3/raw_images3/to_test/IMG_4223.jpg")
    #path_of_image2 = Path("C:/Users/Z004KZJX/Documents/MUNKA/ROBOREVO/INPUTS/ObjectDetection_input/Images/v3/raw_images3/to_test/IMG_4224.jpg")
    #path_of_image3 = Path("C:/Users/Z004KZJX/Documents/MUNKA/ROBOREVO/INPUTS/ObjectDetection_input/Images/v3/raw_images3/to_test/3.jpg")
    path_of_image4 = Path("C:/Users/Z004KZJX/Documents/MUNKA/ROBOREVO/URSim_shared/RoboRevo/Main/CameraOutput/opencv_frame_2024-10-16_17-35-19-Copy.png")
    path_of_image5 = Path("C:/Users/Z004KZJX/Pictures/Camera Roll/WIN_20241011_16_38_54_Pro.jpg")
    path_of_image6 = Path("C:/Users/Z004KZJX/Documents/MUNKA/ROBOREVO/URSim_shared/RoboRevo/Main/CameraOutput/opencv_frame_2024-10-16_17-50-14-Copy.png") # should produce error!

    # the real numbers at the test were: 492 227
    button_locator = button_locator(path_of_neural_network, Point(141.87, -268.29), [1920, 1080], True, False)

    try:
        #button_locator.determine_buttons_position_in_TCP_system(path_of_image1, button_collection)
        #button_locator.determine_buttons_position_in_TCP_system(path_of_image2, button_collection)
        #button_locator.determine_buttons_position_in_TCP_system(path_of_image3, button_collection)
        #button_locator.determine_buttons_position_in_TCP_system(path_of_image4, button_collection)
        #button_locator.determine_buttons_position_in_TCP_system(path_of_image5, button_collection)
        button_locator.determine_buttons_position_in_TCP_system(path_of_image6, button_collection)
    except:
        print("Exception catched")