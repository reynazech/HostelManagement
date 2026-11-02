# MessTime – Hostel Mess Attendance

Students scan a personal QR code at the mess counter, and MessTime records which meal they ate.
Each student can be marked once per meal per day.

**Live site:** [messtime.reynazech.tech](https://messtime.reynazech.tech) (the login page from `web/`)

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m messtime set-password                       # first run: create the admin password
python -m messtime add-student S001 "Asha Rao" --room B-12 --phone 9999999999
python -m messtime students                           # list registered students
python -m messtime scan                               # open the webcam and mark attendance (q to quit)
python -m messtime records --date 2026-01-15          # view attendance
```

`add-student` saves the student's QR code to `qr_codes/<id>.png`. Print it or send it to them.

Meal windows (set in `messtime/db.py`):

| Meal      | Time          |
|-----------|---------------|
| Breakfast | 06:00 – 11:00 |
| Lunch     | 11:00 – 16:00 |
| Dinner    | 18:00 – 23:00 |

Data lives in `messtime.db` (SQLite). Use `--db path/to/file.db` to point somewhere else.

## Project layout

```
messtime/
  cli.py    command-line interface
  db.py     SQLite schema, students and attendance
  auth.py   hashed admin password
  qr.py     QR generation and webcam scanning
web/        login page (front end only, not wired to a backend yet)
tests/      pytest tests
```

## Deployment

The `web/` folder is served at https://messtime.reynazech.tech from the VPS. A small Caddy
container in `/docker/messtime` serves the files, and the main Caddy proxy (`/docker/todoapp`)
routes the subdomain to it and handles HTTPS. To publish changes to `web/`:

```bash
scp web/* root@reynazech.tech:/docker/messtime/site/
ssh root@reynazech.tech 'cp /docker/messtime/site/login.html /docker/messtime/site/index.html'
```

## Tests

```bash
pip install pytest
pytest
```
