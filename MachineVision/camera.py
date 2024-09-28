import cv2
from datetime import datetime


def take_image(camera_idx: int) -> None:
    """
        Takes a picutre for image processing in png format.

        Args:
            camera_idx (int): The index of the camera you want to use for taking
                              pictures.

        Returns:
            None
    """

    # NOTE: Could be useful to retuirn the save location of the image
    cam = cv2.VideoCapture(camera_idx)
    cv2.namedWindow("test")

    ret, frame = cam.read()
    if not ret:
        print(f"Could not take a picture with camera index {camera_idx}")
        return
    cv2.imshow("test", frame)
    img_name = f"opencv_frame_{datetime.now()}.png"

    # TODO: save location might need to be modified
    cv2.imwrite(img_name, frame)
    print("Img written!")
    cam.release()
    cv2.destroyAllWindows()
