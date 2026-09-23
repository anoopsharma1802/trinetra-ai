from ultralytics import YOLO
from paddleocr import PaddleOCR
import cv2
import os

# Load models
print("Loading YOLO...")
yolo = YOLO('/Users/apple/trinetra-ai/backend/models/plate_detector/best.pt')
print("YOLO classes:", yolo.names)

print("\nLoading PaddleOCR...")
ocr = PaddleOCR(lang='en', enable_mkldnn=False)
print("PaddleOCR loaded")

# Test image
image_path = 'data/test_plates/plate1.jpg'
img = cv2.imread(image_path)
print(f"\nImage shape: {img.shape}")

# Step 1: YOLO detection
print("\n=== YOLO Detection ===")
results = yolo(img, verbose=False)

plate_found = False
for r in results:
    if r.boxes is None:
        continue
    for box in r.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        class_name = yolo.names[cls]

        print(f"Detected: {class_name} (conf={conf:.2f}) at [{x1},{y1},{x2},{y2}]")

        # Step 2: If plate detected, crop and OCR
        if 'plate' in class_name.lower() or cls == 1:
            plate_found = True
            plate_crop = img[y1:y2, x1:x2]
            crop_path = 'data/test_plates/crop.jpg'
            cv2.imwrite(crop_path, plate_crop)
            print(f"  → Plate crop saved: {crop_path}")

            # Step 3: OCR on cropped plate
            ocr_result = ocr.ocr(plate_crop)

            print(f"  → OCR result:")
            for res in ocr_result:
                if res is None:
                    continue
                for line in res:
                    text = line[1][0]
                    score = line[1][1]
                    print(f"     Plate Text: {text}  (conf: {score:.2f})")

if not plate_found:
    print("\n⚠️ No plate detected. YOLO classes check karo.")