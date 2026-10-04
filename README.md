# IIPS Smart Classroom Attendance Management System

An automated, secure, and real-time attendance management platform built with **FastAPI**, **React (Vite)**, **SQLAlchemy**, and **Time-Limited JWT Dynamic QR Codes**.

---

## 📌 Project Overview & Problem Statement

### 🎯 Objective
Traditional classroom attendance methods (calling roll calls manually or passing around paper sign-in sheets) suffer from:
- **High time consumption**: Wastes 10–15 minutes per lecture.
- **Proxy attendance**: Students sign for absent peers.
- **Data loss & transcription errors**: Manual data entry into spreadsheets is prone to mistakes.

**The Solution:**
A **smart QR attendance system** where:
1. Teachers launch a time-limited dynamic session that generates an encrypted QR code.
2. Students scan the QR code with their mobile device or laptop camera to mark attendance instantly.
3. The system automatically enforces roster snapshots, detects duplicate check-ins, closes sessions upon timer expiry, marks absentees automatically, and generates one-click CSV reports.

---

## ✨ Key Features

- **🔐 Single-Tenant Teacher Authentication**: Secure PBKDF2/Bcrypt hashed credentials with JWT Bearer Token authorization. First-time setup lock prevents unauthorized administrative registration.
- **👨‍🎓 Student Management (CRUD)**: Register students with Student ID, Name, Email, Program, and Academic Year. Includes instant live search and active/inactive toggles.
- **🏫 Classroom & Enrollment Management**: Create courses/sections and enroll students. Roster snapshots are frozen when an attendance session starts to ensure integrity.
- **⚡ Dynamic QR Attendance**:
  - Encrypted, time-limited JWT tokens embedded in dynamic QR codes.
  - Expiry timer automatically disables QR check-in when session duration ends.
  - Prevents repeat check-in and rejects unenrolled students.
  - Live attendance counter updates on the teacher dashboard in real-time.
- **📊 Automated Absence Marking**: When the teacher closes the session (or when time expires), any enrolled student who did not check in is automatically recorded as `ABSENT`.
- **📑 Reports & Analytics**: Filter records by classroom and date range; export reports to CSV with UTF-8 BOM encoding for Excel/Google Sheets compatibility.
- **📱 Phone-Optimized Quick Check-In**: Students save their Student ID once in their phone browser; scanning a class QR automatically records attendance in a single tap.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite | High-performance SPA with instant HMR and responsive UI |
| **Styling** | Modern Vanilla CSS | Glassmorphism, tailored tokens, responsive layout |
| **Backend API** | FastAPI (Python 3.11+) | Asynchronous high-speed RESTful API with automatic OpenAPI documentation |
| **Database ORM** | SQLAlchemy 2.0 | Type-safe ORM supporting SQLite & MySQL/PostgreSQL |
| **Validation** | Pydantic v2 | Robust schema validation and strict request typing |
| **Authentication** | Python-Jose & Passlib (Bcrypt) | Time-limited JWT authentication & password hashing |
| **QR Code Engine** | Python `qrcode` & Pillow | Dynamic generation of base64 PNG QR images |

---

## 📐 System Architecture & Workflow

```
[ Teacher Dashboard ]
       │
       ├─► Creates Classroom (e.g., CS-501) & Enrolls Students
       │
       ├─► Starts Attendance Session (Duration: 60 mins)
       │         │
       │         └─► Generates Time-Limited JWT Token embedded in QR Code
       │
[ Student Phone / Browser ]
       │
       ├─► Scans Class QR Code (Google Lens / Camera)
       │
       ├─► Submits { student_id, session_token }
       │
[ FastAPI Backend ]
       │
       ├─► 1. Verifies JWT signature & expiration
       ├─► 2. Validates session status (Active vs Closed)
       ├─► 3. Verifies student is in Session Roster Snapshot
       ├─► 4. Checks for duplicate attendance
       └─► 5. Saves AttendanceRecord(status='present', checked_in_at=NOW)
                 │
                 ▼
[ Live Teacher Screen ] ◄── Real-time attendee counter & roster updates
```

---

## 🗄️ Database Schema

- **`users`**: Teacher accounts (`id`, `full_name`, `email`, `password_hash`, `role`, `is_active`, `timestamps`).
- **`students`**: Student directory (`id`, `student_id`, `full_name`, `email`, `program`, `year`, `is_active`, `timestamps`).
- **`classrooms`**: Classrooms/courses (`id`, `course_code`, `course_name`, `section`, `teacher_id`, `timestamps`).
- **`classroom_enrollments`**: Student-Classroom mappings (`id`, `classroom_id`, `student_id`, `is_active`, `enrolled_at`).
- **`attendance_sessions`**: Session instances (`id`, `classroom_id`, `title`, `session_date`, `start_time`, `end_time`, `status`, `qr_code`, `created_by`).
- **`attendance_session_roster`**: Frozen snapshot of enrolled students when the session begins.
- **`attendance_records`**: Check-in records (`id`, `session_id`, `student_id`, `status`, `checked_in_at`, `check_method`).

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- **Node.js** (v18 or higher)
- **Python** (v3.11 or higher)
- **Git**

### 2. Backend Setup
```powershell
# Navigate to backend
cd backend

# Create & activate virtual environment (Windows)
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Interactive Swagger API Docs will be available at [http://localhost:8000/docs](http://localhost:8000/docs)*

### 3. Frontend Setup
```powershell
# Open a second terminal and navigate to frontend
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
*Frontend Web App will run at [http://localhost:5173](http://localhost:5173)*

### 4. Running with Demo Data
To quickly populate the database with sample students and a demo classroom:
```powershell
cd backend
.\.venv\Scripts\python.exe .\seed_demo_data.py
```

### 5. Running Automated Tests
```powershell
cd backend
.\.venv\Scripts\python.exe .\test_suite.py
```

---

## 📱 Testing on Mobile (Local Wi-Fi Network)

1. Find your computer's IPv4 address:
   ```powershell
   ipconfig
   ```
   *(e.g., `192.168.1.5`)*
2. In `backend/.env`, set:
   ```env
   FRONTEND_URL=http://192.168.1.5:5173
   ```
3. Restart the backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
4. On your mobile phone connected to the **same Wi-Fi**, open `http://192.168.1.5:5173`.
5. Display the session QR code on your PC screen and scan it using your phone!

---

## 📦 Pushing the Project to GitHub

```powershell
# Initialize git repository (from project root)
git init

# Stage all files (.env and virtual environments are ignored automatically)
git add .

# Create initial commit
git commit -m "feat: initial release of IIPS Smart Classroom Attendance System"

# Add remote and push to your GitHub repo
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY_NAME>.git
git push -u origin main
```

---

## 🌐 Deployment Guide

### Backend Deployment (Render / Railway)
1. Push your repository to GitHub.
2. In **Render** or **Railway**, create a new **Web Service** connected to your repo.
3. Set root directory to `backend`.
4. Set Build Command: `pip install -r requirements.txt`
5. Set Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Set Environment Variables:
   - `APP_ENV=production`
   - `SECRET_KEY=<generate-a-strong-random-32-char-key>`
   - `FRONTEND_URL=https://your-frontend-domain.vercel.app`
   - `DATABASE_URL=<your-hosted-database-url-or-sqlite>`

### Frontend Deployment (Vercel / Netlify)
1. In **Vercel** or **Netlify**, import your GitHub repository.
2. Set Root Directory to `frontend`.
3. Set Build Command: `npm run build`
4. Set Output Directory: `dist`
5. Set Environment Variable:
   - `VITE_API_BASE_URL=https://your-backend-domain.onrender.com`

---

## 🎓 Placement & Technical Interview Guide

### 💡 1. Project Elevator Pitch (30 seconds)
> *"I developed the IIPS Smart Classroom Attendance Management System, a full-stack web application designed to eliminate roll-call inefficiencies and proxy attendance. It uses FastAPI, React, and SQLAlchemy. Teachers generate time-limited, cryptographically signed dynamic QR codes, allowing students to check in from mobile devices in one tap. The backend automatically marks absentees when sessions expire and exports clean CSV reports for academic record-keeping."*

### 🔍 2. Common Technical Interview Questions & Answers

#### Q1: How did you prevent students from sharing the QR code with friends outside the classroom?
- **Dynamic Expiry & Time-boxing**: QR codes contain short-lived JWT tokens signed with a secret key and expiration timestamp (`exp`).
- **Session Roster Snapshot**: Only students enrolled prior to session creation can be marked present; un-enrolled IDs are rejected.
- **One-time Check-in (Idempotency)**: Database unique constraint on `(session_id, student_id)` prevents multiple check-ins.

#### Q2: Why did you choose FastAPI over Flask or Django?
- **Asynchronous performance**: Built on Starlette and Uvicorn with async/await support.
- **Pydantic Data Validation**: Strict type enforcement prevents malformed data from reaching database layers.
- **Automatic OpenAPI Documentation**: Swagger UI (`/docs`) is generated automatically from schemas.

#### Q3: How is absence recorded accurately?
- When an attendance session starts, a `SessionRoster` snapshot is created from currently active enrolled students.
- When the teacher closes the session (or the timer expires), the system calculates the set difference: `EnrolledStudents - CheckedInStudents` and writes `ABSENT` records in a single transactional batch.

#### Q4: What security practices are implemented?
- Passwords hashed with **Bcrypt** with custom salt.
- JWT Bearer Token validation on all administrative endpoints.
- CSV Injection mitigation: Sanitization of special characters (`=`, `+`, `-`, `@`) during report exports.
- `.gitignore` prevents leaks of secret keys, database files, and virtual environments.

---

## 🔮 Future Enhancements & Scope

- [ ] **Geolocation Fencing**: Enforce GPS radius checks so students must be within classroom coordinates.
- [ ] **Face Recognition / Biometric Layer**: Secondary verification step for high-stakes examinations.
- [ ] **Multi-Teacher RBAC**: Departmental role-based access control (HOD, Professor, Lab Assistant).
- [ ] **Push & WhatsApp Notifications**: Automated absence alerts to parents/students.
- [ ] **LMS Integration**: Webhook synchronization with Moodle / Google Classroom.