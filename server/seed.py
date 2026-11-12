"""Optional demo data. Run once:  python server/seed.py   (all demo passwords: 1234)"""
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import DEFAULT_DB
from database import Database

db = Database(DEFAULT_DB)
if db.query("SELECT 1 FROM users"):
    raise SystemExit("Database already has users - nothing added.")

password = generate_password_hash("1234")
tutors = [("Sara Alharbi", "sara", "Python", 60), ("Omar Khan", "omar", "Mathematics", 45),
          ("Lina Ahmed", "lina", "Physics", 50), ("Yusuf Ali", "yusuf", "Databases", 55)]
slot_ids = {}
for name, username, subject, rate in tutors:
    tutor_id = db.add_user(name, username, password, "tutor", subject, rate)
    slot_ids[username] = []
    for days in (1, 2, 3):
        day = (date.today() + timedelta(days=days)).isoformat()
        slot_ids[username].append(db.add_slot(tutor_id, day, "16:00", "17:00"))
        slot_ids[username].append(db.add_slot(tutor_id, day, "17:00", "18:00"))

ali = db.add_user("Ali Hassan", "ali", password, "student", "", 0)
db.add_user("Noor Saleh", "noor", password, "student", "", 0)

# one pending request so the tutor dashboard is not empty in the demo
db.add_booking(ali, slot_ids["sara"][0], "Help with for loops")
db.set_slot_status(slot_ids["sara"][0], "booked")
print("Demo data added. Tutors: sara, omar, lina, yusuf. Students: ali, noor. Password: 1234")
