# Peer Tutor Hub

A peer tutoring app with a student dashboard and a tutor dashboard.
**Tkinter** (window) <-> **Flask** (API, port 5050) <-> **SQLite** (data).

## What it does
**Students:** search tutors by subject and maximum rate, see a tutor's open time slots, book a slot
with a topic, follow their bookings (pending / approved / rejected / completed / cancelled),
cancel a booking, and see their confirmed sessions in a timetable.

**Tutors:** add and delete time slots, approve or reject booking requests, mark sessions
completed with short notes, see all their sessions, and edit their profile.

Extra feature: when a booking is rejected or cancelled, its time slot becomes open again automatically.

## Install
```
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Run
1. Start Flask (tables are created automatically, old records are kept): `python server/app.py`
2. Optional demo data (once): `python server/seed.py`
   Demo logins, password `1234`: tutors `sara`, `omar`, `lina`, `yusuf`; students `ali`, `noor`.
3. In a second terminal: `python client/gui.py`
4. Report helper (Flask running): `python report_helper.py` -> creates `tutor_report.txt`

## Database tables
`users` (id, name, username, password_hash, role, subject, hourly_rate),
`slots` (id, tutor_id, slot_date, start_time, end_time, status open/booked),
`bookings` (id, slot_id, student_id, topic, status, notes).

## Routes
| Method | Route | Purpose |
|---|---|---|
| POST | /register, /login | accounts |
| POST | /profile | edit tutor profile |
| GET | /tutors?subject=&max_rate= | search tutors |
| GET | /slots?tutor_id=&status= | list slots |
| POST | /slots/add, /slots/<id>/delete | add / delete slot |
| GET | /bookings?role=&status= | my bookings |
| POST | /bookings/add | student books a slot |
| POST | /bookings/<id>/approve, reject, complete | tutor actions |
| POST | /bookings/<id>/cancel | student cancels |
| GET | /report-data | all bookings as JSON (report helper) |

Errors are JSON: 400 invalid input, 404 unknown record, 401 wrong login.

## Course topics
| Topic | Evidence |
|---|---|
| Python and collections | `server/app.py` `clean_date`, `clean_time`, `check_tutor_fields`; lists of dictionaries in every route |
| Exceptions | `client/api_client.py` `request` (HTTPError, URLError, timeout); `server/app.py` `clean_date` (ValueError); `report_helper.py` |
| Classes | `server/database.py` `Database`; `client/gui.py` `App`, `LoginFrame`; `client/student_view.py` `StudentView`; `client/tutor_view.py` `TutorView`; `client/widgets.py` `Table` |
| SQLite | `server/database.py` - every query uses `?` placeholders |
| Threads and files | `report_helper.py` `main` (Thread, start, join) and `write_report` (`with open`, UTF-8) |
| Tkinter | `client/*.py` labels, text boxes, buttons, tables, tabs, confirmation dialogs |
| Client and server | Click "Book selected slot" -> `StudentView.book_slot` -> `App.api` -> `request("/bookings/add")` POST -> Flask `add_booking` checks and saves -> JSON reply -> message in the window |
| Flask | `server/app.py` routes, input checks, JSON replies |

Add / view / edit / delete in the window: bookings (add, view, cancel with confirmation),
slots (add, view, delete with confirmation), tutor profile (edit).

## Tests
Automated: `python -m unittest tests/test_server.py -v` (8 tests).

Manual checklist (write your own results):
- [ ] Add, view, edit, delete changes only the chosen record
- [ ] Stop and restart Flask and the window: records remain
- [ ] Missing input / invalid value / empty list show clear messages
- [ ] Unknown ID: open two windows, cancel a booking in one, approve it in the other -> "Booking not found."
- [ ] Stop Flask -> action shows a connection error; start Flask -> try again without restarting the window
- [ ] Report helper writes a correct tutor_report.txt

## Limitations
After login the window sends the user's id with each request (no tokens). This is enough for a local course project.

## Credits
List outside code, assets and AI assistance here, following the course integrity policy.
