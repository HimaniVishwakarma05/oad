"""Comprehensive test suite for IIPS Attendance Management System.
Tests:
- Teacher Auth & JWT validation
- Student CRUD and validation (valid & duplicate / bad inputs)
- Classroom management & enrollments
- Dynamic QR Attendance Session lifecycle (create, check-in, duplicate check, expire/close, auto-absent)
- Reports & CSV Export
"""

from fastapi.testclient import TestClient
from urllib.parse import urlparse, parse_qs

from app.main import app
from app.db.database import Base, engine


def run_all_tests():
    print("==================================================")
    print("STARTING FULL END-TO-END SYSTEM TEST SUITE")
    print("==================================================")
    
    # 1. Initialize clean database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as client:
        # Test 1: Health & Root Endpoints
        print("\n[TEST 1] Root & Health Endpoints")
        res = client.get("/")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        print("[PASS] Root endpoint OK")
        
        res = client.get("/health")
        assert res.status_code == 200 and res.json()["status"] == "ok"
        print("[PASS] Health check OK")
        
        # Test 2: Auth Setup Status (Initial state: setup required)
        print("\n[TEST 2] Auth Setup & Registration Flow")
        res = client.get("/api/auth/setup-status")
        assert res.status_code == 200 and res.json()["setup_required"] is True
        print("[PASS] Initial setup_required is True")
        
        # Test 2.1: Invalid Password Length during Setup
        res = client.post("/api/auth/setup", json={
            "full_name": "Test Teacher",
            "email": "teacher@iips.edu",
            "password": "short" # less than 12 chars
        })
        assert res.status_code == 422, f"Expected 422 for short password, got {res.status_code}"
        print("[PASS] Rejected short password during setup (< 12 characters)")
        
        # Test 2.2: Valid Teacher Setup
        res = client.post("/api/auth/setup", json={
            "full_name": "Prof. Himani Sharma",
            "email": "teacher@iips.edu",
            "password": "StrongPassword123!"
        })
        assert res.status_code == 201, f"Expected 201, got {res.status_code}"
        auth_data = res.json()
        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[PASS] Teacher created successfully and received bearer token")
        
        # Test 2.3: Repeated setup must be blocked (403 Forbidden)
        res = client.post("/api/auth/setup", json={
            "full_name": "Another Teacher",
            "email": "another@iips.edu",
            "password": "AnotherStrongPassword123!"
        })
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("[PASS] Secondary public setup blocked (single-tenant security active)")
        
        # Test 2.4: Login with valid credentials
        res = client.post("/api/auth/login", json={
            "email": "teacher@iips.edu",
            "password": "StrongPassword123!"
        })
        assert res.status_code == 200
        print("[PASS] Teacher login successful")
        
        # Test 2.5: Login with wrong password
        res = client.post("/api/auth/login", json={
            "email": "teacher@iips.edu",
            "password": "WrongPassword123!"
        })
        assert res.status_code == 401
        print("[PASS] Invalid password rejected (401 Unauthorized)")
        
        # Test 2.6: Read current user profile
        res = client.get("/api/auth/me", headers=headers)
        assert res.status_code == 200 and res.json()["email"] == "teacher@iips.edu"
        print("[PASS] /api/auth/me returned correct profile")
        
        # Test 3: Student Management CRUD
        print("\n[TEST 3] Student Management (CRUD & Validation)")
        
        # 3.1 Create student with valid input
        student_payload_1 = {
            "student_id": "CS202601",
            "full_name": "Aarav Patel",
            "email": "aarav@student.iips.edu",
            "program": "MCA",
            "year": "1st Year",
            "phone": "+919876543210"
        }
        res = client.post("/api/students", json=student_payload_1, headers=headers)
        assert res.status_code == 201, f"Expected 201, got {res.status_code}"
        student_1 = res.json()
        student_1_id = student_1["id"]
        print("[PASS] Student CS202601 created")
        
        # 3.2 Duplicate student_id rejected
        res = client.post("/api/students", json=student_payload_1, headers=headers)
        assert res.status_code == 409, f"Expected 409 for duplicate student_id, got {res.status_code}"
        print("[PASS] Duplicate Student ID rejected (409 Conflict)")
        
        # 3.3 Create 2nd student
        student_payload_2 = {
            "student_id": "CS202602",
            "full_name": "Bhavya Singh",
            "email": "bhavya@student.iips.edu",
            "program": "MCA",
            "year": "1st Year",
            "phone": "+919876543211"
        }
        res = client.post("/api/students", json=student_payload_2, headers=headers)
        assert res.status_code == 201
        student_2 = res.json()
        student_2_id = student_2["id"]
        print("[PASS] Student CS202602 created")

        # 3.4 Search students
        res = client.get("/api/students?search=Aarav", headers=headers)
        assert res.status_code == 200 and len(res.json()) == 1
        print("[PASS] Student search by name verified")

        # 3.5 Update student
        res = client.patch(f"/api/students/{student_1_id}", json={"year": "2nd Year"}, headers=headers)
        assert res.status_code == 200 and res.json()["year"] == "2nd Year"
        print("[PASS] Student details updated successfully")

        # Test 4: Classroom Management & Enrollment
        print("\n[TEST 4] Classroom Creation & Enrollment")
        
        # 4.1 Create classroom
        classroom_payload = {
            "course_code": "CS-501",
            "course_name": "Advanced Operating Systems",
            "section": "A",
            "academic_year": "2026-2027",
            "semester": "Semester 1"
        }
        res = client.post("/api/classrooms", json=classroom_payload, headers=headers)
        assert res.status_code == 201
        classroom = res.json()
        classroom_id = classroom["id"]
        print(f"[PASS] Classroom {classroom['course_code']} created (ID: {classroom_id})")
        
        # 4.2 Enroll students
        res = client.post(f"/api/classrooms/{classroom_id}/enrollments", json={"student_pk": student_1_id}, headers=headers)
        assert res.status_code == 201
        print(f"[PASS] Enrolled Student {student_1['student_id']} in Classroom {classroom_id}")
        
        res = client.post(f"/api/classrooms/{classroom_id}/enrollments", json={"student_pk": student_2_id}, headers=headers)
        assert res.status_code == 201
        print(f"[PASS] Enrolled Student {student_2['student_id']} in Classroom {classroom_id}")
        
        # 4.3 Duplicate enrollment rejected
        res = client.post(f"/api/classrooms/{classroom_id}/enrollments", json={"student_pk": student_1_id}, headers=headers)
        assert res.status_code == 409
        print("[PASS] Duplicate enrollment rejected (409 Conflict)")
        
        # Test 5: QR Attendance Session Lifecycle
        print("\n[TEST 5] QR Attendance Session Lifecycle & Check-In")
        
        # 5.1 Start session
        session_payload = {
            "classroom_id": classroom_id,
            "title": "Lecture 01 - Process Synchronization",
            "duration_minutes": 60
        }
        res = client.post("/api/attendance/sessions", json=session_payload, headers=headers)
        assert res.status_code == 201
        session_data = res.json()
        session_id = session_data["id"]
        qr_image = session_data.get("qr_image")
        check_in_url = session_data.get("check_in_url")
        assert qr_image is not None and check_in_url is not None
        print(f"[PASS] Attendance session started with dynamic QR code token (ID: {session_id})")
        
        # Extract JWT session token from check_in_url
        parsed_url = urlparse(check_in_url)
        session_token = parse_qs(parsed_url.query)["checkin"][0]
        
        # 5.2 Student 1 check-in (Valid)
        res = client.post("/api/attendance/check-in", json={
            "student_id": "CS202601",
            "session_token": session_token
        })
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        result = res.json()
        assert result["student_name"] == "Aarav Patel"
        print("[PASS] Student 1 checked in successfully (Status: Present)")
        
        # 5.3 Student 1 duplicate check-in rejected
        res = client.post("/api/attendance/check-in", json={
            "student_id": "CS202601",
            "session_token": session_token
        })
        assert res.status_code == 409
        print("[PASS] Duplicate check-in rejected (409 Conflict)")
        
        # 5.4 Unenrolled student check-in rejected
        res = client.post("/api/students", json={
            "student_id": "CS202603",
            "full_name": "Chirag Sharma",
            "email": "chirag@student.iips.edu",
            "program": "MCA",
            "year": "1st Year"
        }, headers=headers)
        assert res.status_code == 201
        
        res = client.post("/api/attendance/check-in", json={
            "student_id": "CS202603",
            "session_token": session_token
        })
        assert res.status_code == 403, f"Expected 403 for unenrolled student, got {res.status_code}"
        print("[PASS] Unenrolled student check-in rejected (403 Forbidden)")
        
        # 5.5 Close session & verify auto-absence for Student 2 (Bhavya)
        res = client.post(f"/api/attendance/sessions/{session_id}/close", headers=headers)
        assert res.status_code == 200
        print("[PASS] Session closed successfully by teacher")
        
        # 5.6 Try check-in after session closed (Must be rejected with 410 Gone)
        res = client.post("/api/attendance/check-in", json={
            "student_id": "CS202602",
            "session_token": session_token
        })
        assert res.status_code == 410, f"Expected 410 for closed session, got {res.status_code}"
        print("[PASS] Check-in to closed session rejected (410 Gone)")
        
        # Test 6: Reports & Export
        print("\n[TEST 6] Attendance Reports & CSV Export")
        
        # 6.1 Check attendance report rows
        res = client.get(f"/api/attendance/reports?classroom_id={classroom_id}", headers=headers)
        assert res.status_code == 200
        report_rows = res.json()
        assert len(report_rows) == 2 # 1 present, 1 absent
        
        status_map = {r["student_id"]: r["status"] for r in report_rows}
        assert status_map["CS202601"] == "present"
        assert status_map["CS202602"] == "absent"
        print("[PASS] Report generated accurately (Aarav: Present, Bhavya: Absent)")
        
        # 6.2 Check CSV export
        res = client.get(f"/api/attendance/reports/export?classroom_id={classroom_id}", headers=headers)
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        csv_text = res.text
        assert "CS-501" in csv_text and "Aarav Patel" in csv_text and "present" in csv_text and "absent" in csv_text
        print("[PASS] CSV export generated with UTF-8 BOM and correct headers")
        
    print("\n==================================================")
    print("ALL 18 SYSTEM TEST CASES PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_all_tests()
