"""All SQLite work for Peer Tutor Hub is inside the Database class."""
import sqlite3
from datetime import date

BOOKING_SQL = """
    SELECT b.id, b.slot_id, b.student_id, s.tutor_id, s.slot_date, s.start_time, s.end_time,
           b.topic, b.status, b.notes,
           st.name AS student_name, t.name AS tutor_name, t.subject AS subject
    FROM bookings b
    JOIN slots s ON s.id = b.slot_id
    JOIN users st ON st.id = b.student_id
    JOIN users t ON t.id = s.tutor_id"""


class Database:
    """Every method opens its own connection, saves changes and closes it."""

    def __init__(self, path):
        self.path = path
        self.create_tables()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def query(self, sql, params=()):
        """Run a SELECT and return a list of dictionaries."""
        conn = self._connect()
        try:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    def execute(self, sql, params=()):
        """Run INSERT / UPDATE / DELETE. Returns (new id, rows changed)."""
        conn = self._connect()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.lastrowid, cursor.rowcount
        finally:
            conn.close()

    def create_tables(self):
        """Creates the tables only if they are missing, so old records are kept."""
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    subject TEXT NOT NULL DEFAULT '',
                    hourly_rate REAL NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tutor_id INTEGER NOT NULL,
                    slot_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open'
                );
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slot_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    notes TEXT NOT NULL DEFAULT ''
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    # ---------- users ----------
    def add_user(self, name, username, password_hash, role, subject, rate):
        return self.execute(
            "INSERT INTO users (name, username, password_hash, role, subject, hourly_rate) "
            "VALUES (?, ?, ?, ?, ?, ?)", (name, username, password_hash, role, subject, rate))[0]

    def get_login(self, username):
        rows = self.query("SELECT * FROM users WHERE username = ?", (username,))
        return rows[0] if rows else None

    def get_user(self, user_id):
        rows = self.query("SELECT id, name, username, role, subject, hourly_rate FROM users WHERE id = ?",
                          (user_id,))
        return rows[0] if rows else None

    def update_profile(self, user_id, name, subject, rate):
        self.execute("UPDATE users SET name = ?, subject = ?, hourly_rate = ? WHERE id = ?",
                     (name, subject, rate, user_id))

    def list_tutors(self, subject, max_rate):
        return self.query(
            """SELECT u.id, u.name, u.subject, u.hourly_rate,
                      (SELECT COUNT(*) FROM slots
                        WHERE tutor_id = u.id AND status = 'open' AND slot_date >= ?) AS open_slots
               FROM users u
               WHERE u.role = 'tutor' AND LOWER(u.subject) LIKE ? AND u.hourly_rate <= ?
               ORDER BY u.name""",
            (date.today().isoformat(), f"%{subject.lower()}%", max_rate))

    # ---------- slots ----------
    def list_slots(self, tutor_id, status=""):
        sql = "SELECT * FROM slots WHERE tutor_id = ?"
        params = [tutor_id]
        if status:
            sql += " AND status = ? AND slot_date >= ?"
            params += [status, date.today().isoformat()]
        sql += " ORDER BY slot_date, start_time"
        return self.query(sql, params)

    def get_slot(self, slot_id):
        rows = self.query("SELECT * FROM slots WHERE id = ?", (slot_id,))
        return rows[0] if rows else None

    def add_slot(self, tutor_id, day, start, end):
        return self.execute("INSERT INTO slots (tutor_id, slot_date, start_time, end_time) VALUES (?, ?, ?, ?)",
                            (tutor_id, day, start, end))[0]

    def delete_slot(self, slot_id):
        self.execute("DELETE FROM slots WHERE id = ?", (slot_id,))

    def set_slot_status(self, slot_id, status):
        self.execute("UPDATE slots SET status = ? WHERE id = ?", (status, slot_id))

    # ---------- bookings ----------
    def add_booking(self, student_id, slot_id, topic):
        return self.execute("INSERT INTO bookings (slot_id, student_id, topic) VALUES (?, ?, ?)",
                            (slot_id, student_id, topic))[0]

    def get_booking(self, booking_id):
        rows = self.query(BOOKING_SQL + " WHERE b.id = ?", (booking_id,))
        return rows[0] if rows else None

    def list_bookings(self, user_id, role, status=""):
        column = "b.student_id" if role == "student" else "s.tutor_id"  # chosen by us, not typed by the user
        sql = BOOKING_SQL + f" WHERE {column} = ?"
        params = [user_id]
        if status:
            sql += " AND b.status = ?"
            params.append(status)
        return self.query(sql + " ORDER BY s.slot_date, s.start_time", params)

    def set_status(self, booking_id, status, notes=""):
        self.execute("UPDATE bookings SET status = ?, notes = ? WHERE id = ?", (status, notes, booking_id))

    def report_rows(self):
        return self.query(BOOKING_SQL + " ORDER BY b.id")
