"""Command-line interface: ``python -m messtime <command>``."""

import argparse
import getpass
import sys
from pathlib import Path

from . import auth, db, qr


def _require_admin(conn) -> None:
    if not auth.has_password(conn):
        print("No admin password set yet. Run: python -m messtime set-password")
        sys.exit(1)
    for _ in range(3):
        if auth.check_password(conn, getpass.getpass("Admin password: ")):
            return
        print("Incorrect password.")
    sys.exit(1)


def cmd_set_password(args) -> None:
    with db.connect(args.db) as conn:
        if auth.has_password(conn):
            _require_admin(conn)
        password = getpass.getpass("New admin password: ")
        if password != getpass.getpass("Confirm password: "):
            sys.exit("Passwords don't match.")
        try:
            auth.set_password(conn, password)
        except ValueError as e:
            sys.exit(str(e))
    print("Admin password saved.")


def cmd_add_student(args) -> None:
    student = db.Student(args.student_id, args.name, args.phone or "", args.room or "")
    with db.connect(args.db) as conn:
        _require_admin(conn)
        try:
            db.add_student(conn, student)
        except ValueError as e:
            sys.exit(str(e))
    path = qr.make_qr(student.student_id, args.qr_dir)
    print(f"Added {student.name} ({student.student_id}). QR code saved to {path}")


def cmd_students(args) -> None:
    with db.connect(args.db) as conn:
        students = db.list_students(conn)
    if not students:
        print("No students registered.")
        return
    print(f"{'ID':<12} {'Name':<25} {'Room':<8} Phone")
    for s in students:
        print(f"{s.student_id:<12} {s.name:<25} {s.room:<8} {s.phone}")


def cmd_scan(args) -> None:
    with db.connect(args.db) as conn:

        def on_code(code: str) -> str:
            try:
                student, meal = db.mark_attendance(conn, code)
            except db.AttendanceError as e:
                message = str(e)
            else:
                conn.commit()
                message = f"Marked {student.name} for {meal}"
            print(message)
            return message

        qr.scan(on_code, camera=args.camera)


def cmd_records(args) -> None:
    with db.connect(args.db) as conn:
        rows = db.attendance_records(conn, on=args.date)
    if not rows:
        print("No attendance records.")
        return
    print(f"{'Date':<11} {'Meal':<10} {'Time':<9} {'ID':<12} Name")
    for r in rows:
        print(f"{r['meal_date']:<11} {r['meal']:<10} {r['marked_at'][11:]:<9} {r['student_id']:<12} {r['name']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="messtime", description="QR code mess attendance for hostels.")
    parser.add_argument("--db", type=Path, default=db.DEFAULT_DB_PATH, help="database file (default: %(default)s)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("set-password", help="set or change the admin password")
    p.set_defaults(func=cmd_set_password)

    p = sub.add_parser("add-student", help="register a student and generate their QR code (admin)")
    p.add_argument("student_id")
    p.add_argument("name")
    p.add_argument("--phone")
    p.add_argument("--room")
    p.add_argument("--qr-dir", type=Path, default=qr.DEFAULT_QR_DIR)
    p.set_defaults(func=cmd_add_student)

    p = sub.add_parser("students", help="list registered students")
    p.set_defaults(func=cmd_students)

    p = sub.add_parser("scan", help="open the webcam and mark attendance from QR codes")
    p.add_argument("--camera", type=int, default=0, help="camera index (default: %(default)s)")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("records", help="show attendance records")
    p.add_argument("--date", help="only show this date (YYYY-MM-DD)")
    p.set_defaults(func=cmd_records)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)
