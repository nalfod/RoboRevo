import cv2
from datetime import datetime
from pathlib import Path
import time

class Camera:
    def __init__(self, camera_idx=0, resolution=(1920, 1080)) -> None:        
        self.camera_idx = camera_idx

        print(f"Camera.__init__ - BEGIN Creating the image capturer object with id {self.camera_idx}")
        self.cam = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)

        if not self.cam.isOpened():
            raise ValueError(f"Could not open camera with index {camera_idx}")

        self.set_resolution(*resolution)

        print("Camera.__init__  - Auto exposure and white balance")
        # Set camera properties for automatic adjustments (if available)
        retValAutoExp = self.cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Enable auto-exposure if available
        retValAutoWB = self.cam.set(cv2.CAP_PROP_AUTO_WB, 1)        # Enable auto white-balance if available
        print(f"Camera.__init__  - retValAutoExp= {retValAutoExp} retValAutoWB= {retValAutoWB}")

        if retValAutoWB is not True:
            print("Camera.__init__  - Auto white balance failed.... setting brightness manually")
            retValAutoManualBrightness = self.cam.set(cv2.CAP_PROP_BRIGHTNESS, 1000)
            print(f"Camera.__init__  - retValAutoManualBrightness= {retValAutoManualBrightness} retValAutoWB= {self.cam.get(cv2.CAP_PROP_BRIGHTNESS)}")

            # what can be also set: CAP_PROP_CONTRAST  CAP_PROP_SATURATION 

    def set_resolution(self, width, height):
        print(f"Camera.set_resolution - Setting the resolution to {width}x{height}")
        retValWidth = self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        print(f"Camera.set_resolution - The result of setting the width is= {retValWidth} current width is= {self.cam.get(cv2.CAP_PROP_FRAME_WIDTH)}")
        retValHeight = self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        print(f"Camera.set_resolution - The result of setting the height is= {retValHeight} current height is= {self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
             

    def __del__(self):
        if self.cam.isOpened():
            self.cam.release()
            print(f"Camera {self.camera_idx} released")


    def take_image(self) -> Path:
        """
            Takes a picutre for image processing in png format.

            Args:
                -

            Returns:
                None if wrong camera index given
                otherwise the path of the saved image
        """

        cv2.namedWindow("test")

        print("take_image - Taking the picture")
        ret, frame = self.cam.read()

        # TODO: worth a shot to try this, if brigthness is still bad:
        # cv2.normalize(frame, frame, 0, 255, cv2.NORM_MINMAX)
        if not ret:
            print(f"Could not take a picture with camera index {self.camera_idx}")
            return None
        
        print("take_image - Displaying the picture on the test frame")
        cv2.imshow("test", frame)

        img_name = f"opencv_frame_{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        current_dir = Path.cwd()
        save_dir = current_dir / "CameraOutput"
        save_dir.mkdir(parents=True, exist_ok=True) # Create CameraOutput directory if it doesn't exist

        save_path = save_dir / img_name
        print(f"take_image - I will save to {save_path}")

        # TODO: save location might need to be modified
        cv2.imwrite(save_path, frame)
        print(f"take_image - Img saved as {img_name}")

        cv2.destroyAllWindows()
        return save_path


if __name__ == "__main__":
    camera = Camera(camera_idx=0)

    print("Taking the first picture!")
    path = camera.take_image()

    print("Taking the second picture!!! Get ready!!")
    time.sleep(3)
    path = camera.take_image()

    if path is not None:
        print(f"Image saved to {path}")
    else:
        print("Returned None... maybe wrong camera index?")