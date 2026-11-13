import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
from app import create_app  # noqa: E402

TOMORROW = (date.today() + timedelta(days=1)).isoformat()


class HubTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.c = create_app(self.tmp.name).test_client()
        self.tutor = self.register("tutor", "sara", subject="Python", hourly_rate="60")
        self.student = self.register("student", "ali")

    def tearDown(self):
        os.unlink(self.tmp.name)

    def register(self, role, username, **extra):
        data = {"name": username.title(), "username": username, "password": "1234", "role": role, **extra}
        return self.c.post("/register", data=data).get_json()["user"]["id"]

    def post(self, path, uid, **data):
        return self.c.post(path, data={"user_id": uid, **data})

    def add_slot(self, start="16:00", end="17:00"):
        self.post("/slots/add", self.tutor, slot_date=TOMORROW, start_time=start, end_time=end)
        return self.c.get(f"/slots?tutor_id={self.tutor}").get_json()["slots"][-1]["id"]

    def book(self, slot_id):
        return self.post("/bookings/add", self.student, slot_id=slot_id, topic="Loops")

    def first_booking(self):
        return self.c.get(f"/bookings?user_id={self.student}&role=student").get_json()["bookings"][0]["id"]

    def test_register_and_login(self):
        dup = self.c.post("/register", data={"name": "X", "username": "sara", "password": "1234", "role": "student"})
        self.assertEqual(dup.status_code, 400)
        no_subject = {"name": "T", "username": "tt1", "password": "1234", "role": "tutor", "hourly_rate": "10"}
        self.assertEqual(self.c.post("/register", data=no_subject).status_code, 400)
        self.assertEqual(self.c.post("/login", data={"username": "sara", "password": "bad"}).status_code, 401)
        good = self.c.post("/login", data={"username": "sara", "password": "1234"})
        self.assertEqual(good.status_code, 200)
        self.assertNotIn("password_hash", good.get_json()["user"])

    def test_slot_validation(self):
        bad = [dict(slot_date="2020-01-01", start_time="16:00", end_time="17:00"),
               dict(slot_date="not-a-date", start_time="16:00", end_time="17:00"),
               dict(slot_date=TOMORROW, start_time="9am", end_time="17:00"),
               dict(slot_date=TOMORROW, start_time="17:00", end_time="16:00")]
        for data in bad:
            self.assertEqual(self.post("/slots/add", self.tutor, **data).status_code, 400)

    def test_booking_flow(self):
        slot = self.add_slot()
        self.assertEqual(self.book(slot).status_code, 200)
        self.assertEqual(self.book(slot).status_code, 400)  # already booked
        booking = self.first_booking()
        self.assertEqual(self.post(f"/bookings/{booking}/approve", self.tutor).status_code, 200)
        self.assertEqual(self.post(f"/bookings/{booking}/approve", self.tutor).status_code, 400)
        self.assertEqual(self.post(f"/bookings/{booking}/complete", self.tutor, notes="Good job").status_code, 200)
        row = self.c.get(f"/bookings?user_id={self.student}&role=student&status=completed").get_json()["bookings"][0]
        self.assertEqual(row["notes"], "Good job")

    def test_reject_and_cancel_reopen_the_slot(self):
        slot = self.add_slot()
        self.book(slot)
        booking = self.first_booking()
        self.assertEqual(self.post(f"/bookings/{booking}/reject", self.tutor).status_code, 200)
        open_slots = self.c.get(f"/slots?tutor_id={self.tutor}&status=open").get_json()["slots"]
        self.assertEqual(len(open_slots), 1)
        self.book(slot)
        second = self.c.get(f"/bookings?user_id={self.student}&role=student&status=pending").get_json()["bookings"][0]["id"]
        self.assertEqual(self.post(f"/bookings/{second}/cancel", self.student).status_code, 200)
        self.assertEqual(len(self.c.get(f"/slots?tutor_id={self.tutor}&status=open").get_json()["slots"]), 1)

    def test_delete_slot(self):
        slot = self.add_slot()
        self.book(slot)
        self.assertEqual(self.post(f"/slots/{slot}/delete", self.tutor).status_code, 400)  # booked
        free = self.add_slot("18:00", "19:00")
        self.assertEqual(self.post(f"/slots/{free}/delete", self.tutor).status_code, 200)

    def test_unknown_records_and_owners(self):
        other = self.register("tutor", "omar", subject="Math", hourly_rate="40")
        slot = self.add_slot()
        self.book(slot)
        booking = self.first_booking()
        self.assertEqual(self.post("/bookings/999/approve", self.tutor).status_code, 404)
        self.assertEqual(self.post("/bookings/999/cancel", self.student).status_code, 404)
        self.assertEqual(self.post("/slots/999/delete", self.tutor).status_code, 404)
        self.assertEqual(self.post("/bookings/add", self.student, slot_id="999", topic="x").status_code, 404)
        self.assertEqual(self.post(f"/bookings/{booking}/approve", other).status_code, 404)  # not their booking
        self.assertEqual(self.post(f"/slots/{slot}/delete", other).status_code, 404)

    def test_filters_and_empty_lists(self):
        def count(query):
            return len(self.c.get("/tutors" + query).get_json()["tutors"])
        self.assertEqual(count("?subject=pyth"), 1)
        self.assertEqual(count("?subject=chem"), 0)
        self.assertEqual(count("?max_rate=10"), 0)
        self.assertEqual(self.c.get("/tutors?max_rate=abc").status_code, 400)
        self.assertEqual(self.c.get(f"/bookings?user_id={self.student}&role=student").get_json()["bookings"], [])
        self.assertEqual(self.c.get(f"/slots?tutor_id={self.tutor}").get_json()["slots"], [])

    def test_missing_topic_and_profile_and_report(self):
        slot = self.add_slot()
        self.assertEqual(self.post("/bookings/add", self.student, slot_id=slot, topic=" ").status_code, 400)
        edit = self.post("/profile", self.tutor, name="Sara A", subject="Flask", hourly_rate="70")
        self.assertEqual(edit.get_json()["user"]["subject"], "Flask")
        self.assertEqual(self.post("/profile", self.tutor, name="", subject="x", hourly_rate="1").status_code, 400)
        self.book(slot)
        rows = self.c.get("/report-data").get_json()["bookings"]
        self.assertEqual(rows[0]["tutor_name"], "Sara A")


if __name__ == "__main__":
    unittest.main()
