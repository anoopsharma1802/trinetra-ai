from fastapi import APIRouter
from pydantic import BaseModel
router=APIRouter()
class ChallanRequest(BaseModel): plate_number:str; violation_code:str; location:str; evidence_url:str|None=None
@router.post('/challan')
def challan(payload:ChallanRequest): return {'status':'queued','message':'Demo enforcement workflow accepted','plate_number':payload.plate_number,'violation_code':payload.violation_code}
