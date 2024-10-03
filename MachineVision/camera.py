import cv2
from datetime import datetime
from pathlib import Path


def take_image(camera_idx: int) -> Path:
    """
        Takes a picutre for image processing in png format.

        Args:
            camera_idx (int): The index of the camera you want to use for taking
                              pictures.

        Returns:
            None if wrong camera index given
            otherwise the path of the saved image
    """

    cam = cv2.VideoCapture(camera_idx)
    cv2.namedWindow("test")

    ret, frame = cam.read()
    if not ret:
        print(f"Could not take a picture with camera index {camera_idx}")
        return None
    cv2.imshow("test", frame)
    img_name = f"opencv_frame_{datetime.now():%Y-%m-%d_%H-%M-%S}.png"

    # Get the current working directory as a Path object
    current_dir = Path.cwd()

    # Create CameraOutput directory if it doesn't exist
    save_dir = current_dir / "CameraOutput"
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / img_name
    print(f"I will save to {save_path}")

    # TODO: save location might need to be modified
    cv2.imwrite(save_path, frame)
    print(f"Img written as {img_name}")
    cam.release()
    cv2.destroyAllWindows()

    return save_path


if __name__ == "__main__":
    path = take_image(0)

    if path is not None:
        print(f"Image saved to {path}")
    else:
        print("Returned None... maybe wrong camera index?")