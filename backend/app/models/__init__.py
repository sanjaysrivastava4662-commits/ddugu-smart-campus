
from __future__ import annotations

from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from app.database import Base


class RoleEnum(str, PyEnum):
    ADMIN = "admin"
    FACULTY = "faculty"
    STUDENT = "student"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String(120), nullable=False)
    email: Mapped[str] = Column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = Column(String(255), nullable=False)
    role: Mapped[str] = Column(String(20), nullable=False, default=RoleEnum.STUDENT.value)
    branch: Mapped[Optional[str]] = Column(String(60), nullable=True)
    year: Mapped[Optional[int]] = Column(Integer, nullable=True)
    section: Mapped[Optional[str]] = Column(String(10), nullable=True)
    roll_number: Mapped[Optional[str]] = Column(String(30), nullable=True)
    phone: Mapped[Optional[str]] = Column(String(30), nullable=True)
    is_active: Mapped[bool] = Column(Boolean, default=True)

    schedule_classes: Mapped[list["ClassSchedule"]] = relationship(back_populates="instructor")
    requests: Mapped[list["FacultyRequest"]] = relationship(back_populates="faculty")
    exam_seats: Mapped[list["ExamSeat"]] = relationship(back_populates="student")
    library_passes: Mapped[list["LibraryPass"]] = relationship(back_populates="student")


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String(120), nullable=False)
    code: Mapped[str] = Column(String(30), nullable=False, unique=True)
    location: Mapped[str] = Column(String(120), default="Campus")
    description: Mapped[Optional[str]] = Column(Text, nullable=True)

    rooms: Mapped[list["Room"]] = relationship(back_populates="building")
    exams: Mapped[list["Exam"]] = relationship(back_populates="building")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    building_id: Mapped[int] = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    code: Mapped[str] = Column(String(30), nullable=False)
    room_type: Mapped[str] = Column(String(40), nullable=False, default="classroom")
    floor: Mapped[str] = Column(String(20), nullable=False, default="Ground")
    capacity: Mapped[int] = Column(Integer, nullable=False, default=60)
    facilities: Mapped[str] = Column(String(255), default="Projector")
    usage_permission: Mapped[str] = Column(String(40), default="all")
    examination_suitable: Mapped[bool] = Column(Boolean, default=False)
    is_active: Mapped[bool] = Column(Boolean, default=True)

    building: Mapped[Building] = relationship(back_populates="rooms")
    classes: Mapped[list["ClassSchedule"]] = relationship(back_populates="room")
    requests: Mapped[list["FacultyRequest"]] = relationship(back_populates="room")
    exams: Mapped[list["Exam"]] = relationship(back_populates="room")


class ClassSchedule(Base):
    __tablename__ = "class_schedules"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    title: Mapped[str] = Column(String(120), nullable=False)
    subject: Mapped[str] = Column(String(120), nullable=False)
    day: Mapped[str] = Column(String(20), nullable=False)
    start_time: Mapped[str] = Column(String(20), nullable=False)
    end_time: Mapped[str] = Column(String(20), nullable=False)
    room_id: Mapped[int] = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    instructor_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False)
    branch: Mapped[str] = Column(String(60), nullable=False)
    year: Mapped[int] = Column(Integer, nullable=False)
    section: Mapped[str] = Column(String(20), nullable=False)
    batch: Mapped[Optional[str]] = Column(String(20), nullable=True)

    room: Mapped[Room] = relationship(back_populates="classes")
    instructor: Mapped[User] = relationship(back_populates="schedule_classes")


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    title: Mapped[str] = Column(String(150), nullable=False)
    subject: Mapped[str] = Column(String(120), nullable=False)
    exam_date: Mapped[date] = Column(Date, nullable=False)
    start_time: Mapped[str] = Column(String(20), nullable=False)
    end_time: Mapped[str] = Column(String(20), nullable=False)
    building_id: Mapped[int] = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    room_id: Mapped[Optional[int]] = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    published: Mapped[bool] = Column(Boolean, default=False)
    reporting_time: Mapped[Optional[str]] = Column(String(20), nullable=True)
    branch: Mapped[Optional[str]] = Column(String(60), nullable=True)
    year: Mapped[Optional[int]] = Column(Integer, nullable=True)
    section: Mapped[Optional[str]] = Column(String(20), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    building: Mapped[Building] = relationship(back_populates="exams")
    room: Mapped[Optional[Room]] = relationship(back_populates="exams")
    seats: Mapped[list["ExamSeat"]] = relationship(back_populates="exam")
    room_allocations: Mapped[list["ExamRoomAllocation"]] = relationship(back_populates="exam")


class ExamRoomAllocation(Base):
    __tablename__ = "exam_room_allocations"
    __table_args__ = (UniqueConstraint("exam_id", "room_id", name="uq_exam_room_allocation"),)

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    exam_id: Mapped[int] = Column(Integer, ForeignKey("exams.id"), nullable=False)
    room_id: Mapped[int] = Column(Integer, ForeignKey("rooms.id"), nullable=False)

    exam: Mapped[Exam] = relationship(back_populates="room_allocations")
    room: Mapped[Room] = relationship()


class ExamSeat(Base):
    __tablename__ = "exam_seats"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_exam_student_seat"),)

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    exam_id: Mapped[int] = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id: Mapped[int] = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    seat_number: Mapped[str] = Column(String(20), nullable=False)
    seat_row: Mapped[Optional[str]] = Column(String(20), nullable=True)

    exam: Mapped[Exam] = relationship(back_populates="seats")
    student: Mapped[User] = relationship(back_populates="exam_seats")
    room: Mapped[Room] = relationship()


class FacultyRequest(Base):
    __tablename__ = "faculty_requests"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    faculty_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id: Mapped[int] = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    requested_date: Mapped[date] = Column(Date, nullable=False)
    start_time: Mapped[str] = Column(String(20), nullable=False)
    end_time: Mapped[str] = Column(String(20), nullable=False)
    subject: Mapped[Optional[str]] = Column(String(120), nullable=True)
    purpose: Mapped[str] = Column(String(200), nullable=False)
    branch: Mapped[Optional[str]] = Column(String(60), nullable=True)
    year: Mapped[Optional[int]] = Column(Integer, nullable=True)
    section: Mapped[Optional[str]] = Column(String(20), nullable=True)
    batch: Mapped[Optional[str]] = Column(String(20), nullable=True)
    expected_attendance: Mapped[Optional[int]] = Column(Integer, nullable=True)
    required_facilities: Mapped[Optional[str]] = Column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = Column(Text, nullable=True)
    status: Mapped[str] = Column(String(20), default="pending")
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    faculty: Mapped[User] = relationship(back_populates="requests")
    room: Mapped[Room] = relationship(back_populates="requests")


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    title: Mapped[str] = Column(String(150), nullable=False)
    message: Mapped[str] = Column(Text, nullable=False)
    audience: Mapped[str] = Column(String(50), default="all")
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)


class LibraryPass(Base):
    __tablename__ = "library_passes"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False)
    pass_code: Mapped[str] = Column(String(40), nullable=False, unique=True)
    issue_date: Mapped[date] = Column(Date, default=date.today)
    expiry_date: Mapped[date] = Column(Date, nullable=False)
    status: Mapped[str] = Column(String(20), default="active")

    student: Mapped[User] = relationship(back_populates="library_passes")


class IssueReport(Base):
    __tablename__ = "issue_reports"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = Column(String(40), nullable=False)
    details: Mapped[str] = Column(Text, nullable=False)
    status: Mapped[str] = Column(String(20), default="open")
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)

    student: Mapped[User] = relationship()


class BlueprintAsset(Base):
    __tablename__ = "blueprint_assets"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    building_id: Mapped[int] = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    filename: Mapped[str] = Column(String(255), nullable=False)
    media_type: Mapped[str] = Column(String(80), nullable=False)
    content: Mapped[bytes] = Column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    building: Mapped[Building] = relationship()


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    actor_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = Column(String(60), nullable=False)
    entity_type: Mapped[str] = Column(String(60), nullable=False)
    entity_id: Mapped[int] = Column(Integer, nullable=False)
    details: Mapped[Optional[str]] = Column(Text, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, index=True)

    actor: Mapped[User] = relationship()
