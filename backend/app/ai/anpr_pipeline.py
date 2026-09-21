from dataclasses import dataclass
@dataclass
class ANPRResult: plate_number:str; confidence:float; vehicle_type:str; bbox:tuple[int,int,int,int]
class ANPRPipeline:
    # Integration point for YOLO -> plate localization -> enhancement -> OCR/ANPR.
    def __init__(self,detector=None,ocr=None): self.detector=detector; self.ocr=ocr
    def process(self,frame): return []
