from dataclasses import dataclass
from pathlib import Path
import re



@dataclass
class ANPRResult:
    plate_number: str
    confidence: float
    vehicle_type: str
    bbox: tuple[int, int, int, int]


class ANPRPipeline:
    def __init__(self, detector=None, ocr=None):
        self.detector = detector
        self.ocr = ocr

    def process(self, frame):
        if self.detector is None:
            from ultralytics import YOLO

            model_path = Path(__file__).resolve().parents[2] / "models" / "plate_detector" / "best.pt"
            self.detector = YOLO(str(model_path))

        if self.ocr is None:
            from paddleocr import PaddleOCR

            self.ocr = PaddleOCR(
                lang="en",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )

        detections = []
        for result in self.detector.predict(source=frame, conf=0.25, verbose=False):
            if result.boxes is None:
                continue

            height, width = frame.shape[:2]
            for box, confidence in zip(
                result.boxes.xyxy.cpu().numpy(),
                result.boxes.conf.cpu().numpy(),
            ):
                x1, y1, x2, y2 = map(int, box)
                x1, x2 = max(0, min(x1, width - 1)), max(0, min(x2, width))
                y1, y2 = max(0, min(y1, height - 1)), max(0, min(y2, height))
                if x2 <= x1 or y2 <= y1:
                    continue

                crop = frame[y1:y2, x1:x2]
                text = self._read_plate(crop)
                if text:
                    detections.append(
                        ANPRResult(text, float(confidence), "vehicle", (x1, y1, x2, y2))
                    )

        return detections

    def _read_plate(self, crop):
        import cv2

        if crop is None or crop.size == 0:
            return None

        height, width = crop.shape[:2]
        scale = max(2, min(4, 720 // max(width, 1)))
        enlarged = cv2.resize(
            crop,
            (width * scale, height * scale),
            interpolation=cv2.INTER_CUBIC,
        )
        gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
        variants = [
            enlarged,
            cv2.detailEnhance(enlarged, sigma_s=10, sigma_r=0.15),
            cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        ]

        values = []
        for variant in variants:
            values.extend(self._ocr_variant(variant))

        for text in values:
            normalized = self._normalize_plate(text)
            if self._is_plate(normalized):
                return normalized
        return None

    def _ocr_variant(self, image):
        if hasattr(self.ocr, "predict"):
            results = self.ocr.predict(image)
            values = []
            for result in results:
                data = result.json() if callable(result.json) else result.json
                values.extend(self._ocr_texts(data))
        else:
            # PaddleOCR 2.x exposes OCR through ``ocr`` instead of ``predict``.
            results = self.ocr.ocr(image, cls=False)
            values = self._ocr_texts(results)
        return values

    def _normalize_plate(self, text):
        normalized = re.sub(r"[^A-Z0-9]", "", str(text).upper())
        if len(normalized) < 8 or len(normalized) > 12:
            return normalized

        # Correct common OCR confusions only in positions where a plate expects digits.
        normalized = list(normalized)
        for index in (2, 3, 7, 8, 9, 10):
            if index < len(normalized):
                normalized[index] = {"O": "0", "I": "1", "Z": "2", "S": "5"}.get(
                    normalized[index], normalized[index]
                )
        return "".join(normalized)

    def _is_plate(self, text):
        return bool(re.fullmatch(r"[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}", text))

    def _ocr_texts(self, value):
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            return [text for item in value.values() for text in self._ocr_texts(item)]
        if isinstance(value, (list, tuple)):
            if len(value) == 2 and isinstance(value[0], str):
                return [value[0]]
            return [text for item in value for text in self._ocr_texts(item)]
        return []
