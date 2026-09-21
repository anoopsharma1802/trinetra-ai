import cv2
import re
import json
import time
from ultralytics import YOLO
from paddleocr import PaddleOCR

MODEL_PATH = "backend/models/plate_detector/best.pt"
VIDEO_PATH = "backend/tests/anpr/IMG_0.avi"

# -----------------------------
# YOLO
# -----------------------------
model = YOLO(MODEL_PATH)

# -----------------------------
# PaddleOCR
# -----------------------------
ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

# -----------------------------
# Indian Vehicle Number Validation
# -----------------------------
# Examples:
# UP32AB1234
# DL01AB1234
# TN10BQ1586
# MH12DE1433
#
# This is a practical ANPR filter.
# It intentionally focuses on normal
# Indian private/commercial plate patterns.
# -----------------------------

INDIAN_PLATE_PATTERN = re.compile(
    r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$"
)

# Common OCR noise that is definitely not a plate
IGNORED_TEXT = {
    "LICENSE",
    "LICENSEPLATE",
    "PLATE",
    "NUMBERPLATE",
    "NUMBER",
    "INDIA",
    "IND",
}

MIN_CONFIDENCE = 0.75

# -----------------------------
# Duplicate Suppression
# -----------------------------
# Same plate will not be printed again
# within this many seconds.
DUPLICATE_WINDOW_SECONDS = 5

last_seen = {}

# -----------------------------
# Helper functions
# -----------------------------

def clean_ocr_text(text: str) -> str:
    """
    Convert OCR output into a normalized
    alphanumeric uppercase string.
    """
    text = str(text).upper().strip()

    # Remove spaces, -, dots, etc.
    text = re.sub(r"[^A-Z0-9]", "", text)

    return text


def normalize_plate(text: str) -> str:
    """
    Normalize common OCR mistakes.

    Only applies substitutions where they
    commonly occur in vehicle plates.
    """
    text = clean_ocr_text(text)

    # Common OCR substitutions
    replacements = {
        " ": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def is_valid_indian_plate(text: str) -> bool:
    """
    Validate Indian vehicle registration format.
    """

    text = normalize_plate(text)

    if text in IGNORED_TEXT:
        return False

    if len(text) < 9 or len(text) > 11:
        return False

    return bool(INDIAN_PLATE_PATTERN.fullmatch(text))


def should_emit_plate(plate: str) -> bool:
    """
    Duplicate suppression.

    Returns True only when the plate should
    be emitted as a new detection.
    """

    now = time.time()

    previous_time = last_seen.get(plate)

    # First time seeing this plate
    if previous_time is None:
        last_seen[plate] = now
        return True

    # Same plate seen recently
    if now - previous_time < DUPLICATE_WINDOW_SECONDS:
        return False

    # Seen again after duplicate window
    last_seen[plate] = now

    return True


# -----------------------------
# Open Video
# -----------------------------

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise RuntimeError(
        f"Could not open video: {VIDEO_PATH}"
    )

frame_count = 0
plates_found = 0
valid_plates = 0
duplicates_removed = 0

print("=" * 70)
print("TRENETRA AI - INDIAN ANPR TEST")
print("=" * 70)

while True:

    ok, frame = cap.read()

    if not ok:
        break

    frame_count += 1

    # Process every 5th frame
    if frame_count % 5 != 0:
        continue

    # -----------------------------
    # YOLO Plate Detection
    # -----------------------------

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

            # -----------------------------
            # PaddleOCR
            # -----------------------------

            try:

                ocr_result = ocr.predict(plate_crop)

                for res in ocr_result:

                    data = res.json

                    if isinstance(data, str):
                        data = json.loads(data)

                    result_data = data.get(
                        "res",
                        data
                    )

                    texts = result_data.get(
                        "rec_texts",
                        []
                    )

                    scores = result_data.get(
                        "rec_scores",
                        []
                    )

                    for text, score in zip(
                        texts,
                        scores
                    ):

                        # Confidence filter
                        if float(score) < MIN_CONFIDENCE:
                            continue

                        plate = normalize_plate(text)

                        # -----------------------------
                        # Indian plate validation
                        # -----------------------------

                        if not is_valid_indian_plate(
                            plate
                        ):
                            continue

                        valid_plates += 1

                        # -----------------------------
                        # Duplicate suppression
                        # -----------------------------

                        if not should_emit_plate(
                            plate
                        ):

                            duplicates_removed += 1

                            continue

                        # -----------------------------
                        # CLEAN ANPR OUTPUT
                        # -----------------------------

                        print()
                        print("=" * 60)
                        print("[ANPR] VALID VEHICLE PLATE")
                        print("=" * 60)

                        print(
                            f"Frame      : {frame_count}"
                        )

                        print(
                            f"Plate      : {plate}"
                        )

                        print(
                            f"Confidence : {float(score):.2%}"
                        )

                        print(
                            "Status     : VALID"
                        )

                        print("=" * 60)

            except Exception as error:

                print(
                    f"[OCR ERROR] Frame {frame_count}: "
                    f"{error}"
                )


cap.release()

print()
print("=" * 70)
print("ANPR TEST COMPLETE")
print("=" * 70)

print(
    f"Frames processed   : {frame_count}"
)

print(
    f"Plate detections   : {plates_found}"
)

print(
    f"Valid OCR results  : {valid_plates}"
)

print(
    f"Duplicates removed : {duplicates_removed}"
)

print("=" * 70)