import { useEffect, useMemo, useRef, useState } from 'react';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const TOKEN_KEY = 'iips_access_token';
const STUDENT_ID_KEY = 'iips_student_id';
const CHECK_IN_TOKEN = new URLSearchParams(window.location.search).get('checkin');
const EMPTY_STUDENT = {
  student_id: '',
  full_name: '',
  email: '',
  phone: '',
  program: '',
  year: '',
};
const EMPTY_CLASSROOM = {
  course_code: '',
  course_name: '',
  section: '',
  academic_year: '',
  semester: '',
};

async function apiRequest(path, options = {}) {
  const { token, ...requestOptions } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestOptions,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...requestOptions.headers,
    },
  });
  const result = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = result?.detail;
    const message = Array.isArray(detail)
      ? detail.map((issue) => `${issue.loc?.slice(-1)[0] || 'Field'}: ${issue.msg}`).join('. ')
      : detail || `Request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return result;
}

function App() {
  const [students, setStudents] = useState([]);
  const [authStatus, setAuthStatus] = useState('checking');
  const [setupRequired, setSetupRequired] = useState(false);
  const [user, setUser] = useState(null);
  const [authForm, setAuthForm] = useState({ full_name: '', email: '', password: '' });
  const [studentSignInId, setStudentSignInId] = useState(
    () => localStorage.getItem(STUDENT_ID_KEY) || '',
  );
  const [signedInStudentId, setSignedInStudentId] = useState(
    () => localStorage.getItem(STUDENT_ID_KEY) || '',
  );
  const [authLoading, setAuthLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_STUDENT);
  const [activePage, setActivePage] = useState('students');
  const [classrooms, setClassrooms] = useState([]);
  const [enrollmentClassroomId, setEnrollmentClassroomId] = useState('');
  const [enrollmentStudents, setEnrollmentStudents] = useState([]);
  const [classroomEnrollments, setClassroomEnrollments] = useState([]);
  const [enrollmentLoading, setEnrollmentLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [reportRows, setReportRows] = useState([]);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportFilters, setReportFilters] = useState({
    classroom_id: '',
    date_from: '',
    date_to: '',
  });
  const [reportDraft, setReportDraft] = useState({
    classroom_id: '',
    date_from: '',
    date_to: '',
  });
  const [classroomForm, setClassroomForm] = useState(EMPTY_CLASSROOM);
  const [sessionForm, setSessionForm] = useState({
    classroom_id: '',
    title: '',
    duration_minutes: 90,
  });
  const [checkInStudentId, setCheckInStudentId] = useState('');
  const [checkInLoading, setCheckInLoading] = useState(false);
  const [checkInResult, setCheckInResult] = useState(null);
  const [checkInError, setCheckInError] = useState('');
  const autoCheckInStarted = useRef(false);
  const [teacherLoginOpen, setTeacherLoginOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function checkSession() {
      if (CHECK_IN_TOKEN) {
        setAuthStatus('checkin');
        return;
      }
      try {
        const setup = await apiRequest('/api/auth/setup-status');
        if (cancelled) return;
        setSetupRequired(setup.setup_required);

        const token = sessionStorage.getItem(TOKEN_KEY);
        if (token) {
          try {
            const currentUser = await apiRequest('/api/auth/me', { token });
            if (cancelled) return;
            setUser(currentUser);
            setAuthStatus('authenticated');
            return;
          } catch {
            sessionStorage.removeItem(TOKEN_KEY);
          }
        }
        if (!cancelled) setAuthStatus('anonymous');
      } catch (requestError) {
        if (!cancelled) {
          const help =
            requestError.status === 500 || String(requestError.message).includes('500')
              ? ' Please ensure the backend server is started on port 8000 (run: uvicorn app.main:app --host 0.0.0.0 --port 8000 in the backend folder).'
              : '';
          setError(`Could not connect to the attendance API: ${requestError.message}.${help}`);
          setAuthStatus('unavailable');
        }
      }
    }

    checkSession();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!CHECK_IN_TOKEN) return;
    const savedStudentId = localStorage.getItem(STUDENT_ID_KEY)?.trim();
    if (!savedStudentId) return;
    setCheckInStudentId(savedStudentId);
    if (autoCheckInStarted.current) return;
    autoCheckInStarted.current = true;
    void recordStudentCheckIn(savedStudentId);
  }, []);

  useEffect(() => {
    if (authStatus !== 'authenticated') {
      setLoading(false);
      return undefined;
    }
    const controller = new AbortController();
    const loadStudents = async () => {
      setLoading(true);
      setError('');
      try {
        const query = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : '';
        const data = await apiRequest(`/api/students${query}`, {
          signal: controller.signal,
          token: sessionStorage.getItem(TOKEN_KEY),
        });
        setStudents(data);
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          if (!handleUnauthorized(requestError)) {
            setError(requestError.message);
          }
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };

    loadStudents();
    return () => controller.abort();
  }, [authStatus, search]);

  useEffect(() => {
    if (authStatus !== 'authenticated' || activePage !== 'attendance') {
      return undefined;
    }
    let cancelled = false;
    const token = sessionStorage.getItem(TOKEN_KEY);
    async function loadAttendancePage() {
      setError('');
      try {
        const [roomList, sessionList] = await Promise.all([
          apiRequest('/api/classrooms', { token }),
          apiRequest('/api/attendance/sessions', { token }),
        ]);
        if (cancelled) return;
        setClassrooms(roomList);
        setSessions(sessionList);
        setEnrollmentClassroomId((current) => (
          current && roomList.some((room) => String(room.id) === current)
            ? current
            : roomList[0] ? String(roomList[0].id) : ''
        ));
        setSessionForm((current) => ({
          ...current,
          classroom_id: current.classroom_id || (roomList[0] ? String(roomList[0].id) : ''),
        }));
        const activeSession = sessionList.find((session) => session.status === 'active');
        if (activeSession) {
          const detail = await apiRequest(`/api/attendance/sessions/${activeSession.id}`, { token });
          if (cancelled) return;
          setSelectedSession(detail);
          const records = await apiRequest(
            `/api/attendance/sessions/${activeSession.id}/records`,
            { token },
          );
          if (!cancelled) setAttendanceRecords(records);
        } else {
          setSelectedSession(null);
          setAttendanceRecords([]);
        }
      } catch (requestError) {
        if (!cancelled && !handleUnauthorized(requestError)) {
          setError(requestError.message);
        }
      }
    }
    loadAttendancePage();
    return () => {
      cancelled = true;
    };
  }, [activePage, authStatus]);

  useEffect(() => {
    if (
      authStatus !== 'authenticated'
      || activePage !== 'attendance'
      || !enrollmentClassroomId
    ) {
      setEnrollmentStudents([]);
      setClassroomEnrollments([]);
      return undefined;
    }
    let cancelled = false;
    async function loadClassroomRoster() {
      setEnrollmentLoading(true);
      try {
        const token = sessionStorage.getItem(TOKEN_KEY);
        const [roster, enrolled] = await Promise.all([
          apiRequest('/api/students', { token }),
          apiRequest(`/api/classrooms/${enrollmentClassroomId}/enrollments`, { token }),
        ]);
        if (cancelled) return;
        setEnrollmentStudents(roster);
        setClassroomEnrollments(enrolled);
      } catch (requestError) {
        if (!cancelled && !handleUnauthorized(requestError)) setError(requestError.message);
      } finally {
        if (!cancelled) setEnrollmentLoading(false);
      }
    }
    loadClassroomRoster();
    return () => {
      cancelled = true;
    };
  }, [activePage, authStatus, enrollmentClassroomId]);

  useEffect(() => {
    if (authStatus !== 'authenticated' || activePage !== 'reports') {
      return undefined;
    }
    let cancelled = false;
    async function loadReport() {
      setReportLoading(true);
      setError('');
      const queryParams = new URLSearchParams();
      if (reportFilters.classroom_id) queryParams.set('classroom_id', reportFilters.classroom_id);
      if (reportFilters.date_from) queryParams.set('date_from', reportFilters.date_from);
      if (reportFilters.date_to) queryParams.set('date_to', reportFilters.date_to);
      const query = queryParams.size ? `?${queryParams.toString()}` : '';
      try {
        const [roomList, rows] = await Promise.all([
          apiRequest('/api/classrooms', { token: sessionStorage.getItem(TOKEN_KEY) }),
          apiRequest(`/api/attendance/reports${query}`, { token: sessionStorage.getItem(TOKEN_KEY) }),
        ]);
        if (cancelled) return;
        setClassrooms(roomList);
        setReportRows(rows);
      } catch (requestError) {
        if (!cancelled && !handleUnauthorized(requestError)) setError(requestError.message);
      } finally {
        if (!cancelled) setReportLoading(false);
      }
    }
    loadReport();
    return () => {
      cancelled = true;
    };
  }, [activePage, authStatus, reportFilters]);

  useEffect(() => {
    if (!selectedSession || selectedSession.status !== 'active') return undefined;
    const timer = window.setInterval(async () => {
      try {
        const token = sessionStorage.getItem(TOKEN_KEY);
        const [records, detail] = await Promise.all([
          apiRequest(`/api/attendance/sessions/${selectedSession.id}/records`, { token }),
          apiRequest(`/api/attendance/sessions/${selectedSession.id}`, { token }),
        ]);
        setAttendanceRecords(records);
        setSelectedSession(detail);
        if (detail.status !== 'active') {
          const sessionList = await apiRequest('/api/attendance/sessions', { token });
          setSessions(sessionList);
        }
      } catch (requestError) {
        if (!handleUnauthorized(requestError)) {
          setError(requestError.message);
        }
      }
    }, 10000);
    return () => window.clearInterval(timer);
  }, [selectedSession?.id, selectedSession?.status]);

  const activeCount = useMemo(
    () => students.filter((student) => student.is_active).length,
    [students],
  );

  const enrolledStudentPks = useMemo(
    () => new Set(classroomEnrollments.map((enrollment) => enrollment.student_pk)),
    [classroomEnrollments],
  );

  const selectedClassEnrolledCount = useMemo(
    () => classroomEnrollments.filter((enrollment) => (
      enrollmentStudents.some((student) => (
        student.id === enrollment.student_pk && student.is_active
      ))
    )).length,
    [classroomEnrollments, enrollmentStudents],
  );

  async function exportAttendanceReport() {
    const queryParams = new URLSearchParams();
    if (reportFilters.classroom_id) queryParams.set('classroom_id', reportFilters.classroom_id);
    if (reportFilters.date_from) queryParams.set('date_from', reportFilters.date_from);
    if (reportFilters.date_to) queryParams.set('date_to', reportFilters.date_to);
    const query = queryParams.size ? `?${queryParams.toString()}` : '';
    try {
      const response = await fetch(`${API_BASE_URL}/api/attendance/reports/export${query}`, {
        headers: { Authorization: `Bearer ${sessionStorage.getItem(TOKEN_KEY)}` },
      });
      if (!response.ok) {
        const result = await response.json().catch(() => null);
        const error = new Error(result?.detail || `Export failed (${response.status})`);
        error.status = response.status;
        throw error;
      }
      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = 'attendance-report.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
    } catch (requestError) {
      if (requestError.status === 401 && handleUnauthorized(requestError)) return;
      setError(requestError.message);
    }
  }

  function startRegistration() {
    setEditingId(null);
    setForm(EMPTY_STUDENT);
    setError('');
    setNotice('');
    setFormOpen(true);
  }

  function startEditing(student) {
    setEditingId(student.id);
    setForm({
      student_id: student.student_id,
      full_name: student.full_name,
      email: student.email || '',
      phone: student.phone || '',
      program: student.program || '',
      year: student.year || '',
    });
    setError('');
    setNotice('');
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setEditingId(null);
    setForm(EMPTY_STUDENT);
  }

  function updateForm(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  function updateAuthForm(event) {
    setAuthForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  function signInStudent(event) {
    event.preventDefault();
    const studentId = studentSignInId.trim();
    if (studentId.length < 3) {
      setError('Enter a student ID with at least 3 characters.');
      return;
    }
    localStorage.setItem(STUDENT_ID_KEY, studentId);
    setStudentSignInId(studentId);
    setSignedInStudentId(studentId);
    setError('');
    setNotice(`Ready to scan as ${studentId}. Scan the class QR with this browser.`);
  }

  function signOutStudent() {
    localStorage.removeItem(STUDENT_ID_KEY);
    setStudentSignInId('');
    setSignedInStudentId('');
    setCheckInStudentId('');
    setCheckInResult(null);
    setCheckInError('');
  }

  function handleUnauthorized(requestError) {
    if (requestError.status !== 401 || !sessionStorage.getItem(TOKEN_KEY)) {
      return false;
    }
    sessionStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setStudents([]);
    setAuthStatus('anonymous');
    setError('Your session has expired. Please sign in again.');
    return true;
  }

  async function submitAuth(event) {
    event.preventDefault();
    setAuthLoading(true);
    setError('');
    setNotice('');
    try {
      const isSetup = setupRequired;
      const session = await apiRequest(isSetup ? '/api/auth/setup' : '/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(
          isSetup
            ? { ...authForm, full_name: authForm.full_name.trim(), email: authForm.email.trim() }
            : { email: authForm.email.trim(), password: authForm.password },
        ),
      });
      sessionStorage.setItem(TOKEN_KEY, session.access_token);
      setUser(session.user);
      setSetupRequired(false);
      setAuthStatus('authenticated');
      setAuthForm({ full_name: '', email: '', password: '' });
      setNotice(isSetup ? 'Teacher account created. You are signed in.' : 'Signed in successfully.');
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) {
        setError(requestError.message);
      }
    } finally {
      setAuthLoading(false);
    }
  }

  function signOut() {
    sessionStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setStudents([]);
    setAuthStatus('anonymous');
    setError('');
    setNotice('You have been signed out.');
  }

  async function saveStudent(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');

    const payload = {
      ...form,
      student_id: form.student_id.trim(),
      full_name: form.full_name.trim(),
      email: form.email.trim() || null,
      phone: form.phone.trim() || null,
      program: form.program.trim() || null,
      year: form.year.trim() || null,
    };

    try {
      if (editingId) {
        await apiRequest(`/api/students/${editingId}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
          token: sessionStorage.getItem(TOKEN_KEY),
        });
        setNotice('Student details updated.');
      } else {
        await apiRequest('/api/students', {
          method: 'POST',
          body: JSON.stringify(payload),
          token: sessionStorage.getItem(TOKEN_KEY),
        });
        setNotice('Student registered.');
      }
      closeForm();
      const query = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : '';
      setStudents(await apiRequest(`/api/students${query}`, {
        token: sessionStorage.getItem(TOKEN_KEY),
      }));
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) {
        setError(requestError.message);
      }
    } finally {
      setSaving(false);
    }
  }

  async function toggleStudentStatus(student) {
    setError('');
    setNotice('');
    try {
      const updated = await apiRequest(`/api/students/${student.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !student.is_active }),
        token: sessionStorage.getItem(TOKEN_KEY),
      });
      setStudents((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setNotice(updated.is_active ? 'Student activated.' : 'Student deactivated.');
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function recordStudentCheckIn(studentId) {
    setCheckInLoading(true);
    setCheckInError('');
    setCheckInResult(null);
    try {
      const result = await apiRequest('/api/attendance/check-in', {
        method: 'POST',
        body: JSON.stringify({
          student_id: studentId,
          session_token: CHECK_IN_TOKEN,
        }),
      });
      localStorage.setItem(STUDENT_ID_KEY, studentId);
      setStudentSignInId(studentId);
      setSignedInStudentId(studentId);
      setCheckInResult(result);
    } catch (requestError) {
      setCheckInError(requestError.message);
    } finally {
      setCheckInLoading(false);
    }
  }

  async function submitStudentCheckIn(event) {
    event.preventDefault();
    const studentId = checkInStudentId.trim();
    if (studentId.length < 3) {
      setCheckInError('Enter a student ID with at least 3 characters.');
      return;
    }
    await recordStudentCheckIn(studentId);
  }

  async function createClassroom(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      const classroom = await apiRequest('/api/classrooms', {
        method: 'POST',
        body: JSON.stringify({
          ...classroomForm,
          course_code: classroomForm.course_code.trim(),
          course_name: classroomForm.course_name.trim(),
          section: classroomForm.section.trim() || null,
          academic_year: classroomForm.academic_year.trim() || null,
          semester: classroomForm.semester.trim() || null,
        }),
        token: sessionStorage.getItem(TOKEN_KEY),
      });
      setClassrooms((current) => [...current, classroom]);
      setEnrollmentClassroomId(String(classroom.id));
      setSessionForm((current) => ({ ...current, classroom_id: String(classroom.id) }));
      setClassroomForm(EMPTY_CLASSROOM);
      setNotice('Classroom created.');
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  async function toggleEnrollment(student) {
    const isEnrolled = enrolledStudentPks.has(student.id);
    setError('');
    setNotice('');
    try {
      const token = sessionStorage.getItem(TOKEN_KEY);
      if (isEnrolled) {
        await apiRequest(
          `/api/classrooms/${enrollmentClassroomId}/enrollments/${student.id}`,
          { method: 'DELETE', token },
        );
        setClassroomEnrollments((current) => current.filter(
          (entry) => entry.student_pk !== student.id,
        ));
        setNotice(`${student.full_name} removed from this classroom.`);
      } else {
        const enrollment = await apiRequest(
          `/api/classrooms/${enrollmentClassroomId}/enrollments`,
          {
            method: 'POST',
            body: JSON.stringify({ student_pk: student.id }),
            token,
          },
        );
        setClassroomEnrollments((current) => [...current, enrollment]);
        setNotice(`${student.full_name} enrolled in this classroom.`);
      }
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(requestError.message);
    }
  }

  async function createAttendanceSession(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const session = await apiRequest('/api/attendance/sessions', {
        method: 'POST',
        body: JSON.stringify({
          ...sessionForm,
          classroom_id: Number(sessionForm.classroom_id),
          duration_minutes: Number(sessionForm.duration_minutes),
        }),
        token: sessionStorage.getItem(TOKEN_KEY),
      });
      setSelectedSession(session);
      setAttendanceRecords([]);
      setSessions((current) => [session, ...current]);
      setNotice('Attendance session is live. Display its QR code for students to scan.');
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  async function closeAttendanceSession() {
    if (!selectedSession) return;
    setSaving(true);
    setError('');
    try {
      const closed = await apiRequest(
        `/api/attendance/sessions/${selectedSession.id}/close`,
        { method: 'POST', token: sessionStorage.getItem(TOKEN_KEY) },
      );
      setSelectedSession(closed);
      setSessions((current) => current.map((session) => (
        session.id === closed.id ? closed : session
      )));
      setNotice('Attendance session closed. Its QR code can no longer be used.');
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  async function showSession(sessionId) {
    setError('');
    try {
      const token = sessionStorage.getItem(TOKEN_KEY);
      const [detail, records] = await Promise.all([
        apiRequest(`/api/attendance/sessions/${sessionId}`, { token }),
        apiRequest(`/api/attendance/sessions/${sessionId}/records`, { token }),
      ]);
      setSelectedSession(detail);
      setAttendanceRecords(records);
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(requestError.message);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">IIPS · Student Administration</p>
          <h1>Smart Classroom Attendance</h1>
        </div>
        {authStatus === 'authenticated' && (
          <div className="account-actions">
            <span className="signed-in-label">Signed in as {user?.full_name}</span>
            <button className="secondary-button" onClick={signOut} type="button">
              Sign out
            </button>
            <button className="primary-button" onClick={startRegistration} type="button">
              Register student
            </button>
          </div>
        )}
      </header>

      {authStatus === 'checking' && (
        <main className="content">
          <section className="panel empty-state" role="status">Checking teacher session…</section>
        </main>
      )}

      {!CHECK_IN_TOKEN && (authStatus === 'anonymous' || authStatus === 'unavailable') && (
        <main className={`content auth-content${setupRequired ? '' : ' student-first'}`}>
          {authStatus === 'unavailable' && error && (
            <p className="feedback error" role="alert">{error}</p>
          )}
          {!setupRequired && (
            <section className="panel auth-panel student-signin-panel" aria-labelledby="student-signin-title">
              <p className="kicker">Student quick check-in</p>
              <h2 id="student-signin-title">Sign in with student ID</h2>
              <p className="subtitle">
                Enter your ID once on this phone. When you scan a class QR with this browser, attendance is recorded automatically.
              </p>
              {signedInStudentId ? (
                <div className="checkin-success" role="status">
                  <strong>Ready to scan</strong>
                  <p>Student ID: {signedInStudentId}</p>
                  <button className="secondary-button" onClick={signOutStudent} type="button">
                    Change student
                  </button>
                </div>
              ) : (
                <form className="auth-form" onSubmit={signInStudent}>
                  <label>
                    Student ID
                    <input
                      autoComplete="off"
                      maxLength={50}
                      minLength={3}
                      onChange={(event) => setStudentSignInId(event.target.value)}
                      required
                      value={studentSignInId}
                    />
                  </label>
                  <button className="primary-button" type="submit">Continue as student</button>
                </form>
              )}
              <p className="optional-label">
                Student ID is not verified by a password. Anyone who knows an enrolled ID could use it.
              </p>
            </section>
          )}
          {(setupRequired || teacherLoginOpen) && (
            <section className="panel auth-panel" aria-labelledby="auth-title">
              <p className="kicker">{setupRequired ? 'First-time setup' : 'Teacher access'}</p>
              <h2 id="auth-title">{setupRequired ? 'Create the teacher account' : 'Sign in to continue'}</h2>
              <p className="subtitle">
                {setupRequired
                  ? 'Set up the first teacher account. Public account registration is disabled after this step.'
                  : 'Manage students, classrooms, and attendance reports.'}
              </p>
              {error && <p className="feedback error" role="alert">{error}</p>}
              <form className="auth-form" onSubmit={submitAuth}>
                {setupRequired && (
                  <label>
                    Full name
                    <input
                      autoComplete="name"
                      maxLength={150}
                      minLength={2}
                      name="full_name"
                      onChange={updateAuthForm}
                      required
                      value={authForm.full_name}
                    />
                  </label>
                )}
                <label>
                  Email
                  <input
                    autoComplete="username"
                    name="email"
                    onChange={updateAuthForm}
                    required
                    type="email"
                    value={authForm.email}
                  />
                </label>
                <label>
                  Password
                  <input
                    autoComplete={setupRequired ? 'new-password' : 'current-password'}
                    maxLength={72}
                    minLength={setupRequired ? 12 : 1}
                    name="password"
                    onChange={updateAuthForm}
                    required
                    type="password"
                    value={authForm.password}
                  />
                  {setupRequired && <span className="optional-label">Use at least 12 characters.</span>}
                </label>
                <button className="primary-button" disabled={authLoading} type="submit">
                  {authLoading
                    ? 'Please wait…'
                    : setupRequired
                      ? 'Create teacher account'
                      : 'Sign in'}
                </button>
              </form>
            </section>
          )}
          {!setupRequired && !teacherLoginOpen && (
            <button
              className="teacher-login-link"
              onClick={() => setTeacherLoginOpen(true)}
              type="button"
            >
              Teacher? Sign in to manage attendance
            </button>
          )}
          {!setupRequired && teacherLoginOpen && (
            <button
              className="teacher-login-link"
              onClick={() => setTeacherLoginOpen(false)}
              type="button"
            >
              Back to student check-in
            </button>
          )}
        </main>
      )}

      {authStatus === 'checkin' && CHECK_IN_TOKEN && (
        <main className="content auth-content">
          <section className="panel auth-panel" aria-labelledby="checkin-title">
            <p className="kicker">Class attendance</p>
            <h2 id="checkin-title">Check in to class</h2>
            {checkInResult ? (
              <div className="checkin-success" role="status">
                <strong>Attendance recorded</strong>
                <p>{checkInResult.student_name} · {checkInResult.course_name}</p>
                <span>{checkInResult.session_title}</span>
                <button className="secondary-button" onClick={signOutStudent} type="button">
                  Change student
                </button>
              </div>
            ) : checkInLoading && signedInStudentId ? (
              <p className="subtitle" role="status">
                Recording attendance as {signedInStudentId}…
              </p>
            ) : (
              <>
                <p className="subtitle">
                  {signedInStudentId
                    ? `Not you? Enter the active enrolled student's ID. Scanning this QR again will use the ID saved in this browser.`
                    : 'Enter your student ID once. After this check-in, scanning another class QR in this browser will record attendance automatically.'}
                  {' '}Student IDs are not independently verified.
                </p>
                {checkInError && <p className="feedback error" role="alert">{checkInError}</p>}
                <form className="auth-form" onSubmit={submitStudentCheckIn}>
                  <label>
                    Student ID
                    <input
                      autoComplete="off"
                      minLength={3}
                      onChange={(event) => setCheckInStudentId(event.target.value)}
                      required
                      value={checkInStudentId}
                    />
                  </label>
                  <button className="primary-button" disabled={checkInLoading} type="submit">
                    {checkInLoading ? 'Recording…' : 'Record attendance'}
                  </button>
                </form>
              </>
            )}
          </section>
        </main>
      )}

      {authStatus === 'authenticated' && !CHECK_IN_TOKEN && <main className="content">
        <section className="hero-card">
          <div>
            <p className="kicker">Student management</p>
            <h2>Keep your classroom roster accurate and ready.</h2>
            <p className="subtitle">
              Register students, update their details, and manage roster access from one place.
            </p>
          </div>
        </section>

        {error && <p className="feedback error" role="alert">{error}</p>}
        {notice && <p className="feedback success" role="status">{notice}</p>}

        <nav className="page-tabs" aria-label="Attendance management">
          <button
            aria-current={activePage === 'students' ? 'page' : undefined}
            className={activePage === 'students' ? 'page-tab active' : 'page-tab'}
            onClick={() => setActivePage('students')}
            type="button"
          >
            Students
          </button>
          <button
            aria-current={activePage === 'attendance' ? 'page' : undefined}
            className={activePage === 'attendance' ? 'page-tab active' : 'page-tab'}
            onClick={() => setActivePage('attendance')}
            type="button"
          >
            QR attendance
          </button>
          <button
            aria-current={activePage === 'reports' ? 'page' : undefined}
            className={activePage === 'reports' ? 'page-tab active' : 'page-tab'}
            onClick={() => setActivePage('reports')}
            type="button"
          >
            Reports
          </button>
        </nav>

        {activePage === 'attendance' ? (
          <section className="attendance-layout">
            <div className="attendance-column">
              {classrooms.length === 0 && (
                <section className="panel form-panel" aria-labelledby="classroom-title">
                  <p className="kicker">One-time setup</p>
                  <h3 id="classroom-title">Create your first classroom</h3>
                  <form className="student-form" onSubmit={createClassroom}>
                    <label>
                      Course code
                      <input maxLength={50} minLength={2} onChange={(event) => setClassroomForm((current) => ({ ...current, course_code: event.target.value }))} required value={classroomForm.course_code} />
                    </label>
                    <label>
                      Course name
                      <input maxLength={150} minLength={2} onChange={(event) => setClassroomForm((current) => ({ ...current, course_name: event.target.value }))} required value={classroomForm.course_name} />
                    </label>
                    <label>
                      Section <span className="optional-label">Optional</span>
                      <input maxLength={50} onChange={(event) => setClassroomForm((current) => ({ ...current, section: event.target.value }))} value={classroomForm.section} />
                    </label>
                    <label>
                      Academic year <span className="optional-label">Optional</span>
                      <input maxLength={30} onChange={(event) => setClassroomForm((current) => ({ ...current, academic_year: event.target.value }))} value={classroomForm.academic_year} />
                    </label>
                    <div className="form-actions">
                      <button className="primary-button" disabled={saving} type="submit">
                        {saving ? 'Saving…' : 'Create classroom'}
                      </button>
                    </div>
                  </form>
                </section>
              )}

              {classrooms.length > 0 && (
                <section className="panel form-panel" aria-labelledby="enrollment-title">
                  <div className="section-heading">
                    <div>
                      <p className="kicker">Class roster</p>
                      <h3 id="enrollment-title">Manage enrollment</h3>
                    </div>
                  </div>
                  <label className="enrollment-course">
                    Classroom
                    <select
                      onChange={(event) => {
                        setEnrollmentClassroomId(event.target.value);
                        setSessionForm((current) => ({
                          ...current,
                          classroom_id: event.target.value,
                        }));
                      }}
                      value={enrollmentClassroomId}
                    >
                      {classrooms.map((classroom) => (
                        <option key={classroom.id} value={classroom.id}>
                          {classroom.course_code} · {classroom.course_name}
                          {classroom.section ? ` (${classroom.section})` : ''}
                        </option>
                      ))}
                    </select>
                  </label>
                  <p className="enrollment-help">
                    Enrolled students are included in the session roster. Students without a check-in
                    are marked absent when you close or the session expires.
                  </p>
                  {enrollmentLoading ? (
                    <p className="empty-state" role="status">Loading classroom roster…</p>
                  ) : enrollmentStudents.length === 0 ? (
                    <p className="empty-state">
                      No students registered yet. Add students on the Students tab before enrolling them.
                    </p>
                  ) : (
                    <ul className="enrollment-list">
                      {enrollmentStudents.map((student) => {
                        const isEnrolled = enrolledStudentPks.has(student.id);
                        return (
                          <li key={student.id}>
                            <span>
                              <strong>{student.full_name}</strong>
                              <small>{student.student_id}{student.is_active ? '' : ' · inactive'}</small>
                            </span>
                            <button
                              className={isEnrolled ? 'text-button unenroll-button' : 'secondary-button'}
                              disabled={!student.is_active && !isEnrolled}
                              onClick={() => toggleEnrollment(student)}
                              type="button"
                            >
                              {isEnrolled ? 'Remove' : student.is_active ? 'Enroll' : 'Inactive'}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </section>
              )}

              {classrooms.length > 0 && !selectedSession && (
                <section className="panel form-panel" aria-labelledby="session-title">
                  <p className="kicker">New session</p>
                  <h3 id="session-title">Start QR attendance</h3>
                  <form className="session-form" onSubmit={createAttendanceSession}>
                    <label>
                      Classroom
                      <select
                        onChange={(event) => {
                          setEnrollmentClassroomId(event.target.value);
                          setSessionForm((current) => ({
                            ...current,
                            classroom_id: event.target.value,
                          }));
                        }}
                        required
                        value={sessionForm.classroom_id}
                      >
                        {classrooms.map((classroom) => (
                          <option key={classroom.id} value={classroom.id}>
                            {classroom.course_code} · {classroom.course_name}{classroom.section ? ` (${classroom.section})` : ''}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Session title
                      <input maxLength={150} minLength={2} onChange={(event) => setSessionForm((current) => ({ ...current, title: event.target.value }))} placeholder="e.g. Lecture 4" required value={sessionForm.title} />
                    </label>
                    <label>
                      QR active for
                      <select
                        onChange={(event) => setSessionForm((current) => ({ ...current, duration_minutes: Number(event.target.value) }))}
                        value={sessionForm.duration_minutes}
                      >
                        <option value={30}>30 minutes</option>
                        <option value={60}>1 hour</option>
                        <option value={90}>90 minutes</option>
                        <option value={120}>2 hours</option>
                        <option value={180}>3 hours</option>
                        <option value={360}>6 hours</option>
                      </select>
                    </label>
                    {selectedClassEnrolledCount === 0 && (
                      <p className="enrollment-warning">
                        Enroll at least one active student above before starting this session.
                      </p>
                    )}
                    <button
                      className="primary-button"
                      disabled={
                        saving
                        || enrollmentLoading
                        || selectedClassEnrolledCount === 0
                        || enrollmentClassroomId !== sessionForm.classroom_id
                      }
                      type="submit"
                    >
                      {saving ? 'Starting…' : 'Start session'}
                    </button>
                  </form>
                </section>
              )}

              {sessions.length > 0 && (
                <section className="panel form-panel">
                  <div className="section-heading">
                    <div>
                      <p className="kicker">History</p>
                      <h3>Attendance sessions</h3>
                    </div>
                  </div>
                  <div className="session-list">
                    {sessions.map((session) => (
                      <button
                        className="session-list-item"
                        key={session.id}
                        onClick={() => showSession(session.id)}
                        type="button"
                      >
                        <span>
                          <strong>{session.title}</strong>
                          <small>{session.classroom_name} · {session.session_date}</small>
                        </span>
                        <span className={`status-badge ${session.status === 'active' ? 'active' : 'inactive'}`}>
                          {session.status === 'active' ? 'Live' : 'Closed'} · {session.present_count}
                        </span>
                      </button>
                    ))}
                  </div>
                </section>
              )}
            </div>

            {selectedSession && (
              <section className="panel active-session-panel" aria-labelledby="live-session-title">
                <div className="section-heading">
                  <div>
                    <p className="kicker">{selectedSession.status === 'active' ? 'Live session' : 'Session details'}</p>
                    <h3 id="live-session-title">{selectedSession.title}</h3>
                    <p className="secondary-text">{selectedSession.classroom_name}</p>
                  </div>
                  <div className="section-actions">
                    <button
                      className="secondary-button"
                      onClick={() => {
                        setSelectedSession(null);
                        setAttendanceRecords([]);
                      }}
                      type="button"
                    >
                      New session
                    </button>
                    {selectedSession.status === 'active' && (
                      <button className="secondary-button" disabled={saving} onClick={closeAttendanceSession} type="button">
                        Close session
                      </button>
                    )}
                  </div>
                </div>
                {selectedSession.qr_image ? (
                  <div className="session-qr">
                    <img alt="QR code students scan to open class check-in" src={selectedSession.qr_image} />
                    <p>Students who saved their ID on this phone are checked in automatically when they scan.</p>
                    <small>The code expires at the session end time or when you close the session.</small>
                  </div>
                ) : (
                  <p className="empty-state">This session is closed. Its QR code is no longer valid.</p>
                )}
                <div className="attendance-summary">
                  <strong>{attendanceRecords.length}</strong>
                  <span>students checked in</span>
                </div>
                {attendanceRecords.length > 0 && (
                  <ul className="attendance-record-list">
                    {attendanceRecords.map((record) => (
                      <li key={record.student_id}>
                        <span><strong>{record.full_name}</strong><small>{record.student_id}</small></span>
                        <time>{new Date(record.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}
          </section>
        ) : activePage === 'reports' ? (
          <section className="panel report-panel" aria-labelledby="report-title">
            <div className="section-heading">
              <div>
                <p className="kicker">Attendance history</p>
                <h3 id="report-title">Attendance report</h3>
                <p className="secondary-text">
                  Shows recorded attendance entries only; students without a record are not marked absent.
                </p>
              </div>
              <button
                className="primary-button"
                disabled={reportLoading}
                onClick={exportAttendanceReport}
                type="button"
              >
                Export CSV
              </button>
            </div>
            <form
              className="report-filters"
              onSubmit={(event) => {
                event.preventDefault();
                setError('');
                setReportFilters(reportDraft);
              }}
            >
              <label>
                Course
                <select
                  onChange={(event) => setReportDraft((current) => ({
                    ...current,
                    classroom_id: event.target.value,
                  }))}
                  value={reportDraft.classroom_id}
                >
                  <option value="">All courses</option>
                  {classrooms.map((classroom) => (
                    <option key={classroom.id} value={classroom.id}>
                      {classroom.course_code} · {classroom.course_name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                From
                <input
                  onChange={(event) => setReportDraft((current) => ({
                    ...current,
                    date_from: event.target.value,
                  }))}
                  type="date"
                  value={reportDraft.date_from}
                />
              </label>
              <label>
                To
                <input
                  onChange={(event) => setReportDraft((current) => ({
                    ...current,
                    date_to: event.target.value,
                  }))}
                  type="date"
                  value={reportDraft.date_to}
                />
              </label>
              <button className="secondary-button" type="submit">Apply filters</button>
            </form>
            <p className="report-result-count" role="status">
              {reportLoading ? 'Loading report…' : `${reportRows.length} recorded attendance ${reportRows.length === 1 ? 'entry' : 'entries'}`}
            </p>
            {!reportLoading && reportRows.length === 0 ? (
              <p className="empty-state">No attendance entries match these filters.</p>
            ) : reportRows.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Session date</th>
                      <th>Course</th>
                      <th>Session</th>
                      <th>Student</th>
                      <th>Status</th>
                      <th>Checked in (UTC)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportRows.map((row, index) => (
                      <tr key={`${row.session_id}-${row.student_id}-${index}`}>
                        <td>{row.session_date}</td>
                        <td>{row.course_code} · {row.course_name}</td>
                        <td>{row.session_title}</td>
                        <td>{row.full_name}<span className="secondary-text">{row.student_id}</span></td>
                        <td><span className={`status-badge ${row.status === 'present' ? 'active' : 'inactive'}`}>{row.status}</span></td>
                        <td>
                          {row.checked_in_at
                            ? new Date(`${row.checked_in_at}Z`).toLocaleString()
                            : row.status === 'absent' ? 'Not checked in' : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </section>
        ) : <>
        <section className="stats-grid" aria-label="Student summary">
          <article className="stat-card">
            <span>Students found</span>
            <strong>{students.length}</strong>
          </article>
          <article className="stat-card">
            <span>Active students</span>
            <strong>{activeCount}</strong>
          </article>
          <article className="stat-card">
            <span>Inactive students</span>
            <strong>{students.length - activeCount}</strong>
          </article>
        </section>

        {formOpen && (
          <section className="panel form-panel" aria-labelledby="student-form-title">
            <div className="section-heading">
              <div>
                <p className="kicker">{editingId ? 'Edit record' : 'New record'}</p>
                <h3 id="student-form-title">{editingId ? 'Update student' : 'Register a student'}</h3>
              </div>
              <button className="secondary-button" onClick={closeForm} type="button">
                Cancel
              </button>
            </div>
            <form className="student-form" onSubmit={saveStudent}>
              <label>
                Student ID
                <input
                  autoComplete="off"
                  maxLength={50}
                  minLength={3}
                  name="student_id"
                  onChange={updateForm}
                  required
                  value={form.student_id}
                />
              </label>
              <label>
                Full name
                <input
                  autoComplete="name"
                  maxLength={150}
                  minLength={2}
                  name="full_name"
                  onChange={updateForm}
                  required
                  value={form.full_name}
                />
              </label>
              <label>
                Email <span className="optional-label">Optional</span>
                <input
                  autoComplete="email"
                  maxLength={150}
                  name="email"
                  onChange={updateForm}
                  type="email"
                  value={form.email}
                />
              </label>
              <label>
                Phone <span className="optional-label">Optional</span>
                <input
                  autoComplete="tel"
                  maxLength={30}
                  name="phone"
                  onChange={updateForm}
                  value={form.phone}
                />
              </label>
              <label>
                Program <span className="optional-label">Optional</span>
                <input
                  maxLength={100}
                  name="program"
                  onChange={updateForm}
                  value={form.program}
                />
              </label>
              <label>
                Year <span className="optional-label">Optional</span>
                <input
                  maxLength={30}
                  name="year"
                  onChange={updateForm}
                  value={form.year}
                />
              </label>
              <div className="form-actions">
                <button className="primary-button" disabled={saving} type="submit">
                  {saving ? 'Saving…' : editingId ? 'Save changes' : 'Register student'}
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="panel roster-panel" aria-labelledby="roster-title">
          <div className="section-heading roster-heading">
            <div>
              <p className="kicker">Directory</p>
              <h3 id="roster-title">Student roster</h3>
            </div>
            <label className="search-field">
              <span>Search students</span>
              <input
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Name, student ID, email, or program"
                type="search"
                value={search}
              />
            </label>
          </div>

          {loading ? (
            <p className="empty-state" role="status">Loading student roster…</p>
          ) : students.length === 0 ? (
            <div className="empty-state">
              <strong>{search ? 'No matching students' : 'No students registered yet'}</strong>
              <p>{search ? 'Try a different search.' : 'Register a student to start your classroom roster.'}</p>
              {!search && (
                <button className="primary-button" onClick={startRegistration} type="button">
                  Register first student
                </button>
              )}
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Student</th>
                    <th scope="col">Program / year</th>
                    <th scope="col">Contact</th>
                    <th scope="col">Status</th>
                    <th scope="col"><span className="visually-hidden">Actions</span></th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((student) => (
                    <tr key={student.id}>
                      <td>
                        <strong>{student.full_name}</strong>
                        <span className="secondary-text">{student.student_id}</span>
                      </td>
                      <td>
                        {student.program || '—'}
                        <span className="secondary-text">{student.year || 'Year not set'}</span>
                      </td>
                      <td>
                        {student.email || '—'}
                        <span className="secondary-text">{student.phone || 'No phone'}</span>
                      </td>
                      <td>
                        <span className={`status-badge ${student.is_active ? 'active' : 'inactive'}`}>
                          {student.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="row-actions">
                        <button
                          aria-label={`Edit ${student.full_name}`}
                          className="text-button"
                          onClick={() => startEditing(student)}
                          type="button"
                        >
                          Edit
                        </button>
                        <button
                          aria-label={`${student.is_active ? 'Deactivate' : 'Activate'} ${student.full_name}`}
                          className="text-button"
                          onClick={() => toggleStudentStatus(student)}
                          type="button"
                        >
                          {student.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        </>
        }
      </main>}
    </div>
  );
}

export default App;
