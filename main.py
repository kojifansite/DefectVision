from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from PIL import Image, ImageDraw
import numpy  as np
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from ultralytics import YOLO
import cv2
import math
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")

origins = [
    "http://localhost:8000",
    "http://localhost:5173"

]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ПОИСК ДЕФЕКТОВ ЧЕРЕЗ ИЗОБРАЖЕНИЕ

@app.post("/detect")
async def detect(image_file: UploadFile = File(...)):
    buf = await image_file.read()
    boxes = detect_objects_on_image(Image.open(BytesIO(buf)))
    annotated_image = annotate_image(Image.open(BytesIO(buf)), boxes)
    return save_annotated_image(annotated_image)


def detect_objects_on_image(image):
    model = YOLO("./models/best_s2.pt")
    results = model.predict(image)
    result = results[0]
    output = []
    for box in result.boxes:
        x1, y1, x2, y2 = [round(x) for x in box.xyxy[0].tolist()]
        class_id = box.cls[0].item()
        prob = round(box.conf[0].item(), 2)
        output.append([x1, y1, x2, y2, result.names[class_id], prob])
    return output


def annotate_image(image, boxes):
    draw = ImageDraw.Draw(image)
    for box in boxes:
        x1, y1, x2, y2, object_type, probability = box
        draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)
        draw.text((x1, y1 - 10), f"{object_type} ({probability})", fill="red")
    return image


def save_annotated_image(image):
    output_buffer = BytesIO()
    image.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    return StreamingResponse(output_buffer, media_type="image/png")

# ПОИСК ДЕФЕКТОВ ЧЕРЕЗ КАМЕРУ

model = YOLO('./models/best_s2.pt')

classNames = ["defect", "inosuke"]

# Async video capture
class VideoCapture:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)
        self.cap.set(4, 480)

    def __del__(self):
        self.cap.release()

    async def get_frame(self):
        success, img = self.cap.read()
        if not success:
            return None
        ret, jpeg = cv2.imencode('.jpg', img)
        return jpeg.tobytes()

video_capture = VideoCapture()

def detect_objects(img):
    results = model(img, stream=True)
    
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = math.ceil((box.conf[0] * 100)) / 100
            cls = int(box.cls[0])
            class_name = classNames[cls]
            org = [x1, y1]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            color = (0, 0, 225)
            thickness = 2
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(img, class_name, org, font, fontScale, color, thickness)
    return img


async def generate():
    while True:
        frame = await video_capture.get_frame()
        if frame is not None:
            img = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8), -1)
            img_with_objects = detect_objects(img)
            _, frame = cv2.imencode('.jpg', img_with_objects)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n\r\n')
            

@app.get("/video_cam")
async def video_feed():
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")