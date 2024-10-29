import sys
import os
from pathlib import Path

print(os.getcwd())
sys.path.append("..")
print(os.getcwd())

from GUI.gui import MainGui
from Main.main_class import robot_developer

# KRP is the l button of the keyboard
KRP = [146.5/1000, -262.8/1000, 20/1000]

#CAMERA_POSITION = [KRP[0] - 5/1000, KRP[1] + 17/1000, 195/1000]
CAMERA_POSITION = [KRP[0], KRP[1] + 61.5/1000, 195/1000]

if __name__ == "__main__":
    robot_developer = robot_developer(KRP, CAMERA_POSITION)
    app = MainGui(robot_developer)
    app.mainloop()