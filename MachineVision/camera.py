import cv2
from datetime import datetime
from pathlib import Path


def take_image(camera_idx: int, resolution=(1920, 1080)) -> Path:
    """
        Takes a picutre for image processing in png format.

        Args:
            camera_idx (int): The index of the camera you want to use for taking
                              pictures.

        Returns:
            None if wrong camera index given
            otherwise the path of the saved image
    """

    print("take_image - Creating the video capturer object")
    cam = cv2.VideoCapture(camera_idx)
    # Set the resolution
    print("take_image - Setting the resolution")
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    print("take_image - Auto exposure and white balance")
    # Set camera properties for automatic adjustments (if available)
    cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Enable auto-exposure if available
    cam.set(cv2.CAP_PROP_AUTO_WB, 1)        # Enable auto white-balance if available

    # cam.set(cv2.CAP_PROP_BRIGHTNESS, 0.5 * 255) # Manually set the brightness

    cv2.namedWindow("test")

    print("take_image - Taking the picture")
    ret, frame = cam.read()
    if not ret:
        print(f"Could not take a picture with camera index {camera_idx}")
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
    print(f"take_image -Img written as {img_name}")
    cam.release()
    cv2.destroyAllWindows()

    return save_path


if __name__ == "__main__":
    path = take_image(0, [1920, 1080])

    if path is not None:
        print(f"Image saved to {path}")
    else:
        print("Returned None... maybe wrong camera index?")