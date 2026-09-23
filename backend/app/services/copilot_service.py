import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.models import Alert, Camera, VehicleBlacklist, VehicleEvent

logger = logging.getLogger("trinetra.copilot")


INDIAN_PLATE_PATTERN = re.compile(r"\b([A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{1,4})\b")
CAMERA_PATTERN = re.compile(r"(?:camera|cam)[\s_-]*(\d+)", re.IGNORECASE)
DATE_WITH_MONTH_PATTERN = re.compile(
    r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{2,4})\b",
    re.IGNORECASE,
)
DATE_NUMERIC_PATTERN = re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b")

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def _normalize_plate(plate: str | None) -> str | None:
    if not plate:
        return None
    cleaned = re.sub(r"[^A-Za-z0-9]", "", plate).upper()
    if len(cleaned) < 6:
        return None
    return cleaned


def _extract_plate_number(message: str) -> str | None:
    candidates = []
    for match in INDIAN_PLATE_PATTERN.finditer(message.upper()):
        candidates.append(match.group(1))
    for match in re.finditer(r"([A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{1,4})", message.upper()):
        candidates.append(match.group(1))
    if not candidates:
        return None
    best = None
    for candidate in candidates:
        cleaned = _normalize_plate(candidate)
        if cleaned and len(cleaned) >= 8:
            best = cleaned
            break
    return best or _normalize_plate(candidates[0])


def _extract_camera_id(message: str) -> int | None:
    match = CAMERA_PATTERN.search(message)
    if match:
        return int(match.group(1))
    return None


def _parse_date_value(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%d-%m-%Y")
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def _extract_date_window(message: str) -> tuple[datetime | None, datetime | None]:
    text = message.lower()
    if "last 7 days" in text or "7 din" in text:
        end = datetime.utcnow()
        start = end - timedelta(days=7)
        return start, end
    if "last 30 days" in text or "30 din" in text:
        end = datetime.utcnow()
        start = end - timedelta(days=30)
        return start, end

    month_match = DATE_WITH_MONTH_PATTERN.search(message)
    if month_match:
        day, month_name, year = month_match.groups()
        month_number = MONTHS.get(month_name.lower())
        if month_number is not None:
            parsed_date = datetime(int(year), month_number, int(day))
            return parsed_date, parsed_date + timedelta(days=1)

    numeric_match = DATE_NUMERIC_PATTERN.search(message)
    if numeric_match:
        day, month, year = numeric_match.groups()
        year_value = int(year)
        if year_value < 100:
            year_value += 2000 if year_value < 50 else 1900
        parsed_date = datetime(year_value, int(month), int(day))
        return parsed_date, parsed_date + timedelta(days=1)

    return None, None


def _parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _build_metrics(events: list[VehicleEvent]) -> dict[str, Any]:
    if not events:
        return {"count": 0, "camera_count": 0, "first_seen": None, "last_seen": None}
    camera_ids = sorted({event.camera_id for event in events})
    return {
        "count": len(events),
        "camera_count": len(camera_ids),
        "first_seen": min(event.captured_at for event in events).isoformat(),
        "last_seen": max(event.captured_at for event in events).isoformat(),
    }


class CopilotChatRequest:
    def __init__(self, message: str, conversation_id: str | None = None):
        self.message = message.strip()
        self.conversation_id = conversation_id


class CopilotQueryService:
    def __init__(self, db: Session):
        self.db = db

    def _local_response(
        self,
        message: str,
        vehicle_number: str | None = None,
        camera_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        location: str | None = None,
        alert_status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        question = message.strip()
        plate_number = _normalize_plate(vehicle_number) or _extract_plate_number(question)
        camera_id = camera_id or _extract_camera_id(question)
        start_dt, end_dt = _extract_date_window(question)
        start_dt = _parse_iso_date(start_date) or start_dt
        end_dt = _parse_iso_date(end_date) or end_dt

        if not plate_number:
            return {
                "success": True,
                "answer": "Database mein is request ke liye sufficient records available nahi hain.",
                "data": {
                    "vehicle_number": None,
                    "events": [],
                    "blacklist_status": None,
                    "coverage_note": "No verifiable vehicle number was found in the request.",
                    "search_period": {"start": None, "end": None},
                },
                "metadata": {
                    "source": "database",
                    "records_count": 0,
                    "camera_filter": camera_id,
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }

        query = self.db.query(VehicleEvent).filter(VehicleEvent.plate_number.ilike(plate_number))
        if camera_id:
            query = query.filter(VehicleEvent.camera_id == camera_id)
        if start_dt:
            query = query.filter(VehicleEvent.captured_at >= start_dt)
        if end_dt:
            query = query.filter(VehicleEvent.captured_at <= end_dt)
        if location:
            query = query.join(Camera, VehicleEvent.camera_id == Camera.id).filter(
                Camera.name.ilike(f"%{location.strip()}%")
            )
        if alert_status:
            normalized_alert_status = alert_status.strip().lower()
            if normalized_alert_status in {"active", "open", "alert"}:
                query = query.filter(
                    self.db.query(Alert.plate_number)
                    .filter(Alert.plate_number == plate_number, Alert.resolved.is_(False))
                    .exists()
                )

        total_records = query.count()
        events = (
            query.order_by(VehicleEvent.captured_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        camera_ids = sorted({event.camera_id for event in events})
        camera_map = {
            camera.id: camera
            for camera in self.db.query(Camera).filter(Camera.id.in_(camera_ids)).all()
        }
        blacklist_entry = self.db.query(VehicleBlacklist).filter(VehicleBlacklist.plate_number == plate_number).first()
        related_alerts = self.db.query(Alert).filter(Alert.plate_number == plate_number).order_by(Alert.created_at.desc()).limit(5).all()

        if not events:
            return {
                "success": True,
                "answer": "Database mein is request ke liye sufficient records available nahi hain.",
                "data": {
                    "vehicle_number": plate_number,
                    "events": [],
                    "blacklist_status": None,
                    "coverage_note": "No authorized detections were found matching the requested plate and time window.",
                    "search_period": {"start": start_dt.isoformat() if start_dt else None, "end": end_dt.isoformat() if end_dt else None},
                },
                "metadata": {
                    "source": "database",
                    "records_count": 0,
                    "camera_filter": camera_id,
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }

        event_payload = []
        for event in events:
            camera = camera_map.get(event.camera_id)
            event_payload.append(
                {
                    "id": event.id,
                    "plate_number": event.plate_number,
                    "camera_id": event.camera_id,
                    "camera_name": camera.name if camera else "Unknown",
                    "latitude": event.latitude,
                    "longitude": event.longitude,
                    "confidence": float(event.confidence),
                    "captured_at": event.captured_at.isoformat(),
                    "image_url": event.image_url,
                }
            )

        summary = _build_metrics(events)
        summary["total_records"] = total_records
        blacklist_status = {
            "present": bool(blacklist_entry),
            "reason": blacklist_entry.reason if blacklist_entry else None,
        }
        alert_summary = [
            {
                "id": alert.id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
            }
            for alert in related_alerts
        ]

        latest_event = event_payload[-1]
        question_lower = question.lower()
        if "last" in question_lower or "latest" in question_lower or "aakhri" in question_lower:
            answer = (
                f"Vehicle {plate_number} ka latest authorized observation "
                f"{latest_event['camera_name']} par {latest_event['captured_at']} ko record hua tha."
            )
        elif "how many" in question_lower or "kitni baar" in question_lower or "count" in question_lower:
            answer = f"Vehicle {plate_number} ke liye selected filters mein {total_records} authorized detections mile."
        else:
            answer = (
                f"Vehicle {plate_number} ke liye authorized records {total_records} detections dikhate hain. "
                f"First observed at {summary['first_seen']} aur last observed at {summary['last_seen']}. "
                f"Camera coverage {summary['camera_count']} points par available hai. "
                f"Observed route sequence ko timeline ke roop mein data mein represent kiya gaya hai."
            )
        if blacklist_status["present"]:
            answer += f" Blacklist status also available: {blacklist_status['reason']}."
        if summary['count'] > 0 and summary['count'] < 5:
            answer += " Results depend on available camera coverage and are not interpreted as a complete journey beyond recorded observations."

        return {
            "success": True,
            "answer": answer,
            "data": {
                "vehicle_number": plate_number,
                "events": event_payload,
                "blacklist_status": blacklist_status,
                "alerts": alert_summary,
                "coverage_note": "Results are limited to authorized detections available in the current database and should be treated as observed events rather than guaranteed full-route travel.",
                "search_period": {
                    "start": start_dt.isoformat() if start_dt else None,
                    "end": end_dt.isoformat() if end_dt else None,
                },
                "metrics": summary,
            },
            "metadata": {
                "source": "database",
                "records_count": summary["count"],
                "total_records": total_records,
                "page": page,
                "page_size": page_size,
                "camera_filter": camera_id,
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

    def _llm_response(self, question: str, db_context: dict[str, Any]) -> dict[str, Any] | None:
        if not settings.openai_api_key and not settings.gemini_api_key:
            return None

        system_prompt = (
            "You are Trinetra AI Copilot. Use only the structured records provided from the project database. "
            "Never invent camera IDs, timestamps, routes, or ownership. If records are missing, say: "
            "Database mein is request ke liye sufficient records available nahi hain. "
            "Return valid JSON with keys: answer, evidence_summary."
        )
        try:
            context = json.dumps({"question": question, "records": db_context}, ensure_ascii=False)
            if settings.openai_api_key:
                payload = {
                    "model": settings.copilot_model or "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": context},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                }
                response = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json=payload,
                    timeout=20,
                )
            else:
                response = httpx.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{settings.copilot_model or 'gemini-3.6-flash'}:generateContent",
                    params={"key": settings.gemini_api_key},
                    json={"contents": [{"parts": [{"text": f"{system_prompt}\n\n{context}"}]}]},
                    timeout=20,
                )
            if response.status_code != 200:
                logger.warning("ai_provider_request_failed provider=%s status=%s", "openai" if settings.openai_api_key else "gemini", response.status_code)
                return None
            body = response.json()
            if settings.openai_api_key:
                content = body["choices"][0]["message"]["content"]
            else:
                content = body["candidates"][0]["content"]["parts"][0]["text"]
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                object_start = content.find("{")
                object_end = content.rfind("}")
                if object_start < 0 or object_end <= object_start:
                    return {"answer": content, "evidence_summary": "Generated from the authorized database context."} if content else None
                try:
                    parsed = json.loads(content[object_start:object_end + 1])
                except json.JSONDecodeError:
                    return {"answer": content, "evidence_summary": "Generated from the authorized database context."} if content else None
            if isinstance(parsed, dict) and parsed.get("answer"):
                return parsed
        except Exception as error:
            logger.warning("ai_provider_response_failed provider=%s error=%s", "openai" if settings.openai_api_key else "gemini", type(error).__name__)
            return None
        return None

    def handle_question(self, message: str, **filters: Any) -> dict[str, Any]:
        response = self._local_response(message, **filters)
        if not response["data"].get("events") and response["answer"].startswith("Database"):
            return response

        llm_response = self._llm_response(message, response["data"])
        if llm_response:
            response["answer"] = llm_response.get("answer") or response["answer"]
            response["metadata"]["ai_provider"] = "openai" if settings.openai_api_key else "gemini"
        return response
