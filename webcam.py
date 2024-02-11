from ultralytics import YOLO
import cv2

model = YOLO('./models/best_s2.pt')
results = model.predict(source='0', show=True)