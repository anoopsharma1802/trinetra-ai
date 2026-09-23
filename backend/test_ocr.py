from paddleocr import PaddleOCR

# PaddleOCR 3.x — naya API
ocr = PaddleOCR(
    lang='en',
    enable_mkldnn=False,
    use_textline_orientation=True
)

# Naya method: .predict() (purana .ocr(cls=True) deprecated hai)
result = ocr.predict('data/test_plates/plate1.jpg')

print("\n=== OCR Raw Result ===")
print(result)

print("\n=== Extracted Text ===")
for res in result:
    # PaddleOCR 3.x returns objects with .json
    try:
        data = res.json
        if 'res' in data and 'rec_texts' in data['res']:
            for text, score in zip(data['res']['rec_texts'], data['res']['rec_scores']):
                print(f"Detected: {text}  (confidence: {score:.2f})")
    except AttributeError:
        # Fallback for older structures
        if isinstance(res, list):
            for line in res:
                print(line)