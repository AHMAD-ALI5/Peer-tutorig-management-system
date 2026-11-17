"""Flask back end for Peer Tutor Hub (port 5050)."""
import os
from datetime import date, datetime

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from database import Database

DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tutors.db")


def ok(**data):
    return jsonify({"ok": True, **data})


def err(message, status):
    return jsonify({"ok": False, "error": message}), status


def clean_date(text):
    """Return 'YYYY-MM-DD' or None if the text is not a real date."""
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def clean_time(text):
    """Return 'HH:MM' or None if the text is not a real time."""
    try:
        return datetime.strptime(text.strip(), "%H:%M").strftime("%H:%M")
    except ValueError:
        return None


def get_user_id(source):
    try:
        return int(source.get("user_id", ""))
    except ValueError:
        return None


def check_tutor_fields(subject, rate_text):
    """Return (rate, error_message)."""
    if not subject:
        return None, "Tutors must enter a subject."
    try:
        rate = float(rate_text)
    except ValueError:
        return None, "Hourly rate must be a number."
    if rate < 0:
        return None, "Hourly rate cannot be negative."
    return rate, None


def create_app(db_path=DEFAULT_DB):
    app = Flask(__name__)
    db = Database(db_path)

    # ---------- accounts ----------
    @app.get("/")
    def home():
        return ok(message="Peer Tutor Hub API is running. Start the window with: python client/gui.py")

    @app.post("/register")
    def register():
        form = request.form
        name = form.get("name", "").strip()
        username = form.get("username", "").strip().lower()
        password = form.get("password", "")
        role = form.get("role", "")
        subject = form.get("subject", "").strip()
        if not name or not username or not password:
            return err("Name, username and password are required.", 400)
        if len(password) < 4:
            return err("Password must be at least 4 characters.", 400)
        if role not in ("student", "tutor"):
            return err("Choose Student or Tutor.", 400)
        rate = 0.0
        if role == "tutor":
            rate, problem = check_tutor_fields(subject, form.get("hourly_rate", ""))
            if problem:
                return err(problem, 400)
        else:
            subject = ""
        if db.get_login(username):
            return err("That username is already taken.", 400)
        user_id = db.add_user(name, username, generate_password_hash(password), role, subject, rate)
        return ok(message="Account created.", user=db.get_user(user_id))

    @app.post("/login")
    def login():
        row = db.get_login(request.form.get("username", "").strip().lower())
        if row is None or not check_password_hash(row["password_hash"], request.form.get("password", "")):
            return err("Wrong username or password.", 401)
        return ok(message="Logged in.", user=db.get_user(row["id"]))

    @app.post("/profile")
    def edit_profile():
        user = db.get_user(get_user_id(request.form) or 0)
        if user is None:
            return err("Account not found. Please log in again.", 404)
        name = request.form.get("name", "").strip()
        subject = request.form.get("subject", "").strip()
        rate, problem = check_tutor_fields(subject, request.form.get("hourly_rate", ""))
        if not name:
            return err("Name is required.", 400)
        if problem:
            return err(problem, 400)
        db.update_profile(user["id"], name, subject, rate)
        return ok(message="Profile saved.", user=db.get_user(user["id"]))

    # ---------- tutors and slots ----------
    @app.get("/tutors")
    def list_tutors():
        try:
            max_rate = float(request.args.get("max_rate") or 100000)
        except ValueError:
            return err("Maximum rate must be a number.", 400)
        return ok(tutors=db.list_tutors(request.args.get("subject", "").strip(), max_rate))

    @app.get("/slots")
    def list_slots():
        try:
            tutor_id = int(request.args.get("tutor_id", ""))
        except ValueError:
            return err("Choose a tutor first.", 400)
        if db.get_user(tutor_id) is None:
            return err("Tutor not found.", 404)
        return ok(slots=db.list_slots(tutor_id, request.args.get("status", "")))

    @app.post("/slots/add")
    def add_slot():
        user_id = get_user_id(request.form)
        if db.get_user(user_id or 0) is None:
            return err("Account not found. Please log in again.", 404)
        day = clean_date(request.form.get("slot_date", ""))
        start = clean_time(request.form.get("start_time", ""))
        end = clean_time(request.form.get("end_time", ""))
        if day is None:
            return err("Date must look like 2026-11-20.", 400)
        if day < date.today().isoformat():
            return err("The date cannot be in the past.", 400)
        if start is None or end is None:
            return err("Times must look like 16:00.", 400)
        if start >= end:
            return err("The end time must be after the start time.", 400)
        db.add_slot(user_id, day, start, end)
        return ok(message="Time slot added.")

    @app.post("/slots/<int:slot_id>/delete")
    def delete_slot(slot_id):
        slot = db.get_slot(slot_id)
        if slot is None or slot["tutor_id"] != get_user_id(request.form):
            return err("Slot not found. It may already be deleted.", 404)
        if slot["status"] == "booked":
            return err("This slot is booked. Reject or cancel the booking first.", 400)
        db.delete_slot(slot_id)
        return ok(message="Time slot deleted.")

    # ---------- bookings ----------
    @app.get("/bookings")
    def list_bookings():
        user_id = get_user_id(request.args)
        role = request.args.get("role", "")
        if user_id is None or role not in ("student", "tutor"):
            return err("Please log in first.", 400)
        return ok(bookings=db.list_bookings(user_id, role, request.args.get("status", "")))

    @app.post("/bookings/add")
    def add_booking():
        user_id = get_user_id(request.form)
        if db.get_user(user_id or 0) is None:
            return err("Account not found. Please log in again.", 404)
        try:
            slot_id = int(request.form.get("slot_id", ""))
        except ValueError:
            return err("Choose a time slot first.", 400)
        topic = request.form.get("topic", "").strip()
        if not topic:
            return err("Please write the topic you need help with.", 400)
        slot = db.get_slot(slot_id)
        if slot is None:
            return err("Time slot not found.", 404)
        if slot["status"] != "open":
            return err("Someone already booked that slot. Pick another one.", 400)
        db.add_booking(user_id, slot_id, topic)
        db.set_slot_status(slot_id, "booked")
        return ok(message="Request sent! The tutor will approve or reject it.")

    def change_booking(booking_id, owner, allowed, new_status, message):
        """Shared by approve / reject / complete / cancel.
        owner is 'tutor_id' or 'student_id': who is allowed to do this action."""
        booking = db.get_booking(booking_id)
        if booking is None or booking[owner] != get_user_id(request.form):
            return err("Booking not found.", 404)
        if booking["status"] not in allowed:
            return err(f"This booking is {booking['status']}, so you cannot do that.", 400)
        db.set_status(booking_id, new_status, request.form.get("notes", "").strip())
        if new_status in ("rejected", "cancelled"):
            db.set_slot_status(booking["slot_id"], "open")
        elif new_status == "completed":
            db.set_slot_status(booking["slot_id"], "completed")

    @app.post("/bookings/<int:booking_id>/approve")
    def approve(booking_id):
        return change_booking(booking_id, "tutor_id", ("pending",), "approved", "Booking approved.")

    @app.post("/bookings/<int:booking_id>/reject")
    def reject(booking_id):
        return change_booking(booking_id, "tutor_id", ("pending",), "rejected", "Booking rejected.")

    @app.post("/bookings/<int:booking_id>/complete")
    def complete(booking_id):
        return change_booking(booking_id, "tutor_id", ("approved",), "completed", "Session marked as completed.")

    @app.post("/bookings/<int:booking_id>/cancel")
    def cancel(booking_id):
        return change_booking(booking_id, "student_id", ("pending", "approved"), "cancelled", "Booking cancelled.")

    # ---------- used by report_helper.py ----------
    @app.get("/report-data")
    def report_data():
        return ok(bookings=db.report_rows())

    return app


if __name__ == "__main__":
    create_app().run(port=5050)
