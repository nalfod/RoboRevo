from ultralytics import YOLO
import os
#from IPython.display import display, Image
#from IPython import display
#display.clear_output()

os.chdir(r'C:\Users\Z004KZJX\Documents\MUNKA\ROBOREVO\URSim_shared\RoboRevo\MachineVision')
print(os.getcwd())
print(os.path.isfile(r'neural_networks\best2_1.pt'))
model = YOLO(r"neural_networks\best2_1.pt")

results = model.predict(r'C:\Users\Z004KZJX\Documents\MUNKA\ROBOREVO\ObjectDetection\Images\v2\raw_images\both\c1.jpg', show = True, save=True, imgsz=720, conf=0.5)

print("\nDetected objects")
print("----------------\n")
for i in range(len(results[0].boxes)):
        objname = results[0].names[int(results[0].boxes.cls[i])]
        confid = results[0].boxes.cpu().numpy().conf[i]
        xyxy = results[0].boxes.cpu().numpy().xyxy[i]
        
        # position in YOLO format (top-left, bottom-right)
        # more position format: xywh,xywhn; xyxy,xyxyn; I think "n" means normalized
        # check the pixel coordinates with openning of the imgae in paint
        print(f"{objname} {confid:.2f} position: {xyxy}")
print("")