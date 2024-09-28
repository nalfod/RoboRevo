import cv2
from datetime import datetime


def take_image():
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("test")

    ret, frame = cam.read()
    if not ret:
        print("fos")
        return
    cv2.imshow("test", frame)
    img_name = f"opencv_frame_{datetime.now()}.png"

    cv2.imwrite(img_name, frame)
    print("Img written!")
    cam.release()
    cv2.destroyAllWindows()
