import os

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_DISABLE_ONEDNN"] = "1"

from paddleocr import PaddleOCR

IMAGE_PATH = "backend/tests/anpr/plate_1.jpg"

ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

print("Starting OCR...")

try:
    result = ocr.predict(IMAGE_PATH)

    print()
    print("=" * 60)
    print("OCR SUCCESS")
    print("=" * 60)

    for res in result:
        data = res.json

        if callable(data):
            data = data()

        print(data)

except Exception as error:
    print()
    print("=" * 60)
    print("OCR FAILED")
    print("=" * 60)
    print(type(error).__name__)
    print(error)