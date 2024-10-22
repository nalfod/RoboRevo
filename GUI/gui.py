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
        print("MOCK - I SEND MYSELF TO HOME")

    def touch_KRP(self):
        print("MOCK - I SEND MYSELF TO KRP")

    def send_camera_position(self):
        print("MOCK - I SEND MYSELF TO CAMERA POSITION")

    def update_krp_on_current_position(self):
        print("MOCK - MY KRP HAS BEEN UPDATED")

    def update_cam_pos_on_current_position(self):
        print("MOCK - MY CAMERA POSITION HAS BEEN UPDATED")

    def generate_code_based_on_input(self, input: str):
        print(f"MOCK - I WILL GENERATE CODE BASED ON {input}")

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
        label.grid(row=current_row, column=0, sticky="e", padx=5, pady=5)

        current_row += 1
        proceed_button = tk.Button(self, text="Proceed", command=lambda: self.on_proceed())
        proceed_button.grid(row=current_row, column=0, columnspan=2, pady=10)

        cancel_button = tk.Button(self, text="Cancel", command=lambda: self.on_cancel())
        cancel_button.grid(row=current_row, column=2, columnspan=2, pady=10)

        self.grab_set()  # Block input to the parent window until this one is closed
        self.transient(parent)  # Keep popup on top of the parent window
        self.wait_window(self)  # Wait until the popup window is closed

    def on_proceed(self):
        self.result = True
        self.destroy()

    def on_cancel(self):
        self.result = False
        self.destroy()



##################
# MAIN_GUI
##################
class MainApp(tk.Tk):
    def __init__(self, robot_with_camera):
        super().__init__()
        self.title("Robot developer")
        self.geometry("300x150")

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
        
        krp_setting_window = pop_up(self, "Set new KRP", "Move the tool of the robot to touch the midpoint of letter 'l', and press 'Proceed' if it is there!")

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