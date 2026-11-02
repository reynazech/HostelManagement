from datetime import datetime

import pytest

from messtime import auth, db, qr

LUNCHTIME = datetime(2026, 1, 15, 12, 30)


@pytest.fixture
def conn(tmp_path):
    with db.connect(tmp_path / "test.db") as conn:
        db.add_student(conn, db.Student("S001", "Asha Rao", "9999999999", "B-12"))
        yield conn


def test_duplicate_student_rejected(conn):
    with pytest.raises(ValueError):
        db.add_student(conn, db.Student("S001", "Someone Else"))


def test_mark_attendance(conn):
    student, meal = db.mark_attendance(conn, "S001", LUNCHTIME)
    assert student.name == "Asha Rao"
    assert meal == "lunch"
    assert len(db.attendance_records(conn, on="2026-01-15")) == 1


def test_attendance_only_once_per_meal(conn):
    db.mark_attendance(conn, "S001", LUNCHTIME)
    with pytest.raises(db.AttendanceError, match="already"):
        db.mark_attendance(conn, "S001", LUNCHTIME.replace(hour=14))
    # A different meal the same day is fine.
    db.mark_attendance(conn, "S001", LUNCHTIME.replace(hour=19))


def test_unknown_student(conn):
    with pytest.raises(db.AttendanceError, match="Unknown"):
        db.mark_attendance(conn, "NOPE", LUNCHTIME)


def test_outside_meal_hours(conn):
    with pytest.raises(db.AttendanceError, match="No meal"):
        db.mark_attendance(conn, "S001", LUNCHTIME.replace(hour=3))


def test_admin_password(conn):
    assert not auth.check_password(conn, "anything")
    auth.set_password(conn, "secret123")
    assert auth.check_password(conn, "secret123")
    assert not auth.check_password(conn, "wrong")
    assert "secret123" not in db.get_setting(conn, "admin_password")


def test_qr_round_trip(tmp_path):
    cv2 = pytest.importorskip("cv2")
    path = qr.make_qr("S001", tmp_path)
    decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(str(path)))
    assert decoded == "S001"
