# 🎓 DDUGU Smart Campus

## Intelligent Classroom, Academic Scheduling and Examination Management System

**Deen Dayal Upadhyaya Gorakhpur University (DDUGU) – Institute of Engineering & Technology**

> [!NOTE]
> This is a prototype/demo application. All student, faculty and room data is clearly labelled as DEMO/TEST data and does not represent verified university records.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  React Frontend                  │
│        (TypeScript + Tailwind CSS + Vite)        │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Student  │  │ Faculty  │  │    Admin     │   │
│  │Dashboard │  │Dashboard │  │  Dashboard   │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
└──────────────────────┬──────────────────────────┘
                       │ REST API (JWT Auth)
┌──────────────────────┴──────────────────────────┐
│              Python FastAPI Backend               │
│                                                   │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │ Scheduling │ │   Exam     │ │    Room      │  │
│  │  Engine    │ │  Service   │ │  Assistant   │  │
│  └────────────┘ └────────────┘ └──────────────┘  │
└──────────────────────┬───────────────────────────┘
                       │ SQLAlchemy ORM
┌──────────────────────┴───────────────────────────┐
│                  SQLite database                   │
└───────────────────────────────────────────────────┘
```

## ✨ Features

### Three Role-Based Dashboards

| Feature | Student | Faculty | Admin |
|---------|---------|---------|-------|
| View Timetable | ✅ | ✅ | ✅ |
| Search Vacant Rooms | ❌ | ✅ | ✅ |
| Request Classroom | ❌ | ✅ | ❌ |
| Approve Requests | ❌ | ❌ | ✅ |
| Manage Timetable | ❌ | ❌ | ✅ |
| View Exam Details | ✅ | 🔒 | ✅ |
| Create Exams | ❌ | ❌ | ✅ |
| Allocate Seats | ❌ | ❌ | ✅ |
| View Library Pass | ✅ | ❌ | ✅ |
| Issue Library Pass | ❌ | ❌ | ✅ |
| Publish Announcements | ❌ | ❌ | ✅ |
| Report Issues | ✅ | ❌ | ✅ (resolve) |
| Campus Explorer | ✅ | ✅ | ✅ |
| Room Assistant | ❌ | ✅ | ✅ |

### Key Modules

- **🏫 Classroom Management** – Two buildings (IET & Deeksha Bhawan), 30+ rooms
- **📅 Timetable System** – Daily & weekly view, conflict prevention
- **📝 Faculty Request Workflow** – Request → Review → Approve/Reject
- **🎯 Conflict Prevention Engine** – Room, faculty, and section overlap detection
- **📋 Examination Centre** – Create exams, auto-allocate seats, 1-hour release
- **🔍 Exam Details** – Authenticated students see only their own assigned exams
- **📚 Library Pass** – QR-code based pass management
- **📢 Announcements** – Targeted notifications by branch/year/section
- **🔎 Room Assistant** – Deterministic natural-language room finder
- **🗺️ Campus Explorer** – Building and room directory with private blueprint uploads

## 🏢 Campus Coverage

### IET (Institute of Engineering and Technology)
- **Ground Floor**: Library (150-180 capacity), Faculty Cabins, Offices
- **First Floor**: CSE/ME/ECE/IT Labs, Classrooms IET17-20 (75 cap each)
- **Second Floor**: IET32 Seminar Hall (200 cap), IET24/25/28/29/30

### Deeksha Bhawan
- Lecture Halls LH01 through LH12

### Branches
- CSE (150 students, Sections A & B)
- AI-ML (150 students, Sections A & B)
- AI-DS (75 students)
- ECE (75 students)
- ME (75 students)
- IT (75 students)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or pnpm

### Option 1: Docker (Recommended)

```bash
docker-compose up --build
```

Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Public demo deployment (Render)

This repository includes a Render Blueprint. After pushing it to GitHub, sign in to Render, choose **New → Blueprint**, select the public `ddugu-smart-campus` repository, and apply the Blueprint. Render builds a single container that serves both the web UI and API. The public demo starts with the demo accounts listed below.

> [!WARNING]
> The free demo uses temporary SQLite storage. Data created through the app can be lost when the service restarts or redeploys. Use verified university data or this demo for real operations only after configuring persistent production storage, rotating the demo administrator password, and reviewing access controls.

Once deployed, share the URL Render assigns to the service (for example, `https://ddugu-smart-campus.onrender.com`).

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Initialize database and seed demo data
python -m app.seed_data

# Start server
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install

# Start dev server
npm run dev
```

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@ddugu.ac.in | admin123 |
| Faculty | faculty@ddugu.ac.in | faculty123 |
| Student | student@ddugu.ac.in | student123 |

> [!CAUTION]
> These are demo credentials. Change all passwords before any production deployment.

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Lint, Build, and Type Check
```bash
cd frontend
npm run lint
npm run build
```

---

## 📁 Project Structure

```
ddugu-smart-campus/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application and API routes
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── seed_data.py     # Demo data seeder
│   ├── tests/               # Automated tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Role-based dashboard and workflows
│   │   └── main.tsx         # Entry point
│   ├── package.json
│   ├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔒 Security

- JWT-based authentication with role-based access control
- bcrypt password hashing
- Server-side permission checks on all endpoints
- Input validation (Pydantic + frontend)
- Audit logging for admin actions
- Student data privacy protection
- Environment-based secrets

---

## 📊 Examination System

The examination module implements a secure, time-controlled information release:

1. **Create Exam** – Admin defines subject, date, time, eligible students
2. **Allocate Rooms** – Admin selects exam-suitable rooms from both buildings
3. **Auto-Allocate Seats** – System distributes students, preventing overcapacity
4. **Publish** – Admin publishes the exam
5. **Student Access** – Authenticated students see only exams for which they have a seat allocation
6. **1-Hour Release** – Building, room, floor, and seat details appear one hour before the exam

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS v4, Vite |
| UI Components | Lucide React Icons, Recharts |
| Backend | Python 3.10+, FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Validation | Pydantic v2 |
| QR Codes | qrcode (backend), qrcode.react (frontend) |
| DevOps | Docker, Docker Compose, Render Blueprint |

---

## 📄 License

This project was developed for the DDUGU Smart Campus Hackathon. All rights reserved.

---

> [!IMPORTANT]
> This prototype uses DEMO/TEST data throughout. Real deployment requires importing verified student records, faculty records, official timetables, and building blueprints from university administration. Change the demo credentials and secret key before deployment.
