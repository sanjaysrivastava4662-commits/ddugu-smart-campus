from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


def validate_time(value: str) -> str:
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueError("Time must use HH:MM format") from exc
    return value


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=4, max_length=128)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    branch: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    roll_number: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=8, max_length=72)
    role: Literal["faculty", "student"]
    branch: Optional[str] = Field(default=None, max_length=60)
    year: Optional[int] = Field(default=None, ge=1, le=4)
    section: Optional[str] = Field(default=None, max_length=20)
    roll_number: Optional[str] = Field(default=None, max_length=30)
    phone: Optional[str] = Field(default=None, max_length=30)


class RoomCreate(BaseModel):
    building_id: int
    code: str = Field(..., min_length=2, max_length=30)
    room_type: str = Field(default="classroom", max_length=40)
    floor: str = Field(..., max_length=20)
    capacity: int = Field(..., ge=1, le=1000)
    facilities: str = Field(default="", max_length=255)
    usage_permission: str = Field(default="all", max_length=40)
    examination_suitable: bool = False


class RoomResponse(BaseModel):
    id: int
    code: str
    room_type: str
    floor: str
    capacity: int
    facilities: str
    usage_permission: str
    examination_suitable: bool
    building_name: str


class RoomAssistantRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=500)


class ClassScheduleCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    subject: str = Field(..., min_length=2, max_length=120)
    day: str
    start_time: str
    end_time: str
    room_id: int
    instructor_id: int
    branch: str = Field(..., max_length=60)
    year: int = Field(..., ge=1, le=4)
    section: str = Field(..., max_length=20)
    batch: Optional[str] = Field(default=None, max_length=20)

    @field_validator("start_time", "end_time")
    @classmethod
    def valid_time(cls, value: str) -> str:
        return validate_time(value)

    @field_validator("day")
    @classmethod
    def valid_day(cls, value: str) -> str:
        if value.title() not in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}:
            raise ValueError("Invalid day of week")
        return value.title()


class ClassScheduleResponse(BaseModel):
    id: int
    title: str
    subject: str
    day: str
    start_time: str
    end_time: str
    room_code: str
    room_name: str
    instructor: str
    branch: str
    year: int
    section: str


class ExamCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    subject: str = Field(..., min_length=2, max_length=120)
    exam_date: date
    start_time: str
    end_time: str
    reporting_time: Optional[str] = None
    room_ids: list[int] = Field(..., min_length=1)
    branch: str = Field(..., max_length=60)
    year: int = Field(..., ge=1, le=4)
    section: str = Field(..., max_length=20)
    publish: bool = False

    @field_validator("start_time", "end_time")
    @classmethod
    def valid_time(cls, value: str) -> str:
        return validate_time(value)


class ExamResponse(BaseModel):
    id: int
    title: str
    subject: str
    exam_date: date
    start_time: str
    end_time: str
    building_name: str
    room_code: Optional[str] = None
    room_floor: Optional[str] = None
    published: bool
    venue_released: Optional[bool] = None
    seat_number: Optional[str] = None
    reporting_time: Optional[str] = None
    release_at: Optional[datetime] = None
    server_time: Optional[datetime] = None
    seconds_until_release: Optional[int] = None


class ExamSeatUpdate(BaseModel):
    room_id: int
    seat_number: str = Field(..., min_length=1, max_length=20)


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    message: str = Field(..., min_length=2, max_length=4000)
    audience: str = Field(default="all", max_length=60)


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    message: str
    audience: str
    created_at: datetime


class FacultyRequestCreate(BaseModel):
    room_id: int
    requested_date: date
    start_time: str
    end_time: str
    subject: str = Field(..., min_length=2, max_length=120)
    purpose: str = Field(..., min_length=3, max_length=200)
    branch: str = Field(..., max_length=60)
    year: int = Field(..., ge=1, le=4)
    section: str = Field(..., max_length=20)
    batch: Optional[str] = Field(default=None, max_length=20)
    expected_attendance: int = Field(..., ge=1, le=1000)
    required_facilities: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("start_time", "end_time")
    @classmethod
    def valid_time(cls, value: str) -> str:
        return validate_time(value)


class FacultyRequestResponse(BaseModel):
    id: int
    faculty_name: str
    room_code: str
    requested_date: date
    start_time: str
    end_time: str
    subject: Optional[str] = None
    purpose: str
    branch: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    batch: Optional[str] = None
    expected_attendance: Optional[int] = None
    notes: Optional[str]
    status: str
    created_at: datetime


class LibraryPassCreate(BaseModel):
    student_id: int
    expiry_date: date


class LibraryPassVerify(BaseModel):
    pass_code: str = Field(..., min_length=8, max_length=40)


class IssueReportCreate(BaseModel):
    category: str = Field(..., min_length=2, max_length=40)
    details: str = Field(..., min_length=5, max_length=2000)


class CampusSummary(BaseModel):
    total_rooms: int
    available_rooms: int
    active_exams: int
    announcements: int
    pending_requests: int
    students: int
    faculty: int
