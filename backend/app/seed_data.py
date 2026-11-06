from __future__ import annotations

from datetime import date, timedelta

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, create_tables
from app.models import Announcement, Building, ClassSchedule, Exam, ExamSeat, FacultyRequest, LibraryPass, Room, RoleEnum, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def seed_demo_data() -> None:
    create_tables()
    db: Session = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        admin = User(
            name="Admin User",
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role=RoleEnum.ADMIN.value,
            branch="CSE",
            year=4,
            section="A",
        )
        faculty = User(
            name="Dr. S. Mishra",
            email="faculty@ddugu.ac.in",
            password_hash=hash_password("faculty123"),
            role=RoleEnum.FACULTY.value,
            branch="CSE",
            year=3,
            section="A",
        )
        student = User(
            name="Riya Sharma",
            email="student@ddugu.ac.in",
            password_hash=hash_password("student123"),
            role=RoleEnum.STUDENT.value,
            branch="CSE",
            year=2,
            section="A",
            roll_number="CSE-22-102",
        )

        db.add_all([admin, faculty, student])
        db.flush()

        iet = Building(
            name="Institute of Engineering & Technology",
            code="IET",
            location="Main campus",
            description="DEMO/TEST campus record. Room locations and capacities require university verification.",
        )
        deeksha = Building(
            name="Deeksha Bhawan",
            code="DB",
            location="Academic Block",
            description="DEMO/TEST campus record. Room locations and capacities require university verification.",
        )
        db.add_all([iet, deeksha])
        db.flush()

        rooms = [
            Room(building_id=iet.id, code="IET17", room_type="classroom", floor="1", capacity=75, facilities="Projector,Whiteboard", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="IET18", room_type="classroom", floor="1", capacity=75, facilities="Projector,Whiteboard", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="IET19", room_type="classroom", floor="1", capacity=75, facilities="Projector,Whiteboard", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="IET20", room_type="classroom", floor="1", capacity=75, facilities="Projector,Whiteboard", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="IET32", room_type="seminar", floor="2", capacity=200, facilities="Projector,AV", usage_permission="all", examination_suitable=True),
            Room(building_id=deeksha.id, code="LH01", room_type="lecture_hall", floor="Ground", capacity=80, facilities="Projector,Board", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="IET24", room_type="classroom", floor="2", capacity=60, facilities="Projector", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="IET25", room_type="classroom", floor="2", capacity=60, facilities="Projector", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="IET29", room_type="classroom", floor="2", capacity=60, facilities="Projector", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="IET30", room_type="classroom", floor="2", capacity=60, facilities="Projector", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="IET28", room_type="classroom", floor="2", capacity=60, facilities="Projector", usage_permission="all", examination_suitable=True),
            Room(building_id=iet.id, code="CSE-LAB", room_type="laboratory", floor="1", capacity=30, facilities="Computers,Projector", usage_permission="all"),
            Room(building_id=iet.id, code="ME-LAB", room_type="laboratory", floor="1", capacity=30, facilities="Workshop equipment", usage_permission="all"),
            Room(building_id=iet.id, code="ECE-LAB", room_type="laboratory", floor="1", capacity=30, facilities="Electronics benches", usage_permission="all"),
            Room(building_id=iet.id, code="IT-LAB", room_type="laboratory", floor="1", capacity=30, facilities="Computers", usage_permission="all"),
            Room(building_id=iet.id, code="LIBRARY", room_type="library", floor="Ground", capacity=165, facilities="Reading area", usage_permission="library_and_exam", examination_suitable=True),
            Room(building_id=iet.id, code="FACULTY-CABINS", room_type="office", floor="Ground", capacity=1, facilities=""),
            Room(building_id=iet.id, code="DIRECTOR-OFFICE", room_type="office", floor="Ground", capacity=1, facilities=""),
            Room(building_id=iet.id, code="ADMIN-OFFICE", room_type="office", floor="Ground", capacity=1, facilities=""),
            Room(building_id=iet.id, code="PLACEMENT-CELL", room_type="office", floor="Ground", capacity=1, facilities=""),
            Room(building_id=deeksha.id, code="LH05", room_type="lecture_hall", floor="Ground", capacity=60, facilities="Projector,Board", usage_permission="all", examination_suitable=True),
            Room(building_id=deeksha.id, code="LH09", room_type="lecture_hall", floor="1", capacity=60, facilities="Projector,Board", usage_permission="all", examination_suitable=True),
            *[
                Room(
                    building_id=deeksha.id,
                    code=f"LH{number:02d}",
                    room_type="lecture_hall",
                    floor="Ground" if number <= 4 else "1",
                    capacity=60,
                    facilities="Projector,Board",
                    usage_permission="all",
                    examination_suitable=True,
                )
                for number in (2, 3, 4, 6, 7, 8, 10, 11, 12)
            ],
        ]
        db.add_all(rooms)
        db.flush()

        classes = [
            ClassSchedule(title="Operating Systems", subject="CSE-204", day="Monday", start_time="09:00", end_time="10:30", room_id=rooms[0].id, instructor_id=faculty.id, branch="CSE", year=2, section="A", batch="A1"),
            ClassSchedule(title="Data Structures", subject="CSE-203", day="Tuesday", start_time="11:00", end_time="12:30", room_id=rooms[3].id, instructor_id=faculty.id, branch="CSE", year=2, section="A", batch="A1"),
            ClassSchedule(title="Database Lab", subject="CSE-310", day="Wednesday", start_time="14:00", end_time="16:00", room_id=rooms[1].id, instructor_id=faculty.id, branch="CSE", year=3, section="A", batch="A2"),
        ]
        db.add_all(classes)

        exam = Exam(
            title="Mid Semester Exam",
            subject="Operating Systems",
            exam_date=date.today() + timedelta(days=2),
            start_time="10:00",
            end_time="11:30",
            building_id=deeksha.id,
            room_id=rooms[5].id,
            published=True,
            branch="CSE",
            year=2,
            section="A",
        )
        db.add(exam)
        db.flush()

        seat = ExamSeat(exam_id=exam.id, student_id=student.id, room_id=rooms[5].id, seat_number="A-12")
        db.add(seat)

        request = FacultyRequest(
            faculty_id=faculty.id,
            room_id=rooms[2].id,
            requested_date=date.today() + timedelta(days=1),
            start_time="15:00",
            end_time="16:00",
            subject="CSE Practical",
            purpose="Extra practical session",
            branch="CSE",
            year=2,
            section="A",
            batch="A1",
            expected_attendance=30,
            required_facilities="Projector",
            notes="Need room for a guest workshop.",
            status="pending",
        )
        db.add(request)

        announcements = [
            Announcement(title="Exam hall allotment notice", message="Students are advised to verify their room and seat details 1 hour before the exam", audience="all"),
            Announcement(title="Lab maintenance", message="CSE Lab will be unavailable on Friday for maintenance.", audience="CSE"),
        ]
        db.add_all(announcements)

        db.add(LibraryPass(student_id=student.id, pass_code="LIB-2026-001", expiry_date=date.today() + timedelta(days=90), status="active"))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
