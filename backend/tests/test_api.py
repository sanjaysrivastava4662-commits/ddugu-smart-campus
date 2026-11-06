from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_demo_login_and_role_protection(client: TestClient):
    admin_headers = login(client, "admin@ddugu.ac.in", "admin123")
    student_headers = login(client, "student@ddugu.ac.in", "student123")

    assert client.get("/api/admin/summary", headers=admin_headers).status_code == 200
    assert client.get("/api/admin/summary", headers=student_headers).status_code == 403
    assert client.get("/api/health").json()["status"] == "ok"


def test_exam_venue_and_seat_are_hidden_until_release(client: TestClient):
    student_headers = login(client, "student@ddugu.ac.in", "student123")
    response = client.get("/api/exams", headers=student_headers)

    assert response.status_code == 200
    exam = response.json()[0]
    assert exam["venue_released"] is False
    assert exam["room_code"] is None
    assert exam["seat_number"] is None


def test_room_request_rejects_timetable_conflict(client: TestClient):
    faculty_headers = login(client, "faculty@ddugu.ac.in", "faculty123")
    rooms = client.get("/api/rooms", headers=faculty_headers).json()
    room_id = next(room["id"] for room in rooms if room["code"] == "IET17")
    next_monday = date.today() + timedelta(days=(7 - date.today().weekday()) % 7 or 7)

    response = client.post(
        "/api/faculty-requests",
        headers=faculty_headers,
        json={
            "room_id": room_id,
            "requested_date": next_monday.isoformat(),
            "start_time": "09:30",
            "end_time": "10:00",
            "subject": "CSE Test",
            "purpose": "Conflict test request",
            "branch": "CSE",
            "year": 2,
            "section": "A",
            "expected_attendance": 20,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Room conflicts with a scheduled class"


def test_invalid_room_request_time_is_rejected(client: TestClient):
    faculty_headers = login(client, "faculty@ddugu.ac.in", "faculty123")
    rooms = client.get("/api/rooms", headers=faculty_headers).json()
    response = client.post(
        "/api/faculty-requests",
        headers=faculty_headers,
        json={
            "room_id": rooms[0]["id"],
            "requested_date": date.today().isoformat(),
            "start_time": "16:00",
            "end_time": "15:00",
            "subject": "CSE Test",
            "purpose": "Invalid time request",
            "branch": "CSE",
            "year": 2,
            "section": "A",
            "expected_attendance": 20,
        },
    )

    assert response.status_code == 422


def test_approving_request_publishes_official_student_class(client: TestClient):
    admin_headers = login(client, "admin@ddugu.ac.in", "admin123")
    student_headers = login(client, "student@ddugu.ac.in", "student123")
    request = client.get("/api/faculty-requests", headers=admin_headers).json()[0]

    approval = client.post(
        f"/api/faculty-requests/{request['id']}/decision?decision=approved",
        headers=admin_headers,
    )
    assert approval.status_code == 200
    classes = client.get("/api/timetable", headers=student_headers).json()
    assert any(item["title"] == "CSE Practical" for item in classes)


def test_room_assistant_applies_capacity_and_availability_constraints(client: TestClient):
    faculty_headers = login(client, "faculty@ddugu.ac.in", "faculty123")
    response = client.post(
        "/api/assistant/rooms",
        headers=faculty_headers,
        json={"query": "Find a room for 70 CSE second-year students tomorrow between 11 AM and 1 PM with projector"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["parsed"]["minimum_capacity"] == 70
    assert data["parsed"]["year"] == 2
    assert data["recommendations"]
    assert all(item["capacity"] >= 70 for item in data["recommendations"])


def test_exam_seats_are_allocated_across_selected_rooms(client: TestClient):
    admin_headers = login(client, "admin@ddugu.ac.in", "admin123")
    rooms = client.get("/api/rooms", headers=admin_headers).json()
    room_ids = [next(room["id"] for room in rooms if room["code"] == code) for code in ("LH01", "LH05")]
    exam_date = date.today() + timedelta(days=3)

    created = client.post(
        "/api/admin/exams",
        headers=admin_headers,
        json={
            "title": "Multi-room allocation test",
            "subject": "CSE-TEST",
            "exam_date": exam_date.isoformat(),
            "start_time": "11:00",
            "end_time": "12:00",
            "room_ids": room_ids,
            "branch": "CSE",
            "year": 2,
            "section": "A",
            "publish": True,
        },
    )
    assert created.status_code == 201

    allocation = client.get(f"/api/admin/exams/{created.json()['id']}/allocations", headers=admin_headers)
    assert allocation.status_code == 200
    assert allocation.json()["allocated"] == 1
    assert len(allocation.json()["rooms"]) == 2
    assert sum(room["assigned"] for room in allocation.json()["rooms"]) == 1


def test_library_pass_is_validated_server_side(client: TestClient):
    admin_headers = login(client, "admin@ddugu.ac.in", "admin123")
    passes = client.get("/api/library-passes", headers=admin_headers).json()
    code = passes[0]["pass_code"]

    verified = client.post("/api/library-passes/verify", headers=admin_headers, json={"pass_code": code})
    assert verified.status_code == 200
    assert verified.json()["valid"] is True

    student_headers = login(client, "student@ddugu.ac.in", "student123")
    rejected = client.post("/api/library-passes/verify", headers=student_headers, json={"pass_code": code})
    assert rejected.status_code == 403


def test_admin_can_upload_and_retrieve_pdf_blueprint(client: TestClient):
    admin_headers = login(client, "admin@ddugu.ac.in", "admin123")
    buildings = client.get("/api/buildings", headers=admin_headers).json()
    building_id = buildings[0]["id"]

    uploaded = client.post(
        f"/api/admin/buildings/{building_id}/blueprints",
        headers=admin_headers,
        files={"file": ("demo.pdf", b"%PDF-1.4\nDemo blueprint", "application/pdf")},
    )
    assert uploaded.status_code == 201
    asset_id = uploaded.json()["id"]
    retrieved = client.get(f"/api/buildings/{building_id}/blueprints/{asset_id}", headers=admin_headers)
    assert retrieved.status_code == 200
    assert retrieved.content.startswith(b"%PDF-")
