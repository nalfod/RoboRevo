import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

##################
# MOCK ROBOT WITH CAMERA CLASS 
##################

class robot_with_camera_mock:
    def __init__(self):
        self.KRP = [0, 0, 0, 0, 0, 0]
        self.camera_pos = [0, 0, 500, 0, 0, 0]
        pass

    def send_home(self):
        print("MOCK MAINCLASS - I SEND MYSELF TO HOME")

    def touch_KRP(self):
        print("MOCK MAINCLASS - I SEND MYSELF TO KRP")

    def send_camera_position(self):
        print("MOCK MAINCLASS - I SEND MYSELF TO CAMERA POSITION")

    def update_krp_on_current_position(self):
        print("MOCK MAINCLASS - MY KRP HAS BEEN UPDATED")

    def update_cam_pos_on_current_position(self):
        print("MOCK MAINCLASS - MY CAMERA POSITION HAS BEEN UPDATED")

    def generate_code_based_on_input(self, input: str):
        print(f"MOCK MAINCLASS - I WILL GENERATE CODE BASED ON {input}")

    def get_krp(self) -> list:
        return self.KRP
    
    def get_camera_pos(self) -> list:
        return self.camera_pos

##################
# POPUPS
##################

class pop_up(tk.Toplevel):
    def __init__(self, parent, title: str, message: str):
        if isinstance(parent, tk.Tk):
            super().__init__(parent)
        else:
            #print("My master is not tk.Tk object")
            super().__init__(parent.master)
        self.title(title)
        self.geometry("400x150")

        self.result = None

        current_row = 0
        label = tk.Label(self, text=message)
        label.grid(row=current_row, column=0, sticky="e", padx=5, pady=5, columnspan= 4 )

        current_row = self.add_camera_position_adjusting_buttons()

        proceed_button = tk.Button(self, text="Proceed", command=lambda: self.on_proceed())
        proceed_button.grid(row=current_row, column=0, columnspan=1, pady=10, padx=10, sticky="nsew")

        cancel_button = tk.Button(self, text="Cancel", command=lambda: self.on_cancel())
        cancel_button.grid(row=current_row, column=2, columnspan=1, pady=10, padx=10, sticky="nsew")

        self.grab_set()  # Block input to the parent window until this one is closed
        self.transient(parent)  # Keep popup on top of the parent window
        self.wait_window(self)  # Wait until the popup window is closed

    def add_camera_position_adjusting_buttons(self, current_row):
        # virtual function
        return current_row + 1

    def on_proceed(self):
        self.result = True
        self.destroy()

    def on_cancel(self):
        self.result = False
        self.destroy()

class pop_up_camera(pop_up):
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent, title, message)

        self.adjusting_in_progress = True

        self.move_button_is_pressed = False
        self.direction_of_movement = None
        self.magnitude_of_movement = None

    def add_camera_position_adjusting_buttons(self, current_row):
        current_row += 1

        label = tk.Label(self, text="Movement direction (x or y):")
        label.grid(row=current_row, column=0, sticky="e", padx=5, pady=5)
        self.movement_direction_entry = tk.Entry(self)
        self.movement_direction_entry.grid(row=current_row, column=1, sticky="w", padx=5, pady=5)
        self.movement_direction_entry.delete(0, tk.END)  # Clear the current contents

        current_row += 1

        label = tk.Label(self, text="Movement magnitude [mm]:")
        label.grid(row=current_row, column=0, sticky="e", padx=5, pady=5)
        self.movement_magnitude_entry = tk.Entry(self)
        self.movement_magnitude_entry.grid(row=current_row, column=1, sticky="w", padx=5, pady=5)
        self.movement_magnitude_entry.delete(0, tk.END)  # Clear the current contents

        current_row += 1

        self.move_button = tk.Button(self, text="MOVE", command=lambda: self.send_move_command)
        self.move_button.grid(row=current_row, column=0, columnspan=4, pady=10, sticky="w")

        current_row += 1

    def send_move_command(self):
        tmp_direction = self.movement_direction_entry.get()
        if not (tmp_direction == "x" or tmp_direction == "y"):
            messagebox.showerror("Error", "Direction should be either 'x' or 'y'!")
            return
        
        tmp_magnitude = self.movement_magnitude_entry.get()

        try:
            tmp_magnitude_int = int(tmp_magnitude)
        except:
            messagebox.showerror("Error", "Please give me a number")
            return

        self.direction_of_movement = tmp_direction
        self.magnitude_of_movement = tmp_magnitude
        self.move_button_is_pressed = True

    def on_proceed(self):
        self.adjusting_in_progress = False
        super().on_proceed()

    def on_cancel(self):
        self.adjusting_in_progress = False
        super().on_cancel()




##################
# MAIN_GUI
##################
class MainApp(tk.Tk):
    def __init__(self, robot_with_camera):
        super().__init__()
        self.title("Robot developer")
        self.geometry("400x200")

        self.robot_with_camera = robot_with_camera

        self.robot_positions_labels = []

        number_of_rows = 0
        # Yearly data widgets:
        label1 = tk.Label(self, text="KRP:")
        label1.grid(row=number_of_rows, column=0, sticky="e", padx=5, pady=5)
        label2 = tk.Label(self, text=self.robot_with_camera.get_krp())
        label2.grid(row=number_of_rows, column=1, sticky="e", padx=5, pady=5)
        self.robot_positions_labels.append(label2)
        
        number_of_rows += 1
        label3 = tk.Label(self, text="Camera_position:")
        label3.grid(row=number_of_rows, column=0, sticky="e", padx=5, pady=5)
        label4 = tk.Label(self, text=self.robot_with_camera.get_camera_pos())
        label4.grid(row=number_of_rows, column=1, sticky="e", padx=5, pady=5)
        self.robot_positions_labels.append(label4)


        number_of_rows += 1
        send_home_button = tk.Button(self, text="Send home", command=self.robot_with_camera.send_home)
        send_home_button.grid(row=number_of_rows, column=0, sticky="e", padx=5, pady=5)

        touch_krp_button = tk.Button(self, text="Touch KRP", command=self.robot_with_camera.touch_KRP)
        touch_krp_button.grid(row=number_of_rows, column=1, sticky="e", padx=5, pady=5)

        touch_krp_button = tk.Button(self, text="Go to camera pos", command=self.robot_with_camera.send_camera_position)
        touch_krp_button.grid(row=number_of_rows, column=2, sticky="e", padx=5, pady=5)

        number_of_rows += 1

        send_home_button = tk.Button(self, text="Set new KRP", command=self.set_new_krp)
        send_home_button.grid(row=number_of_rows, column=0, sticky="e", padx=5, pady=5)

        touch_krp_button = tk.Button(self, text="Set new camera_position", command=self.set_new_camera_position)
        touch_krp_button.grid(row=number_of_rows, column=1, sticky="e", padx=5, pady=5)

        number_of_rows += 1

        touch_krp_button = tk.Button(self, text="TYPE CODE", command=self.type_code)
        touch_krp_button.grid(row=number_of_rows, column=0, sticky="e", padx=5, pady=5)

    def set_new_krp(self):
        conf_window = pop_up(self, "Attention", "This will change the KRP, do you want to proceed?")

        if conf_window.result is not True:
            return
        
        krp_setting_window = pop_up(self, "Set new KRP", "Move the tool of the robot to touch\nthe midpoint of letter 'l',\nand press 'Proceed' if it is there!")

        if krp_setting_window.result is not True:
            return
        else:
            self.robot_with_camera.update_krp_on_current_position()

    def set_new_camera_position(self):
        conf_window = pop_up(self, "Attention", "This will change the camera position, do you want to proceed?")

        if conf_window.result is not True:
            return
        
        krp_setting_window = pop_up(self, "Set new KRP", "Move the tool of the robot to touch the midpoint of letter 'l', and press 'Proceed' if it is there!")

        # NOT READY
        if krp_setting_window.result is not True:
            return
        else:
            self.robot_with_camera.update_cam_pos_on_current_position()

    def type_code(self):
        print("WRITE ME PLEASE")


if __name__ == "__main__":
    mock_robot = robot_with_camera_mock()
    app = MainApp(mock_robot)
    app.mainloop()