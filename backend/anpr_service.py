"""
M1 + M2: Edge AI + OCR Service
Input: image path or bytes
Output: {plate_text, confidence, bbox, crop_path}
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import cv2
import numpy as np
import os
import tempfile
from ultralytics import YOLO
from paddleocr import PaddleOCR

app = FastAPI(title="M1+M2 ANPR Service", version="1.0.0")

# Load models once at startup
print("[M1] Loading YOLO...")
YOLO_PATH = os.environ.get("YOLO_PATH", "/Users/apple/trinetra-ai/backend/models/plate_detector/best.pt")
yolo = YOLO(YOLO_PATH)
print(f"[M1] YOLO loaded: {yolo.names}")

print("[M2] Loading PaddleOCR...")
ocr = PaddleOCR(lang='en', enable_mkldnn=False)
print("[M2] PaddleOCR loaded")


class DetectionResult(BaseModel):
    plate_text: str
    confidence: float
    yolo_confidence: float
    bbox: list
    crop_path: str


def detect_plate(image_path: str, yolo_conf: float = 0.5):
    """Run YOLO + OCR on image, return all detected plates."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    results = yolo(img, conf=yolo_conf, verbose=False)
    detections = []

    for i, box in enumerate(results[0].boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        yconf = float(box.conf[0])

        # Crop plate region
        crop = img[y1:y2, x1:x2]
        crop_path = f"/tmp/plate_crop_{i}.jpg"
        cv2.imwrite(crop_path, crop)

        # OCR
        ocr_result = ocr.predict(crop)
        for res in ocr_result:
            data = res.json if hasattr(res, 'json') else res
            if isinstance(data, dict) and 'res' in data:
                texts = data['res'].get('rec_texts', [])
                scores = data['res'].get('rec_scores', [])
                for text, score in zip(texts, scores):
                    detections.append(DetectionResult(
                        plate_text=text.upper().strip(),
                        confidence=float(score),
                        yolo_confidence=yconf,
                        bbox=[x1, y1, x2, y2],
                        crop_path=crop_path,
                    ))

    return detections


@app.get("/health")
def health():
    return {"status": "ok", "yolo_classes": list(yolo.names.values())}


@app.post("/detect")
def detect_from_path(image_path: str):
    """Detect plates from an image file path."""
    try:
        results = detect_plate(image_path)
        return {"status": "ok", "count": len(results), "detections": [r.dict() for r in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect-upload")
async def detect_upload(file: UploadFile = File(...)):
    """Detect plates from uploaded image."""
    try:
        # Save uploaded file to temp
        suffix = os.path.splitext(file.filename)[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        results = detect_plate(tmp_path)
        os.unlink(tmp_path)
        return {"status": "ok", "count": len(results), "detections": [r.dict() for r in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))