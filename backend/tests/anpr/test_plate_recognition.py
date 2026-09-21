import os

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_DISABLE_ONEDNN"] = "1"

import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR


MODEL_PATH = "backend/models/plate_detector/best.pt"
VIDEO_PATH = "backend/tests/anpr/IMG_0.avi"

# YOLO = plate localization
model = YOLO(MODEL_PATH)

# PaddleOCR = recognition only
ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)


cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise RuntimeError(f"Could not open video: {VIDEO_PATH}")

frame_count = 0
plates_found = 0


while True:

    ok, frame = cap.read()

    if not ok:
        break

    frame_count += 1

    # Every 5th frame
    if frame_count % 5 != 0:
        continue

    results = model.predict(
        source=frame,
        conf=0.25,
        verbose=False
    )

    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes.xyxy.cpu().numpy():

            x1, y1, x2, y2 = map(int, box)

            h, w = frame.shape[:2]

            x1 = max(0, min(x1, w - 1))
            x2 = max(0, min(x2, w))

            y1 = max(0, min(y1, h - 1))
            y2 = max(0, min(y2, h))

            if x2 <= x1 or y2 <= y1:
                continue

            plate_crop = frame[y1:y2, x1:x2]

            if plate_crop.size == 0:
                continue

            plates_found += 1

            # Save first few crops for inspection
            crop_path = (
                f"backend/tests/anpr/plate_{plates_found}.jpg"
            )

            cv2.imwrite(crop_path, plate_crop)

            print()
            print("=" * 50)
            print(f"PLATE DETECTION #{plates_found}")
            print("Crop:", crop_path)

            # OCR
            try:

                ocr_result = ocr.predict(crop_path)

                for res in ocr_result:

                    print("RAW OCR RESULT:")

                    try:
                        data = res.json

                        if callable(data):
                            data = data()

                        print(data)

                    except Exception as error:

                        print(
                            "Could not parse OCR result:",
                            error
                        )

            except Exception as error:

                print("OCR ERROR:", error)

            # Test only first 10 detections
            if plates_found >= 10:
                break

        if plates_found >= 10:
            break

    if plates_found >= 10:
        break


cap.release()

print()
print("=" * 50)
print("PLATE RECOGNITION TEST COMPLETE")
print("Frames processed:", frame_count)
print("Plate detections:", plates_found)