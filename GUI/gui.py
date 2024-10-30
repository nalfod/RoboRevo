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
        print("MOCK MAINCLASS - MY KRP HAS BEEN UPDATED ON MY CURRENT POSITION")

    def update_cam_pos_on_current_position(self):
        print("MOCK MAINCLASS - MY CAMERA POSITION HAS BEEN UPDATED ON MY CURRENT POSITION")

    def move_relative_to_current_pos(self, direction: str, magnitude: int):
        print(f"MOCK MAINCLASS - I WILL MOVE {magnitude} mm in direction {direction}")

    def listen_the_input_generate_code(self) -> bool:
        print(f"MOCK MAINCLASS - I AM LISTENING THE INSTRUCTION")
        return True
    
    def get_code_to_generate_from_direct_input(self) -> bool:
        print(f"MOCK MAINCLASS - TYPE THE CODE:")
        code_to_generate = input()
        print(f"MOCK MAINCLASS - I WILL TYPE: {code_to_generate}")
        return True
    
    def type_the_code(self) -> bool:
        print(f"MOCK MAINCLASS - I AM TYPING THE CODE")
        return True

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
        self.geometry("400x250")

        self.result = None

        current_row = 0
        label = tk.Label(self, text=message)
        label.grid(row=current_row, column=0, sticky="nsew", padx=5, pady=5, columnspan= 4 )

        current_row = self.add_camera_position_adjusting_buttons(current_row)

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
    def __init__(self, parent, title: str, message: str, robot_with_camera):
        self.robot_with_camera = robot_with_camera
        self.robot_with_camera.send_camera_position()

        # dont change the order! init of base class will block the code at the end of the function
        super().__init__(parent, title, message)

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

        move_button = tk.Button(self, text="MOVE", command=lambda: self.send_move_command())
        move_button.grid(row=current_row, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        return current_row + 1

    def send_move_command(self):
        print("send_move_command - begin")
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

        # print(f"My new direction is= {tmp_direction} and my new magnitude is= {tmp_magnitude_int}")
        self.robot_with_camera.move_relative_to_current_pos(tmp_direction, tmp_magnitude_int)

    def on_proceed(self):
        super().on_proceed()

    def on_cancel(self):
        super().on_cancel()




##################
# MAIN_GUI
##################
class MainGui(tk.Tk):
    def __init__(self, robot_with_camera):
        super().__init__()
        self.title("Robot developer")
        self.geometry("500x200")

        self.robot_with_camera = robot_with_camera

        self.robot_positions_labels = []

        number_of_rows = 0
        # Yearly data widgets:
        label1 = tk.Label(self, text="KRP:")
        label1.grid(row=number_of_rows, column=0, sticky="e", padx=5, pady=5)
        new_krp_to_display = [ ( round(x, 2) ) for x in self.robot_with_camera.get_krp()]
        label2 = tk.Label(self, text=new_krp_to_display)
        label2.grid(row=number_of_rows, column=1, sticky="e", padx=5, pady=5)
        self.robot_positions_labels.append(label2)
        
        number_of_rows += 1
        label3 = tk.Label(self, text="Camera position:")
        label3.grid(row=number_of_rows, column=0, sticky="e", padx=5, pady=5)
        new_cam_pos_to_display = [ ( round(x, 2) ) for x in self.robot_with_camera.get_camera_pos()]
        label4 = tk.Label(self, text=new_cam_pos_to_display)
        label4.grid(row=number_of_rows, column=1, sticky="e", padx=5, pady=5)
        self.robot_positions_labels.append(label4)


        number_of_rows += 1
        send_home_button = tk.Button(self, text="Send home", command=self.robot_with_camera.send_home)
        send_home_button.grid(row=number_of_rows, column=0, sticky="nsew", padx=5, pady=5)

        touch_krp_button = tk.Button(self, text="Touch KRP", command=self.robot_with_camera.touch_KRP)
        touch_krp_button.grid(row=number_of_rows, column=1, sticky="nsew", padx=5, pady=5)

        touch_krp_button = tk.Button(self, text="Go to cam pos", command=self.robot_with_camera.send_camera_position)
        touch_krp_button.grid(row=number_of_rows, column=2, sticky="nsew", padx=5, pady=5)

        number_of_rows += 1

        send_home_button = tk.Button(self, text="Set new KRP", command=self.set_new_krp)
        send_home_button.grid(row=number_of_rows, column=0, sticky="nsew", padx=5, pady=5)

        touch_krp_button = tk.Button(self, text="Set new cam pos", command=self.set_new_camera_position)
        touch_krp_button.grid(row=number_of_rows, column=1, sticky="nsew", padx=5, pady=5)

        number_of_rows += 1

        touch_krp_button = tk.Button(self, text="TYPE CODE", command=self.type_code)
        touch_krp_button.grid(row=number_of_rows, column=0, sticky="nsew", padx=5, pady=5)

        self.code_input_mode_var = tk.IntVar()  # Variable to hold the value of the radio button
        code_input_mode_var = tk.Checkbutton(self, text="CL input (test mode)", variable=self.code_input_mode_var)
        code_input_mode_var.grid(row=number_of_rows, column=2 , pady=10)

    def set_new_krp(self):
        conf_window = pop_up(self, "Attention", "This will change the KRP, do you want to proceed?")

        if conf_window.result is not True:
            return
        
        krp_setting_window = pop_up(self, "Set new KRP", "Move the tool of the robot to touch\nthe midpoint of letter 'l',\nand press 'Proceed' if it is there!")

        if krp_setting_window.result is not True:
            messagebox.showinfo("Info", "New position has been discard!!")
            return
        else:
            messagebox.showinfo("Info", "Position has been updated!")
            self.robot_with_camera.update_krp_on_current_position()
            new_krp_to_display = [ ( round(x, 2) ) for x in self.robot_with_camera.get_krp()]
            self.robot_positions_labels[0].config(text=new_krp_to_display)

            if messagebox.askyesno("Set new cam pos?", "Do you want to reset the camera position according to the new KRP?"):
                new_krp = self.robot_with_camera.get_krp()
                self.robot_with_camera.set_camera_position([new_krp[0] - 5, new_krp[1] + 17, 195] + [-0.0, 3.14159, -0.0])
                
                new_cam_pos_to_display = [ ( round(x, 2) ) for x in self.robot_with_camera.get_camera_pos()]
                self.robot_positions_labels[1].config(text=new_cam_pos_to_display)



    def set_new_camera_position(self):
        conf_window = pop_up(self, "Attention", "This will change the camera position, do you want to proceed?")

        if conf_window.result is not True:
            return
        
        messagebox.showwarning("Warning", "The robot will move to camera position, step away!!")
        
        camera_setting_window = pop_up_camera(self, "Set new camera position", "Move robot is 'x' and 'y' direction\nwith a predefined magnitude,\nand press 'Proceed' if you are satisfied\nwith the new position!", self.robot_with_camera)

        if camera_setting_window.result is not True:
            messagebox.showinfo("Info", "New position has been discard!!")
            return
        else:
            messagebox.showinfo("Info", "Position has been updated!")
            self.robot_with_camera.update_cam_pos_on_current_position()
            new_cam_pos_to_display = [ ( round(x, 2) ) for x in self.robot_with_camera.get_camera_pos()]
            self.robot_positions_labels[1].config(text=new_cam_pos_to_display)

    def type_code(self):
        # FIXME: try - catch blocks would be more sophisticated so the error can be determined here
        result_of_code_generation = False
        if bool(self.code_input_mode_var.get()):
            result_of_code_generation = self.robot_with_camera.get_code_to_generate_from_direct_input()
        else:
            result_of_code_generation = self.robot_with_camera.listen_the_input_generate_code()
        if not result_of_code_generation:
            messagebox.showerror("Error", "Speech recognition or code generation did not work, try it again!!")
            return

        result_of_code_typing = self.robot_with_camera.type_the_code()
        if not result_of_code_typing:
            messagebox.showerror("Error", "Image recognition or typing did not work, try it again!!")
            return


if __name__ == "__main__":
    mock_robot = robot_with_camera_mock()
    app = MainGui(mock_robot)
    app.mainloop()