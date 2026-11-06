from __future__ import annotations

import csv
import io
import math
import os
import re
import secrets
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from openpyxl import load_workbook
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import create_tables, get_db
from app.models import (
    Announcement,
    AdminAuditLog,
    BlueprintAsset,
    Building,
    ClassSchedule,
    Exam,
    ExamRoomAllocation,
    ExamSeat,
    FacultyRequest,
    IssueReport,
    LibraryPass,
    Room,
    RoleEnum,
    User,
)
from app.schemas import (
    AnnouncementCreate,
    AnnouncementResponse,
    CampusSummary,
    ClassScheduleCreate,
    ClassScheduleResponse,
    ExamCreate,
    ExamResponse,
    ExamSeatUpdate,
    FacultyRequestCreate,
    FacultyRequestResponse,
    IssueReportCreate,
    LibraryPassCreate,
    LoginRequest,
    LibraryPassVerify,
    RoomCreate,
    RoomAssistantRequest,
    RoomResponse,
    UserCreate,
    UserResponse,
)
from app.seed_data import seed_demo_data

app = FastAPI(title="DDUGU Smart Campus API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
CAMPUS_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def current_time(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Time must use HH:MM format") from exc


def validate_interval(start: str, end: str) -> tuple[time, time]:
    start_time, end_time = current_time(start), current_time(end)
    if start_time >= end_time:
        raise HTTPException(status_code=422, detail="End time must be after start time")
    return start_time, end_time


def parse_natural_time(value: str) -> str:
    hour = int(re.match(r"\d+", value).group())  # The match is guaranteed by the caller's pattern.
    minute_match = re.search(r":(\d{2})", value)
    minute = int(minute_match.group(1)) if minute_match else 0
    meridiem = value[-2:].lower()
    hour = hour % 12 + (12 if meridiem == "pm" else 0)
    return f"{hour:02d}:{minute:02d}"


def overlaps(start: str, end: str, other_start: str, other_end: str) -> bool:
    return current_time(start) < current_time(other_end) and current_time(other_start) < current_time(end)


def ensure_room_free(
    db: Session,
    room_id: int,
    on_date: date,
    start: str,
    end: str,
    *,
    exclude_request_id: Optional[int] = None,
    exclude_exam_id: Optional[int] = None,
) -> None:
    validate_interval(start, end)
    day = DAYS[on_date.weekday()]
    schedules = db.query(ClassSchedule).filter(
        ClassSchedule.room_id == room_id,
        ClassSchedule.day == day,
    ).all()
    if any(overlaps(start, end, row.start_time, row.end_time) for row in schedules):
        raise HTTPException(status_code=409, detail="Room conflicts with a scheduled class")

    requests = db.query(FacultyRequest).filter(
        FacultyRequest.room_id == room_id,
        FacultyRequest.requested_date == on_date,
        FacultyRequest.status == "approved",
    ).all()
    if any(
        row.id != exclude_request_id and overlaps(start, end, row.start_time, row.end_time)
        for row in requests
    ):
        raise HTTPException(status_code=409, detail="Room conflicts with another faculty request")

    allocated_exam_ids = [
        allocation.exam_id
        for allocation in db.query(ExamRoomAllocation).filter(ExamRoomAllocation.room_id == room_id).all()
    ]
    exams = db.query(Exam).filter(
        Exam.exam_date == on_date,
        or_(Exam.room_id == room_id, Exam.id.in_(allocated_exam_ids or [-1])),
    ).all()
    if any(
        row.id != exclude_exam_id and overlaps(start, end, row.start_time, row.end_time)
        for row in exams
    ):
        raise HTTPException(status_code=409, detail="Room conflicts with an examination")


def ensure_faculty_and_section_free(
    db: Session,
    faculty_id: int,
    branch: str,
    year: int,
    section: str,
    batch: Optional[str],
    on_date: date,
    start: str,
    end: str,
) -> None:
    for row in db.query(ClassSchedule).filter(ClassSchedule.day == DAYS[on_date.weekday()]).all():
        if not overlaps(start, end, row.start_time, row.end_time):
            continue
        if row.instructor_id == faculty_id:
            raise HTTPException(status_code=409, detail="Faculty member has another class at this time")
        if (row.branch, row.year, row.section) == (branch, year, section):
            if not batch or not row.batch or row.batch == batch:
                raise HTTPException(status_code=409, detail="Student section has another class at this time")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if user is None:
        raise credentials_exception
    return user


def require_roles(*roles: str):
    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return current_user

    return dependency


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        branch=user.branch,
        year=user.year,
        section=user.section,
        roll_number=user.roll_number,
        phone=user.phone,
    )


def venue_is_released(exam: Exam) -> bool:
    release_at = datetime.combine(exam.exam_date, current_time(exam.start_time), tzinfo=CAMPUS_TIMEZONE) - timedelta(hours=1)
    return datetime.now(CAMPUS_TIMEZONE) >= release_at


def room_response(room: Room) -> RoomResponse:
    return RoomResponse(
        id=room.id,
        code=room.code,
        room_type=room.room_type,
        floor=room.floor,
        capacity=room.capacity,
        facilities=room.facilities or "",
        usage_permission=room.usage_permission,
        examination_suitable=room.examination_suitable,
        building_name=room.building.name,
    )


def schedule_response(row: ClassSchedule) -> ClassScheduleResponse:
    return ClassScheduleResponse(
        id=row.id,
        title=row.title,
        subject=row.subject,
        day=row.day,
        start_time=row.start_time,
        end_time=row.end_time,
        room_code=row.room.code,
        room_name=row.room.building.name,
        instructor=row.instructor.name,
        branch=row.branch,
        year=row.year,
        section=row.section,
    )


def request_response(row: FacultyRequest) -> FacultyRequestResponse:
    return FacultyRequestResponse(
        id=row.id,
        faculty_name=row.faculty.name,
        room_code=row.room.code,
        requested_date=row.requested_date,
        start_time=row.start_time,
        end_time=row.end_time,
        subject=row.subject,
        purpose=row.purpose,
        branch=row.branch,
        year=row.year,
        section=row.section,
        batch=row.batch,
        expected_attendance=row.expected_attendance,
        notes=row.notes,
        status=row.status,
        created_at=row.created_at,
    )


def announcement_response(row: Announcement) -> AnnouncementResponse:
    return AnnouncementResponse(
        id=row.id,
        title=row.title,
        message=row.message,
        audience=row.audience,
        created_at=row.created_at,
    )


def announcement_query(db: Session, user: User) -> list[Announcement]:
    rows = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    if user.role != RoleEnum.STUDENT.value:
        return rows
    return [row for row in rows if row.audience in ("all", user.branch)]


def write_audit(
    db: Session,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: int,
    details: Optional[str] = None,
) -> None:
    db.add(
        AdminAuditLog(
            actor_id=actor.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
    )


def exam_response(
    exam: Exam,
    *,
    released: bool = False,
    seat_number: Optional[str] = None,
    seat_room: Optional[Room] = None,
) -> ExamResponse:
    release_at = datetime.combine(
        exam.exam_date,
        current_time(exam.start_time),
        tzinfo=CAMPUS_TIMEZONE,
    ) - timedelta(hours=1)
    server_now = datetime.now(CAMPUS_TIMEZONE)
    allocation_count = len(exam.room_allocations)
    return ExamResponse(
        id=exam.id,
        title=exam.title,
        subject=exam.subject,
        exam_date=exam.exam_date,
        start_time=exam.start_time,
        end_time=exam.end_time,
        building_name=(seat_room.building.name if seat_room else exam.building.name) if released else "Details available 1 hour before exam",
        room_code=seat_room.code if released and seat_room else exam.room.code if released and allocation_count <= 1 and exam.room else None,
        room_floor=seat_room.floor if released and seat_room else exam.room.floor if released and allocation_count <= 1 and exam.room else None,
        published=exam.published,
        venue_released=released,
        seat_number=seat_number if released else None,
        reporting_time=exam.reporting_time,
        release_at=release_at,
        server_time=server_now,
        seconds_until_release=max(0, math.ceil((release_at - server_now).total_seconds())),
    )


@app.on_event("startup")
def startup_event() -> None:
    create_tables()
    seed_demo_data()


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "DDUGU Smart Campus API"}


@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not user.is_active or not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = jwt.encode(
        {
            "sub": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return {"access_token": token, "token_type": "bearer", "user": user_response(user)}


@app.get("/api/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return user_response(current_user)


@app.get("/api/dashboard")
def get_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    notices = announcement_query(db, current_user)[:5]
    if current_user.role == RoleEnum.STUDENT.value:
        timetable = db.query(ClassSchedule).filter(
            ClassSchedule.branch == current_user.branch,
            ClassSchedule.year == current_user.year,
            ClassSchedule.section == current_user.section,
        ).order_by(ClassSchedule.day, ClassSchedule.start_time).all()
        seats = db.query(ExamSeat).filter(ExamSeat.student_id == current_user.id).all()
        exams = [
            db.query(Exam).filter(Exam.id == seat.exam_id, Exam.published.is_(True)).first()
            for seat in seats
        ]
        exams = [exam for exam in exams if exam is not None]
        passes = db.query(LibraryPass).filter(LibraryPass.student_id == current_user.id).all()
        return {
            "role": current_user.role,
            "summary": {
                "timetable_count": len(timetable),
                "exam_count": len(exams),
                "active_passes": sum(item.status == "active" and item.expiry_date >= date.today() for item in passes),
            },
            "timetable": [
                {
                    "id": item.id,
                    "title": item.title,
                    "subject": item.subject,
                    "day": item.day,
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                    "room_code": item.room.code,
                    "instructor": item.instructor.name,
                }
                for item in timetable
            ],
            "exams": [
                exam_response(
                    exam,
                    released=venue_is_released(exam),
                    seat_number=next((seat.seat_number for seat in seats if seat.exam_id == exam.id), None),
                    seat_room=next((seat.room for seat in seats if seat.exam_id == exam.id), None),
                ).model_dump(mode="json")
                for exam in exams
            ],
            "announcements": [announcement_response(item).model_dump(mode="json") for item in notices],
            "library_passes": [
                {
                    "id": item.id,
                    "pass_code": item.pass_code,
                    "status": item.status if item.expiry_date >= date.today() else "expired",
                    "expiry_date": item.expiry_date.isoformat(),
                }
                for item in passes
            ],
            "reports": [
                {"id": row.id, "category": row.category, "details": row.details, "status": row.status}
                for row in db.query(IssueReport).filter(IssueReport.student_id == current_user.id).order_by(IssueReport.created_at.desc()).limit(5)
            ],
        }

    if current_user.role == RoleEnum.FACULTY.value:
        requests = db.query(FacultyRequest).filter(
            FacultyRequest.faculty_id == current_user.id
        ).order_by(FacultyRequest.created_at.desc()).all()
        classes = db.query(ClassSchedule).filter(ClassSchedule.instructor_id == current_user.id).all()
        return {
            "role": current_user.role,
            "summary": {
                "my_requests": len(requests),
                "available_rooms": db.query(Room).filter(Room.is_active.is_(True)).count(),
            },
            "timetable": [schedule_response(item).model_dump(mode="json") for item in classes],
            "requests": [request_response(item).model_dump(mode="json") for item in requests],
            "rooms": [room_response(item).model_dump(mode="json") for item in db.query(Room).filter(Room.is_active.is_(True)).all()],
            "announcements": [announcement_response(item).model_dump(mode="json") for item in notices],
        }

    summary = {
        "total_rooms": db.query(Room).count(),
        "available_rooms": db.query(Room).filter(Room.is_active.is_(True)).count(),
        "active_exams": db.query(Exam).count(),
        "announcements": db.query(Announcement).count(),
        "pending_requests": db.query(FacultyRequest).filter(FacultyRequest.status == "pending").count(),
        "students": db.query(User).filter(User.role == RoleEnum.STUDENT.value).count(),
        "faculty": db.query(User).filter(User.role == RoleEnum.FACULTY.value).count(),
    }
    return {
        "role": current_user.role,
        "summary": summary,
        "announcements": [announcement_response(item).model_dump(mode="json") for item in notices],
        "requests": [
            {
                "id": item.id,
                "faculty_name": item.faculty.name,
                "room_code": item.room.code,
                "purpose": item.purpose,
                "requested_date": item.requested_date.isoformat(),
                "start_time": item.start_time,
                "end_time": item.end_time,
                "status": item.status,
            }
            for item in db.query(FacultyRequest).order_by(FacultyRequest.created_at.desc()).limit(10)
        ],
        "reports": [
            {"id": row.id, "student": row.student.name, "category": row.category, "details": row.details, "status": row.status}
            for row in db.query(IssueReport).order_by(IssueReport.created_at.desc()).limit(10)
        ],
    }


@app.get("/api/buildings")
def list_buildings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    return [
        {
            "id": building.id,
            "name": building.name,
            "code": building.code,
            "location": building.location,
            "description": building.description,
            "rooms": [room_response(room).model_dump(mode="json") for room in building.rooms],
            "blueprints": [
                {"id": asset.id, "filename": asset.filename, "media_type": asset.media_type}
                for asset in db.query(BlueprintAsset).filter(BlueprintAsset.building_id == building.id).all()
            ],
        }
        for building in db.query(Building).all()
    ]


@app.post("/api/admin/buildings/{building_id}/blueprints", status_code=status.HTTP_201_CREATED)
async def upload_blueprint(
    building_id: int,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> dict[str, object]:
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_types = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
    if extension not in media_types:
        raise HTTPException(status_code=415, detail="Blueprints must be PDF, PNG, or JPEG files")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Blueprint size must not exceed 10 MB")
    signatures = {
        "pdf": content.startswith(b"%PDF-"),
        "png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "jpg": content.startswith(b"\xff\xd8\xff"),
        "jpeg": content.startswith(b"\xff\xd8\xff"),
    }
    if not content or not signatures[extension]:
        raise HTTPException(status_code=415, detail="File content does not match its PDF or image extension")
    asset = BlueprintAsset(
        building_id=building.id,
        filename=filename[:255],
        media_type=media_types[extension],
        content=content,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"id": asset.id, "filename": asset.filename, "media_type": asset.media_type}


@app.get("/api/buildings/{building_id}/blueprints/{asset_id}")
def download_blueprint(
    building_id: int,
    asset_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    asset = db.query(BlueprintAsset).filter(
        BlueprintAsset.id == asset_id,
        BlueprintAsset.building_id == building_id,
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    safe_extension = "pdf" if asset.media_type == "application/pdf" else "png" if asset.media_type == "image/png" else "jpg"
    return Response(
        content=asset.content,
        media_type=asset.media_type,
        headers={
            "Content-Disposition": f'inline; filename="campus-blueprint-{asset.id}.{safe_extension}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/api/rooms", response_model=list[RoomResponse])
def list_rooms(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    on_date: Optional[date] = Query(default=None, alias="date"),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    min_capacity: int = Query(default=1, ge=1, le=1000),
    building_id: Optional[int] = None,
    floor: Optional[str] = None,
    facility: Optional[str] = None,
):
    if bool(start_time) != bool(end_time):
        raise HTTPException(status_code=422, detail="Provide both start_time and end_time")
    if start_time and end_time and on_date:
        validate_interval(start_time, end_time)
    query = db.query(Room).filter(Room.is_active.is_(True), Room.capacity >= min_capacity)
    if building_id:
        query = query.filter(Room.building_id == building_id)
    if floor:
        query = query.filter(Room.floor == floor)
    rooms = query.all()
    if facility:
        rooms = [room for room in rooms if facility.lower() in (room.facilities or "").lower()]
    if start_time and end_time and on_date:
        available: list[Room] = []
        for room in rooms:
            try:
                ensure_room_free(db, room.id, on_date, start_time, end_time)
            except HTTPException as exc:
                if exc.status_code != 409:
                    raise
            else:
                available.append(room)
        rooms = available
    return [room_response(room) for room in rooms]


@app.post("/api/assistant/rooms")
def recommend_rooms(
    payload: RoomAssistantRequest,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.FACULTY.value, RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    query_text = payload.query.strip()
    times = re.findall(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b", query_text, flags=re.IGNORECASE)
    if len(times) < 2:
        raise HTTPException(status_code=422, detail="Include a time range, for example 'between 11 AM and 1 PM'")
    start_time, end_time = parse_natural_time(times[0]), parse_natural_time(times[1])
    validate_interval(start_time, end_time)

    text = query_text.lower()
    campus_today = datetime.now(CAMPUS_TIMEZONE).date()
    if "tomorrow" in text:
        requested_date = campus_today + timedelta(days=1)
    elif "today" in text:
        requested_date = campus_today
    else:
        date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
        if not date_match:
            raise HTTPException(status_code=422, detail="Include 'today', 'tomorrow', or a date in YYYY-MM-DD format")
        try:
            requested_date = date.fromisoformat(date_match.group())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid requested date") from exc

    capacity_match = re.search(r"\b(\d{1,4})\s+(?:[\w-]+\s+){0,3}(?:students?|people|seats)\b", text)
    capacity = int(capacity_match.group(1)) if capacity_match else 1
    branch = next((name for name in ("cse", "ai ml", "ai-ml", "ai ds", "ai-ds", "ece", "me", "it") if name in text), None)
    year_match = re.search(r"\b(first|second|third|fourth|[1-4](?:st|nd|rd|th)?)[\s-]*(?:year|yr)\b", text)
    year = {"first": 1, "second": 2, "third": 3, "fourth": 4}.get(year_match.group(1)) if year_match else None
    if year_match and year is None:
        year = int(year_match.group(1)[0])
    wanted_building = "DB" if "deeksha" in text else "IET" if re.search(r"\biet\b", text) else None
    wanted_facilities = [
        term for term in ("projector", "whiteboard", "computers", "computer", "ac")
        if term in text
    ]

    candidates: list[tuple[float, Room]] = []
    rooms = db.query(Room).filter(Room.is_active.is_(True), Room.capacity >= capacity).all()
    for room in rooms:
        if room.room_type in {"office", "library"}:
            continue
        if room.usage_permission != "all":
            continue
        building_code = room.building.code
        if wanted_building and building_code != wanted_building:
            continue
        facilities = (room.facilities or "").lower()
        if any(term not in facilities for term in wanted_facilities):
            continue
        try:
            ensure_room_free(db, room.id, requested_date, start_time, end_time)
        except HTTPException as exc:
            if exc.status_code == 409:
                continue
            raise
        capacity_score = max(0, 25 - (room.capacity - capacity) / max(room.capacity, 1) * 25)
        facility_score = 20 if wanted_facilities else 0
        building_score = 10 if wanted_building and building_code == wanted_building else 0
        score = 40 + capacity_score + facility_score + building_score
        candidates.append((score, room))

    candidates.sort(key=lambda result: (-result[0], result[1].capacity))
    recommendations = [
        {
            "room": room.code,
            "building": room.building.name,
            "floor": room.floor,
            "capacity": room.capacity,
            "facilities": room.facilities,
            "score": round(score, 1),
            "explanation": f"Available {requested_date.isoformat()} from {start_time} to {end_time}; capacity {room.capacity} meets the {capacity}-person requirement.",
        }
        for score, room in candidates[:5]
    ]
    return {
        "parsed": {
            "date": requested_date.isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "minimum_capacity": capacity,
            "branch": branch,
            "year": year,
            "building_preference": wanted_building,
            "required_facilities": wanted_facilities,
        },
        "recommendations": recommendations,
        "message": "No suitable rooms are available for those constraints." if not recommendations else "Recommendations are ranked by availability and capacity fit. Booking approval is still required.",
    }


@app.post("/api/admin/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
):
    building = db.query(Building).filter(Building.id == payload.building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    if db.query(Room).filter(Room.building_id == payload.building_id, Room.code == payload.code).first():
        raise HTTPException(status_code=409, detail="Room code already exists in this building")
    values = payload.model_dump(exclude={"building_id"})
    room = Room(building_id=payload.building_id, **values)
    db.add(room)
    db.flush()
    write_audit(db, current_user, "create", "room", room.id, f"Room {room.code} added")
    db.commit()
    db.refresh(room)
    return room_response(room)


@app.put("/api/admin/rooms/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    payload: RoomCreate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    building = db.query(Building).filter(Building.id == payload.building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    duplicate = db.query(Room).filter(
        Room.building_id == payload.building_id,
        Room.code == payload.code,
        Room.id != room_id,
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Room code already exists in this building")
    for key, value in payload.model_dump(exclude={"building_id"}).items():
        setattr(room, key, value)
    room.building_id = payload.building_id
    write_audit(db, current_user, "update", "room", room.id, f"Room {room.code} updated")
    db.commit()
    db.refresh(room)
    return room_response(room)


@app.get("/api/timetable", response_model=list[ClassScheduleResponse])
def list_timetable(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    query = db.query(ClassSchedule)
    if current_user.role == RoleEnum.STUDENT.value:
        query = query.filter(
            ClassSchedule.branch == current_user.branch,
            ClassSchedule.year == current_user.year,
            ClassSchedule.section == current_user.section,
        )
    elif current_user.role == RoleEnum.FACULTY.value:
        query = query.filter(ClassSchedule.instructor_id == current_user.id)
    return [schedule_response(row) for row in query.order_by(ClassSchedule.day, ClassSchedule.start_time).all()]


@app.post("/api/admin/timetable", response_model=ClassScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_timetable_entry(
    payload: ClassScheduleCreate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
):
    start, end = validate_interval(payload.start_time, payload.end_time)
    room = db.query(Room).filter(Room.id == payload.room_id, Room.is_active.is_(True)).first()
    instructor = db.query(User).filter(User.id == payload.instructor_id, User.role == RoleEnum.FACULTY.value).first()
    if not room or not instructor:
        raise HTTPException(status_code=404, detail="Active room or faculty member not found")
    classes = db.query(ClassSchedule).filter(ClassSchedule.day == payload.day).all()
    for row in classes:
        if not (start < current_time(row.end_time) and current_time(row.start_time) < end):
            continue
        if row.room_id == payload.room_id:
            raise HTTPException(status_code=409, detail="Room is already assigned at this time")
        if row.instructor_id == payload.instructor_id:
            raise HTTPException(status_code=409, detail="Faculty member already has a class at this time")
        if (row.branch, row.year, row.section) == (payload.branch, payload.year, payload.section):
            raise HTTPException(status_code=409, detail="Student section already has a class at this time")
    row = ClassSchedule(**payload.model_dump())
    db.add(row)
    db.flush()
    write_audit(db, current_user, "create", "timetable", row.id, f"Class {row.title} scheduled")
    db.commit()
    db.refresh(row)
    return schedule_response(row)


@app.get("/api/exams", response_model=list[ExamResponse])
def list_exams(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    if current_user.role == RoleEnum.ADMIN.value:
        exams = db.query(Exam).order_by(Exam.exam_date).all()
        return [exam_response(exam, released=True) for exam in exams]
    if current_user.role == RoleEnum.FACULTY.value:
        exams = db.query(Exam).filter(Exam.published.is_(True)).order_by(Exam.exam_date).all()
        return [exam_response(exam, released=True) for exam in exams]
    seats = db.query(ExamSeat).filter(ExamSeat.student_id == current_user.id).all()
    result: list[ExamResponse] = []
    for seat in seats:
        exam = db.query(Exam).filter(Exam.id == seat.exam_id, Exam.published.is_(True)).first()
        if not exam:
            continue
        result.append(
            exam_response(
                exam,
                released=venue_is_released(exam),
                seat_number=seat.seat_number,
                seat_room=seat.room,
            )
        )
    return sorted(result, key=lambda exam: exam.exam_date)


@app.post("/api/admin/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: ExamCreate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
):
    validate_interval(payload.start_time, payload.end_time)
    if len(set(payload.room_ids)) != len(payload.room_ids):
        raise HTTPException(status_code=422, detail="A room can only be selected once")
    selected_rooms = db.query(Room).filter(
        Room.id.in_(payload.room_ids),
        Room.is_active.is_(True),
        Room.examination_suitable.is_(True),
    ).all()
    rooms_by_id = {room.id: room for room in selected_rooms}
    if len(rooms_by_id) != len(payload.room_ids):
        raise HTTPException(status_code=400, detail="Select an active room suitable for examinations")
    rooms = [rooms_by_id[room_id] for room_id in payload.room_ids]
    for room in rooms:
        if room.usage_permission != "all" and not (
            room.usage_permission == "library_and_exam" and room.room_type == "library"
        ):
            raise HTTPException(status_code=403, detail=f"Room {room.code} does not permit examination use")
        ensure_room_free(db, room.id, payload.exam_date, payload.start_time, payload.end_time)
    students = db.query(User).filter(
        User.role == RoleEnum.STUDENT.value,
        User.is_active.is_(True),
        User.branch == payload.branch,
        User.year == payload.year,
        User.section == payload.section,
    ).order_by(User.id).all()
    if not students:
        raise HTTPException(status_code=400, detail="No students found for this branch, year, and section")
    total_capacity = sum(room.capacity for room in rooms)
    if len(students) > total_capacity:
        raise HTTPException(status_code=400, detail=f"Selected room capacity ({total_capacity}) is below enrollment ({len(students)})")
    exam = Exam(
        title=payload.title,
        subject=payload.subject,
        exam_date=payload.exam_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        reporting_time=payload.reporting_time,
        building_id=rooms[0].building_id,
        room_id=rooms[0].id,
        published=payload.publish,
        branch=payload.branch,
        year=payload.year,
        section=payload.section,
    )
    db.add(exam)
    db.flush()
    for room in rooms:
        db.add(ExamRoomAllocation(exam_id=exam.id, room_id=room.id))
    student_index = 0
    for room in rooms:
        seats_in_room = min(room.capacity, len(students) - student_index)
        for seat_index in range(1, seats_in_room + 1):
            db.add(
                ExamSeat(
                    exam_id=exam.id,
                    student_id=students[student_index].id,
                    room_id=room.id,
                    seat_number=f"A-{seat_index:03d}",
                )
            )
            student_index += 1
        if student_index >= len(students):
            break
    write_audit(db, current_user, "create", "exam", exam.id, f"Exam {exam.title} created; {len(students)} seats allocated across {len(rooms)} rooms")
    db.commit()
    db.refresh(exam)
    return exam_response(exam, released=True)


@app.patch("/api/admin/exams/{exam_id}/publish")
def publish_exam(
    exam_id: int,
    published: bool,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam.published = published
    write_audit(db, current_user, "publish" if published else "unpublish", "exam", exam.id)
    db.commit()
    return {"id": exam.id, "published": exam.published}


@app.get("/api/admin/exams/{exam_id}/allocations")
def exam_allocations(
    exam_id: int,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    seats = db.query(ExamSeat).filter(ExamSeat.exam_id == exam.id).join(User).order_by(
        ExamSeat.room_id,
        ExamSeat.seat_number,
    ).all()
    rooms = db.query(ExamRoomAllocation).filter(ExamRoomAllocation.exam_id == exam.id).all()
    return {
        "exam_id": exam.id,
        "title": exam.title,
        "allocated": len(seats),
        "rooms": [
            {
                "room_id": allocation.room.id,
                "room": allocation.room.code,
                "building": allocation.room.building.name,
                "capacity": allocation.room.capacity,
                "assigned": sum(seat.room_id == allocation.room.id for seat in seats),
                "students": [
                    {
                        "name": seat.student.name,
                        "roll_number": seat.student.roll_number,
                        "branch": seat.student.branch,
                        "seat_number": seat.seat_number,
                    }
                    for seat in seats
                    if seat.room_id == allocation.room.id
                ],
            }
            for allocation in rooms
        ],
    }


@app.patch("/api/admin/exams/{exam_id}/seats/{seat_id}")
def update_exam_seat(
    exam_id: int,
    seat_id: int,
    payload: ExamSeatUpdate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    seat = db.query(ExamSeat).filter(ExamSeat.id == seat_id, ExamSeat.exam_id == exam_id).first()
    allocation = db.query(ExamRoomAllocation).filter(
        ExamRoomAllocation.exam_id == exam_id,
        ExamRoomAllocation.room_id == payload.room_id,
    ).first()
    if not exam or not seat:
        raise HTTPException(status_code=404, detail="Exam or seat allocation not found")
    if not allocation:
        raise HTTPException(status_code=400, detail="Room is not part of this exam allocation")
    duplicate = db.query(ExamSeat).filter(
        ExamSeat.exam_id == exam_id,
        ExamSeat.room_id == payload.room_id,
        ExamSeat.seat_number == payload.seat_number,
        ExamSeat.id != seat_id,
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Seat is already assigned")
    room = allocation.room
    if seat.room_id != room.id and db.query(ExamSeat).filter(
        ExamSeat.exam_id == exam_id,
        ExamSeat.room_id == room.id,
    ).count() >= room.capacity:
        raise HTTPException(status_code=409, detail="Room has no remaining capacity")
    ensure_room_free(
        db,
        room.id,
        exam.exam_date,
        exam.start_time,
        exam.end_time,
        exclude_exam_id=exam.id,
    )
    seat.room_id = room.id
    seat.seat_number = payload.seat_number
    write_audit(db, current_user, "reallocate", "exam_seat", seat.id, f"Seat reassigned to {room.code} {payload.seat_number}")
    db.commit()
    return {"seat_id": seat.id, "room": room.code, "seat_number": seat.seat_number}


@app.get("/api/admin/exams/{exam_id}/allocations.csv")
def export_exam_allocations(
    exam_id: int,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(("Student", "Roll number", "Branch", "Room", "Building", "Seat"))
    seats = db.query(ExamSeat).filter(ExamSeat.exam_id == exam.id).join(User).order_by(
        ExamSeat.room_id,
        ExamSeat.seat_number,
    ).all()
    for seat in seats:
        writer.writerow((seat.student.name, seat.student.roll_number, seat.student.branch, seat.room.code, seat.room.building.name, seat.seat_number))
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="exam-{exam.id}-allocations.csv"'},
    )


@app.get("/api/announcements", response_model=list[AnnouncementResponse])
def list_announcements(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return [announcement_response(row) for row in announcement_query(db, current_user)]


@app.post("/api/admin/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
):
    row = Announcement(**payload.model_dump())
    db.add(row)
    db.flush()
    write_audit(db, current_user, "publish", "announcement", row.id, row.title)
    db.commit()
    db.refresh(row)
    return announcement_response(row)


@app.post("/api/faculty-requests", response_model=FacultyRequestResponse, status_code=status.HTTP_201_CREATED)
def create_faculty_request(
    payload: FacultyRequestCreate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.FACULTY.value))],
    db: Annotated[Session, Depends(get_db)],
):
    room = db.query(Room).filter(Room.id == payload.room_id, Room.is_active.is_(True)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Active room not found")
    if room.capacity < payload.expected_attendance:
        raise HTTPException(status_code=409, detail="Room capacity is below expected attendance")
    if room.usage_permission != "all" and not (
        room.usage_permission == "library_and_exam" and "exam" in payload.purpose.lower()
    ):
        raise HTTPException(status_code=403, detail="Room usage does not permit this request")
    required = {item.strip().lower() for item in (payload.required_facilities or "").split(",") if item.strip()}
    available = {item.strip().lower() for item in (room.facilities or "").split(",") if item.strip()}
    if not required.issubset(available):
        raise HTTPException(status_code=409, detail="Selected room does not have all required facilities")
    ensure_room_free(db, room.id, payload.requested_date, payload.start_time, payload.end_time)
    ensure_faculty_and_section_free(
        db,
        current_user.id,
        payload.branch,
        payload.year,
        payload.section,
        payload.batch,
        payload.requested_date,
        payload.start_time,
        payload.end_time,
    )
    row = FacultyRequest(faculty_id=current_user.id, status="pending", **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return request_response(row)


@app.get("/api/faculty-requests", response_model=list[FacultyRequestResponse])
def list_faculty_requests(
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value, RoleEnum.FACULTY.value))],
    db: Annotated[Session, Depends(get_db)],
):
    query = db.query(FacultyRequest)
    if current_user.role == RoleEnum.FACULTY.value:
        query = query.filter(FacultyRequest.faculty_id == current_user.id)
    return [request_response(row) for row in query.order_by(FacultyRequest.created_at.desc()).all()]


@app.post("/api/faculty-requests/{request_id}/decision")
def decide_request(
    request_id: int,
    decision: str = Query(..., pattern="^(approved|rejected)$"),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN.value)),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    row = db.query(FacultyRequest).filter(FacultyRequest.id == request_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Faculty request not found")
    if row.status != "pending":
        raise HTTPException(status_code=409, detail="Only pending requests can be decided")
    if decision == "approved":
        ensure_room_free(
            db,
            row.room_id,
            row.requested_date,
            row.start_time,
            row.end_time,
            exclude_request_id=row.id,
        )
        if row.expected_attendance and row.room.capacity < row.expected_attendance:
            raise HTTPException(status_code=409, detail="Room capacity is below expected attendance")
        if row.branch and row.year and row.section:
            ensure_faculty_and_section_free(
                db,
                row.faculty_id,
                row.branch,
                row.year,
                row.section,
                row.batch,
                row.requested_date,
                row.start_time,
                row.end_time,
            )
            db.add(
                ClassSchedule(
                    title=row.subject or row.purpose,
                    subject=row.subject or row.purpose,
                    day=DAYS[row.requested_date.weekday()],
                    start_time=row.start_time,
                    end_time=row.end_time,
                    room_id=row.room_id,
                    instructor_id=row.faculty_id,
                    branch=row.branch,
                    year=row.year,
                    section=row.section,
                    batch=row.batch,
                )
            )
    row.status = decision
    if decision == "approved" and row.branch and row.year and row.section:
        db.flush()
    write_audit(db, current_user, decision, "faculty_request", row.id)
    db.commit()
    return {"message": "Request updated", "status": decision}


@app.get("/api/library-passes")
def list_library_passes(
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value, RoleEnum.STUDENT.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    query = db.query(LibraryPass)
    if current_user.role == RoleEnum.STUDENT.value:
        query = query.filter(LibraryPass.student_id == current_user.id)
    return [
        {
            "id": row.id,
            "student_id": row.student_id,
            "student_name": row.student.name,
            "pass_code": row.pass_code,
            "issue_date": row.issue_date.isoformat(),
            "expiry_date": row.expiry_date.isoformat(),
            "status": row.status if row.expiry_date >= date.today() else "expired",
        }
        for row in query.order_by(LibraryPass.expiry_date.desc()).all()
    ]


@app.post("/api/admin/library-passes", status_code=status.HTTP_201_CREATED)
def issue_library_pass(
    payload: LibraryPassCreate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    student = db.query(User).filter(User.id == payload.student_id, User.role == RoleEnum.STUDENT.value).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if payload.expiry_date < date.today():
        raise HTTPException(status_code=422, detail="Expiry date must be today or later")
    code = f"LIB-{date.today():%Y%m%d}-{secrets.token_hex(6).upper()}"
    row = LibraryPass(student_id=student.id, pass_code=code, expiry_date=payload.expiry_date, status="active")
    db.add(row)
    db.flush()
    write_audit(db, current_user, "issue", "library_pass", row.id, f"Pass issued to student {student.id}")
    db.commit()
    db.refresh(row)
    return {"id": row.id, "pass_code": row.pass_code, "expiry_date": row.expiry_date.isoformat(), "status": row.status}


@app.post("/api/library-passes/verify")
def verify_library_pass(
    payload: LibraryPassVerify,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = db.query(LibraryPass).filter(LibraryPass.pass_code == payload.pass_code).first()
    if not row:
        raise HTTPException(status_code=404, detail="Library pass not found")
    valid = row.status == "active" and row.expiry_date >= date.today()
    return {
        "valid": valid,
        "pass_code": row.pass_code,
        "student_name": row.student.name,
        "roll_number": row.student.roll_number,
        "expiry_date": row.expiry_date.isoformat(),
        "status": row.status if row.expiry_date >= date.today() else "expired",
    }


@app.patch("/api/admin/library-passes/{pass_id}/revoke")
def revoke_library_pass(
    pass_id: int,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    row = db.query(LibraryPass).filter(LibraryPass.id == pass_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Library pass not found")
    row.status = "revoked"
    write_audit(db, current_user, "revoke", "library_pass", row.id)
    db.commit()
    return {"status": row.status}


@app.post("/api/student/reports", status_code=status.HTTP_201_CREATED)
def create_issue_report(
    payload: IssueReportCreate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.STUDENT.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = IssueReport(student_id=current_user.id, category=payload.category, details=payload.details)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "category": row.category, "details": row.details, "status": row.status}


@app.get("/api/admin/reports")
def list_issue_reports(
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    return [
        {
            "id": row.id,
            "student": row.student.name,
            "category": row.category,
            "details": row.details,
            "status": row.status,
            "created_at": row.created_at.isoformat(),
        }
        for row in db.query(IssueReport).order_by(IssueReport.created_at.desc()).all()
    ]


@app.patch("/api/admin/reports/{report_id}/resolve")
def resolve_issue(
    report_id: int,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    row = db.query(IssueReport).filter(IssueReport.id == report_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Issue report not found")
    row.status = "resolved"
    row.resolved_at = datetime.utcnow()
    write_audit(db, current_user, "resolve", "student_report", row.id)
    db.commit()
    return {"status": row.status}


@app.get("/api/admin/users", response_model=list[UserResponse])
def list_users(
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
    role: Optional[str] = None,
):
    query = db.query(User)
    if role:
        if role not in {item.value for item in RoleEnum}:
            raise HTTPException(status_code=422, detail="Invalid role")
        query = query.filter(User.role == role)
    return [user_response(row) for row in query.order_by(User.name).all()]


@app.post("/api/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
):
    email = payload.email.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=422, detail="Provide a valid email address")
    if payload.role == RoleEnum.STUDENT.value and not all((payload.branch, payload.year, payload.section, payload.roll_number)):
        raise HTTPException(status_code=422, detail="Students require branch, year, section, and roll number")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    values = payload.model_dump(exclude={"email", "password"})
    user = User(email=email, password_hash=pwd_context.hash(payload.password), **values)
    db.add(user)
    db.flush()
    write_audit(db, current_user, "create", "user", user.id, f"Created {user.role} account")
    db.commit()
    db.refresh(user)
    return user_response(user)


@app.post("/api/admin/import-students")
async def import_students(
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> dict[str, int]:
    suffix = (file.filename or "").lower().rsplit(".", 1)[-1]
    if suffix not in {"csv", "xlsx"}:
        raise HTTPException(status_code=415, detail="Upload a CSV or XLSX file")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size must not exceed 10 MB")
    try:
        if suffix == "csv":
            records = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
        else:
            workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
            worksheet = workbook.active
            rows = worksheet.iter_rows(values_only=True)
            headers = [str(value or "").strip().lower() for value in next(rows, ())]
            records = [dict(zip(headers, row)) for row in rows]
            workbook.close()
    except (UnicodeDecodeError, csv.Error, OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Could not read the student data file") from exc
    required = {"name", "email", "password", "branch", "year", "section", "roll_number"}
    if not records or not required.issubset({str(key).strip().lower() for key in records[0]}):
        raise HTTPException(status_code=422, detail=f"Required columns: {', '.join(sorted(required))}")

    added = 0
    try:
        for index, record in enumerate(records, start=2):
            values = {str(key).strip().lower(): value for key, value in record.items()}
            name = str(values.get("name") or "").strip()
            email = str(values.get("email") or "").strip().lower()
            password = str(values.get("password") or "")
            branch = str(values.get("branch") or "").strip()
            section = str(values.get("section") or "").strip()
            roll_number = str(values.get("roll_number") or "").strip()
            if not all((name, email, password, branch, section, roll_number)):
                raise ValueError(f"Row {index} is missing a required value")
            if len(password) < 8:
                raise ValueError(f"Row {index} password must be at least 8 characters")
            if len(password) > 72:
                raise ValueError(f"Row {index} password must not exceed 72 characters")
            year = int(values["year"])
            if year not in range(1, 5):
                raise ValueError(f"Row {index} year must be from 1 to 4")
            if db.query(User).filter(User.email == email).first():
                raise ValueError(f"Row {index} email already exists: {email}")
            db.add(
                User(
                    name=name,
                    email=email,
                    password_hash=pwd_context.hash(password),
                    role=RoleEnum.STUDENT.value,
                    branch=branch,
                    year=year,
                    section=section,
                    roll_number=roll_number,
                )
            )
            added += 1
        write_audit(db, current_user, "import", "students", 0, f"Imported {added} student accounts")
        db.commit()
    except (KeyError, TypeError, ValueError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"imported": added}


@app.get("/api/admin/summary", response_model=CampusSummary)
def admin_summary(
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CampusSummary:
    return CampusSummary(
        total_rooms=db.query(Room).count(),
        available_rooms=db.query(Room).filter(Room.is_active.is_(True)).count(),
        active_exams=db.query(Exam).count(),
        announcements=db.query(Announcement).count(),
        pending_requests=db.query(FacultyRequest).filter(FacultyRequest.status == "pending").count(),
        students=db.query(User).filter(User.role == RoleEnum.STUDENT.value).count(),
        faculty=db.query(User).filter(User.role == RoleEnum.FACULTY.value).count(),
    )


@app.get("/api/admin/audit")
def list_audit_logs(
    current_user: Annotated[User, Depends(require_roles(RoleEnum.ADMIN.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    rows = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(200).all()
    return [
        {
            "id": row.id,
            "actor": row.actor.name,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "details": row.details,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@app.get("/", response_model=None)
def root() -> Response | dict[str, str]:
    frontend_index = Path(os.getenv("FRONTEND_DIST_DIR", "/app/frontend/dist")) / "index.html"
    if frontend_index.is_file():
        return FileResponse(frontend_index)
    return {"message": "Welcome to DDUGU Smart Campus API"}


frontend_dist = Path(os.getenv("FRONTEND_DIST_DIR", "/app/frontend/dist"))
if (frontend_dist / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="frontend-assets")


@app.get("/{full_path:path}", include_in_schema=False)
def frontend_route(full_path: str) -> Response:
    frontend_index = frontend_dist / "index.html"
    if frontend_index.is_file() and not full_path.startswith("api/"):
        return FileResponse(frontend_index)
    raise HTTPException(status_code=404, detail="Not found")
