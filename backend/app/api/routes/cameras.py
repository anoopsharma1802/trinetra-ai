from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ...ai.anpr_pipeline import ANPRPipeline
from ...db.database import get_db
from .auth import verify_access_token
from ...db.models import Camera
from ...schemas.api import CameraOut
from ...services.alert_engine import check_blacklist_alert
from ...services.anpr_service import save_anpr_detection

router = APIRouter()
pipeline = ANPRPipeline()
bearer = HTTPBearer(auto_error=False)


@router.get("", response_model=list[CameraOut])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).order_by(Camera.id).all()


@router.post("/video/analyze")
async def analyze_video(
    video: UploadFile = File(...),
    camera_id: int = Form(...),
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    if credentials is None or not verify_access_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Authentication required")

    import cv2

    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    suffix = Path(video.filename or "video.mp4").suffix or ".mp4"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temporary:
        temporary.write(await video.read())
        video_path = temporary.name

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise HTTPException(status_code=400, detail="Uploaded file is not a readable video")

    results = []
    seen = set()
    frame_number = 0
    sampled_frames = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frame_number += 1
            if frame_number % 15 != 0:
                continue
            sampled_frames += 1

            for detection in pipeline.process(frame):
                if detection.plate_number in seen:
                    continue
                seen.add(detection.plate_number)
                event = save_anpr_detection(
                    db,
                    detection.plate_number,
                    camera.id,
                    detection.confidence,
                    camera.latitude,
                    camera.longitude,
                )
                await check_blacklist_alert(db, event.plate_number)
                results.append({
                    "plate_number": event.plate_number,
                    "confidence": event.confidence,
                    "frame": frame_number,
                    "event_id": event.id,
                })
    finally:
        capture.release()
        Path(video_path).unlink(missing_ok=True)

    return {
        "status": "completed",
        "camera_id": camera.id,
        "frames_processed": frame_number,
        "frames_sampled": sampled_frames,
        "detections": results,
        "message": (
            "No valid Indian number plate was recognized. Try a clearer video "
            "with visible plates and better lighting."
            if not results
            else f"Recognized {len(results)} unique plate(s)."
        ),
    }
