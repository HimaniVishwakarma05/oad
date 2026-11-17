"""Generate a professional, beautiful PDF guide for IIPS Attendance Management System."""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

PDF_OUTPUT_PATH = os.path.abspath("IIPS_Attendance_Interview_Preparation_Guide.pdf")


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1e3a8a") # Deep Navy Blue
    secondary_color = colors.HexColor("#2563eb") # Royal Blue
    accent_bg = colors.HexColor("#f8fafc") # Light Slate
    card_border = colors.HexColor("#cbd5e1") # Slate border
    text_dark = colors.HexColor("#0f172a") # Charcoal
    text_muted = colors.HexColor("#475569") # Muted slate

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=1, # Center
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=text_muted,
        alignment=1,
        spaceAfter=15,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_dark,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_dark,
        leftIndent=14,
        spaceAfter=3,
    )

    pitch_box_style = ParagraphStyle(
        "PitchBox",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
    )

    q_style = ParagraphStyle(
        "Question",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=6,
        spaceAfter=2,
    )

    ans_style = ParagraphStyle(
        "Answer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_dark,
        leftIndent=8,
        spaceAfter=6,
    )

    story = []

    # Title & Header
    story.append(Paragraph("IIPS Smart Classroom Attendance Management System", title_style))
    story.append(Paragraph("Major Project Placement, Viva & Technical Interview Preparation Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=0, spaceAfter=12))

    # Part 1: Self-Introduction Pitch
    story.append(Paragraph("🎓 Part 1: Project Self-Introduction Pitch (1–2 Minute Pitch)", h1_style))
    
    pitch_text = """
    <b>"Good morning / afternoon sir/ma'am.</b><br/><br/>
    My major project is the <b>IIPS Smart Classroom Attendance Management System</b>.<br/><br/>
    In universities, traditional manual roll calls consume 10 to 15 minutes of lecture time, are vulnerable to proxy attendance, and require tedious manual entry into spreadsheets.<br/><br/>
    To solve this, I designed and developed a full-stack, real-time web application using <b>FastAPI (Python)</b>, <b>React.js (Vite)</b>, and <b>SQLAlchemy</b>.<br/><br/>
    In our system, the teacher launches an attendance session with a configurable timer. The backend generates a <b>time-limited, cryptographically signed dynamic QR code</b> embedded with a JWT token. Students scan the QR code with their phone camera to check in with a single tap.<br/><br/>
    The system enforces a <b>roster snapshot mechanism</b>, prevents duplicate check-ins, automatically revokes expired QR tokens, reconciles absent students upon session closure, and provides real-time dashboard analytics and filtered CSV report exports."
    """
    
    pitch_table = Table([[Paragraph(pitch_text, pitch_box_style)]], colWidths=[530])
    pitch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94a3b8")),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(pitch_table)
    story.append(Spacer(1, 10))

    # Part 2: Architecture & Workflow
    story.append(Paragraph("🏛️ Part 2: System Architecture & Workflow", h1_style))
    story.append(Paragraph("The application follows a clean <b>3-tier layered architecture</b> ensuring high modularity and separation of concerns:", body_style))

    tech_table_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Key Role & Responsibility</b>", body_style)],
        [Paragraph("<b>Frontend</b>", body_style), Paragraph("React 18, Vite, Vanilla CSS", body_style), Paragraph("Responsive Single Page App (SPA), real-time counter, camera check-in.", body_style)],
        [Paragraph("<b>Backend API</b>", body_style), Paragraph("FastAPI (Python 3.12)", body_style), Paragraph("Asynchronous REST API, OpenAPI/Swagger docs, high concurrency.", body_style)],
        [Paragraph("<b>Data Validation</b>", body_style), Paragraph("Pydantic v2", body_style), Paragraph("Strict schema validation, type safety, automatic error serialization.", body_style)],
        [Paragraph("<b>ORM & Database</b>", body_style), Paragraph("SQLAlchemy 2.0 (SQLite / MySQL)", body_style), Paragraph("Declarative mapped tables, composite unique constraints, transactions.", body_style)],
        [Paragraph("<b>Security & Auth</b>", body_style), Paragraph("Passlib (Bcrypt) & Python-Jose", body_style), Paragraph("Salted password hashing & time-limited JWT QR signature tokens.", body_style)],
    ]
    tech_table = Table(tech_table_data, colWidths=[90, 150, 290])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    # Workflow Steps
    story.append(Paragraph("<b>End-to-End Attendance Execution Flow:</b>", h2_style))
    story.append(Paragraph("<b>1. Session Initialization:</b> Teacher selects a classroom (e.g. CS-5101 OOAD) and clicks 'Start Session'. Backend freezes the enrolled student roster snapshot.", bullet_style))
    story.append(Paragraph("<b>2. Dynamic Token & QR Generation:</b> Backend signs a time-limited JWT containing session ID, expiration timestamp, and unique UUID (JTI), encoding it into a dynamic QR image.", bullet_style))
    story.append(Paragraph("<b>3. Student Check-In:</b> Student scans the QR with their mobile camera. The app submits Student ID and session token.", bullet_style))
    story.append(Paragraph("<b>4. Anti-Proxy & Duplicate Validation:</b> Backend verifies token signature, checks if session is open, verifies student is in the frozen roster, and prevents duplicate check-ins via database constraint.", bullet_style))
    story.append(Paragraph("<b>5. Automated Absence Marking:</b> When the teacher closes the session, the backend computes <code>Enrolled - Present = Absent</code> and logs absentees automatically.", bullet_style))
    story.append(Spacer(1, 10))

    # Part 3: Top 10 Technical Q&A
    story.append(Paragraph("💡 Part 3: Top Technical Interview Questions & Answers", h1_style))

    qa_list = [
        ("Q1: What is the main problem your project solves?",
         "It replaces time-consuming manual roll calls (saving 10-15 minutes per lecture) and eliminates proxy attendance by enforcing time-boxed dynamic QR codes and database-level enrollment validation."),

        ("Q2: Why did you choose FastAPI over Flask or Django?",
         "FastAPI provides asynchronous execution on ASGI (Uvicorn) with native Pydantic v2 type checking and automatic interactive Swagger documentation (/docs), making API development faster and more secure than traditional Flask."),

        ("Q3: How do you prevent proxy attendance (e.g. sharing QR screenshots)?",
         "1) Dynamic Expiration: QR tokens expire with the session timer (HTTP 410 Gone). 2) Session Roster Snapshot: Only students enrolled before session start are accepted. 3) Database Idempotency: Unique constraint (session_id, student_id) rejects repeated check-ins."),

        ("Q4: Why use JWT inside the QR code instead of a simple session number?",
         "A simple number is easily guessed or brute-forced. A JWT is cryptographically signed with HMAC-SHA256 and contains metadata (session ID, expiration, JTI). The backend verifies authenticity without database lookups on forged requests."),

        ("Q5: Explain your database schema design.",
         "The database is normalized into: 'users' (teachers), 'students' (student directory), 'classrooms' (courses), 'classroom_enrollments' (active mappings), 'attendance_sessions' (lecture instances), 'attendance_session_roster' (frozen snapshot), and 'attendance_records' (attendance status & timestamps)."),

        ("Q6: How does the system determine absent students?",
         "When a session starts, active enrolled IDs are stored in 'attendance_session_roster'. Present students are recorded in 'attendance_records'. On session closure, the backend executes a set-difference query: (Enrolled - Present) and inserts 'ABSENT' records in a single transactional batch."),

        ("Q7: How are passwords secured in the database?",
         "Passwords are never stored in plain text. They are hashed using Bcrypt with a 12-round salt. On login, constant-time verification is performed to prevent timing attacks."),

        ("Q8: How did you protect against CSV Formula Injection in exported reports?",
         "Exported cells starting with formula trigger characters (=, +, -, @, \\t) are sanitized by prepending a single quote ('). This prevents formula execution when opened in Microsoft Excel."),

        ("Q9: What challenging bug did you face and how did you resolve it?",
         "During testing, Python 3.12 raised a TypeError when subtracting offset-naive and offset-aware datetimes between SQLite and memory. I resolved this by writing a timezone normalization helper ensuring consistent UTC timestamps across all models and routes."),

        ("Q10: What are future improvements for this project?",
         "Future scope includes: 1) Geolocation fencing to ensure student presence within classroom coordinates, 2) RFID physical card reader integration, and 3) LMS webhook integration with Google Classroom/Moodle."),
    ]

    for q, a in qa_list:
        story.append(Paragraph(f"<b>{q}</b>", q_style))
        story.append(Paragraph(a, ans_style))

    story.append(Spacer(1, 10))

    # Part 4: Live Demo Script
    story.append(Paragraph("🎬 Part 4: Step-by-Step Live Demo Presentation Script", h1_style))
    story.append(Paragraph("Follow this structured 5-step demonstration in front of your examiner/interviewer:", body_style))

    demo_steps = [
        ("Step 1: Teacher Login", "Open http://localhost:5173 -> Sign in as Teacher (himani@gmail.com / admin12345678). Highlight the responsive academic layout."),
        ("Step 2: Show Classrooms & Roster", "Navigate to Students & QR Attendance tabs. Show real IIPS courses (e.g. CS-5101 OOAD, CS-5201 DBMS) and active enrolled students."),
        ("Step 3: Launch Session & Display QR", "Select CS-5101 OOAD -> Click 'Start Session' (Duration: 60 mins). Show dynamic QR code generated in real-time."),
        ("Step 4: Check In Student", "Click 'Open check-in in new tab' (or scan with phone). Enter Student ID: 'Himani' -> Click 'Record attendance'. Show green confirmation and live counter updated to 1 on Teacher screen."),
        ("Step 5: Close Session & Export Report", "Click 'Close Session' (QR code immediately revoked). Open 'Reports' tab -> Show Himani is 'Present' while other students are marked 'Absent'. Click 'Export CSV' to download spreadsheet."),
    ]

    for step_title, step_desc in demo_steps:
        story.append(Paragraph(f"<b>{step_title}</b>: {step_desc}", bullet_style))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=card_border, spaceBefore=5, spaceAfter=8))
    story.append(Paragraph("<i>IIPS Smart Classroom Attendance Management System — Major Project Preparation Document</i>", subtitle_style))

    doc.build(story)
    print(f"PDF successfully generated at: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
