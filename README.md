# 👤 Face Recognition Biometric Attendance Management System

A production-quality, open-source **Face Recognition Biometric Attendance System** built with **Python, Flask, OpenCV, SQLAlchemy, and Modern HTML5/CSS3/JavaScript**.

Designed for college deployment, kiosk displays, and local laptop setups.

---

## 🌟 Key Features

* **Biometric Kiosk View (`/attendance`)**:
  * Real-time camera feed with interactive face guide overlay.
  * Live status transitions: *Looking for Face*, *Face Detected*, *Recognizing...*, *Attendance Marked*, *Attendance Already Marked*, *Face Not Recognized*, *Multiple Faces Detected*.
  * Audio & visual feedback on successful recognition.
  * Controlled 700ms frame sampling with a 4-second post-scan cooldown.

* **Mandatory Duplicate Attendance Protection**:
  * Enforces **strictly one attendance record per student per day**.
  * Database-level composite unique constraint: `UNIQUE(student_id, attendance_date)`.
  * Prevents duplicate entries even under concurrent network or API requests.

* **Admin Panel (`/admin`)**:
  * **Dashboard**: KPI stat cards (*Total Students*, *Present Today*, *Absent Today*, *Attendance %*, *Registered Faces*) and live activity table.
  * **Secure Authentication**: Admin login protected by password hashing (Werkzeug) and session management (Flask-Login).
  * **Student Directory**: Full student management (Add, Edit, Soft Delete/Deactivate, Search by Name/Roll No/ID, Filter by Course & Division).
  * **Guided Face Registration**: 5-sample multi-angle camera frame collector, face uniqueness validation against existing database embeddings.
  * **Attendance Log Records**: Search, filter by date range, course, division, and export to **CSV** and **Excel (`.xlsx`)**.
  * **Analytics & Reports**: Breakdown of Present vs. Absent students (auto-calculated as `Active Students - Present Students` for selected date).
  * **Biometric Privacy Notice**: Local mathematical embedding storage, zero third-party cloud sharing, and data deletion policy.

---

## 🏗️ Technology Stack

* **Backend Framework**: Python 3.10+, Flask 3.1
* **Database**: SQLite (default local DB) with SQLAlchemy ORM
* **Authentication**: Flask-Login, Werkzeug Security (Scrypt password hashing)
* **Computer Vision**: OpenCV (`opencv-python`), NumPy, L2-normalized 512-d multi-scale spatial Pyramids & LBP feature embeddings, Cosine distance matching
* **Data Export**: Pandas, OpenPyXL
* **Frontend**: HTML5, Vanilla CSS3 (Custom Dark/Light tokens, Glassmorphism, Responsive layout), Modern JavaScript (Fetch API, WebRTC MediaDevices Camera Stream)
* **Testing**: Python `unittest` / `pytest`

### Why OpenCV + Feature Vector Embeddings?
We chose **OpenCV with spatial/LBP feature extraction and Cosine distance similarity** over raw `dlib` / `face_recognition` binaries because it installs cleanly across all platforms (**macOS Apple Silicon/Intel, Windows, Linux**) without requiring C++ compilers (`cmake` or `dlib` build failures), making it 100% reliable for local college project deployment.

---

## 📁 Project Structure

```
attendance/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # App factory & DB initialization
│   │   ├── config.py            # Environment & application configuration
│   │   ├── models.py            # SQLAlchemy schemas (Admin, Student, FaceEmbedding, Attendance)
│   │   ├── routes/
│   │   │   ├── auth.py          # Admin login / logout
│   │   │   ├── admin.py         # Dashboard, Student CRUD, Face Registration, Records, Reports
│   │   │   ├── attendance.py    # Kiosk view & /api/attendance/recognize
│   │   │   └── api.py           # REST endpoints & CSV/Excel export handlers
│   │   ├── services/
│   │   │   ├── face_service.py   # OpenCV face detection, feature extraction, distance matching
│   │   │   └── report_service.py # Analytics, present/absent calculations, Pandas exporters
│   │   ├── static/
│   │   │   ├── css/             # main.css, kiosk.css
│   │   │   └── js/              # main.js, face_register.js, kiosk.js
│   │   └── templates/           # HTML templates (Admin views & Kiosk)
├── instance/                    # SQLite database storage (attendance.db)
├── tests/                       # Automated test suite
│   ├── test_auth.py
│   ├── test_student.py
│   └── test_attendance.py
├── .env.example
├── .env                         # Local environment variables
├── requirements.txt
├── README.md
└── run.py                       # Application entry point
```

---

## ⚡ Quick Start Guide

### 1. Clone or Open Workspace
Navigate to the project root directory:
```bash
cd attendance
```

### 2. Set Up Virtual Environment

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Default credentials configured in `.env`:
* **Admin Username**: `admin`
* **Admin Password**: `Admin@123`
* **Kiosk URL**: `http://127.0.0.1:5000/attendance`
* **Admin URL**: `http://127.0.0.1:5000/admin`

### 5. Run the Application
```bash
python run.py
```

The application automatically creates the SQLite database (`instance/attendance.db`) and seeds the default admin account on first launch!

---

## 📖 Usage Walkthrough

### Step 1: Admin Login
1. Open `http://127.0.0.1:5000/admin/login` in your browser.
2. Enter default credentials:
   * **Username**: `admin`
   * **Password**: `Admin@123`

### Step 2: Register a Student
1. Navigate to **Register Student** from the sidebar (`/admin/students/register`).
2. Enter Name, Roll Number, Student ID, Course, Year, and Division.
3. Click **Save & Proceed to Face Registration**.

### Step 3: Face Biometric Registration
1. On the Face Registration workspace (`/admin/students/<id>/register-face`), click **Start Camera**.
2. Allow browser camera permissions.
3. Position student's face inside the oval guide box.
4. Click **Capture Sample** 5 times as the student slightly adjusts face angle/expression.
5. The system extracts face embeddings, checks against existing students to prevent duplicate face registration, and saves to the database.

### Step 4: Mark Attendance via Kiosk
1. Open the Biometric Kiosk at `http://127.0.0.1:5000/attendance`.
2. Position the registered student's face inside the frame guide box.
3. System automatically detects face, extracts embedding, compares against database vectors, and displays:
   * **Name**: Bhushan Padghan
   * **Roll No**: 101 (STU-2026-101)
   * **Status**: PRESENT
   * **Logged Time**: 09:32:15 AM
4. If the same student stays or appears again on the same day, the kiosk displays:
   * **Status**: Attendance Already Marked
   * **Time**: 09:32:15 AM
   *(No duplicate row created in database!)*

### Step 5: View Records & Export Reports
1. In Admin Panel, visit **Attendance Records** (`/admin/records`).
2. Search by student name, roll number, or filter by date range, course, or division.
3. Click **Export CSV** or **Export Excel (.xlsx)** to download generated reports.
4. Visit **Reports** (`/admin/reports`) to inspect Present vs. Absent student lists.

---

## 🔒 Security & Biometric Privacy

1. **Database Constraint**: Daily unique composite index `UNIQUE(student_id, attendance_date)` prevents duplicate records at the database engine level.
2. **Password Security**: Passwords hashed using Werkzeug Scrypt password hashing algorithm.
3. **Protected Admin Routes**: All admin operations require authenticated sessions via `@login_required`.
4. **Local Biometric Processing**: Biometric embeddings are stored as mathematical vectors locally. Raw video feeds or face photographs are never sent to external cloud APIs.
5. **Data Right to Erasure**: Admin can delete or re-register student face embeddings at any time.

---

## 🧪 Running Automated Tests

Run the full automated test suite to verify database constraints, authentication, student CRUD, face matching, and duplicate prevention:

```bash
python -m unittest discover tests
```

Expected Output:
```text
Ran 7 tests in 0.88s
OK
```

---

## ⚙️ Troubleshooting

* **Camera Permission Error**:
  Ensure your web browser (Chrome/Safari/Edge/Firefox) has permission to access the webcam. On macOS, check *System Settings > Privacy & Security > Camera*.
* **Port 5000 in Use**:
  Set custom port in `.env`: `PORT=5001` or run `python run.py`.
* **Database Reset**:
  To start with a clean database, delete `instance/attendance.db` and restart `python run.py`.

---

## 📄 License & Project Scope

This software is an open-source college project designed for demonstration, educational, and institutional attendance tracking.
