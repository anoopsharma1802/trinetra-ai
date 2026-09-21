from ultralytics import YOLO

MODEL_PATH = "backend/models/plate_detector/best.pt"
VIDEO_PATH = "backend/tests/anpr/IMG_0.avi"

model = YOLO(MODEL_PATH)

results = model.predict(
    source=VIDEO_PATH,
    conf=0.25,
    save=True,
    show=False,
)

print("PLATE DETECTION COMPLETE")
print("Processed video:", VIDEO_PATH)
print("Result saved by Ultralytics in the runs folder.")