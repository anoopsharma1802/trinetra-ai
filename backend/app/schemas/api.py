from datetime import datetime
from pydantic import BaseModel

class CityOut(BaseModel):
	id: int
	name: str
	state: str
	country: str
	latitude: float | None = None
	longitude: float | None = None
	is_active: bool
class CameraOut(BaseModel): id:int; name:str; city:str; latitude:float; longitude:float; status:str; stream_url:str|None=None
class VehicleEventOut(BaseModel): id:int; plate_number:str; city:str; camera_id:int; confidence:float; latitude:float; longitude:float; captured_at:datetime; image_url:str|None=None
class VehicleBlacklistIn(BaseModel): plate_number:str; reason:str = "Manual review"
class VehicleBlacklistOut(BaseModel): id:int; plate_number:str; reason:str; created_at:datetime
class TrajectoryPoint(BaseModel): camera_id:int; camera_name:str; latitude:float; longitude:float; timestamp:datetime; confidence:float
class TrajectoryOut(BaseModel): plate_number:str; points:list[TrajectoryPoint]
class AlertOut(BaseModel): id:int; severity:str; title:str; message:str; plate_number:str|None=None; resolved:bool; created_at:datetime
class AnalyticsOut(BaseModel): active_cameras:int; vehicles_today:int; alerts_open:int; congestion_index:float
