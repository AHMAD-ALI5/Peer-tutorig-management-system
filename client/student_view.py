"""Student dashboard: find tutors, book a slot, follow bookings, see confirmed sessions."""
import tkinter as tk
from tkinter import messagebox, ttk

from widgets import Table


class StudentView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.tutor = None  # the tutor selected in the table
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=14)
        self.find_tab = ttk.Frame(self.notebook, padding=14)
        self.bookings_tab = ttk.Frame(self.notebook, padding=14)
        self.timetable_tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.find_tab, text="Find a Tutor")
        self.notebook.add(self.bookings_tab, text="My Bookings")
        self.notebook.add(self.timetable_tab, text="Timetable")
        self.build_find()
        self.build_bookings()
        self.build_timetable()
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.search_tutors()

    def on_tab_change(self, event):
        index = self.notebook.index("current")
        if index == 1:
            self.load_bookings()
        elif index == 2:
            self.load_timetable()

    # ---------- Find a Tutor ----------
    def build_find(self):
        bar = ttk.Frame(self.find_tab)
        bar.pack(fill="x", pady=(0, 10))
        self.f_subject = tk.StringVar()
        self.f_rate = tk.StringVar()
        ttk.Label(bar, text="Subject").grid(row=0, column=0, sticky="w")
        ttk.Entry(bar, textvariable=self.f_subject, width=20).grid(row=1, column=0, padx=(0, 14))
        ttk.Label(bar, text="Max rate (SAR/hr)").grid(row=0, column=1, sticky="w")
        ttk.Entry(bar, textvariable=self.f_rate, width=12).grid(row=1, column=1, padx=(0, 14))
        ttk.Button(bar, text="Search", style="Accent.TButton", command=self.search_tutors).grid(row=1, column=2)
        ttk.Button(bar, text="Clear", style="Plain.TButton", command=self.clear_filters).grid(row=1, column=3, padx=6)

        self.tutor_table = Table(self.find_tab, [("name", "Tutor", 200), ("subject", "Subject", 180),
                                                 ("hourly_rate", "SAR / hour", 110),
                                                 ("open_slots", "Open slots", 110)], height=4)
        self.tutor_table.pack(fill="x")
        self.tutor_table.on_select(self.pick_tutor)

        ttk.Label(self.find_tab, text="Open time slots of the selected tutor", style="Heading.TLabel").pack(
            anchor="w", pady=(14, 6))
        self.slot_table = Table(self.find_tab, [("slot_date", "Date", 160), ("start_time", "From", 120),
                                                ("end_time", "To", 120)], height=4)
        self.slot_table.pack(fill="x")

        book = ttk.Frame(self.find_tab)
        book.pack(fill="x", pady=(12, 0))
        self.topic = tk.StringVar()
        ttk.Label(book, text="What do you need help with?").pack(side="left")
        ttk.Entry(book, textvariable=self.topic, width=40).pack(side="left", padx=10)
        ttk.Button(book, text="Book selected slot", style="Success.TButton", command=self.book_slot).pack(side="left")

    def clear_filters(self):
        self.f_subject.set("")
        self.f_rate.set("")
        self.search_tutors()

    def search_tutors(self):
        reply = self.app.api("/tutors", params={"subject": self.f_subject.get(), "max_rate": self.f_rate.get()})
        if reply is None:
            return
        self.tutor = None
        self.tutor_table.fill(reply["tutors"], "No tutors match your search.")
        self.slot_table.fill([], "Select a tutor to see open slots.")
        self.app.set_status(f"{len(reply['tutors'])} tutor(s) found.")

    def pick_tutor(self, row):
        if row is None:
            return
        self.tutor = row
        self.load_slots()

    def load_slots(self):
        reply = self.app.api("/slots", params={"tutor_id": self.tutor["id"], "status": "open"})
        if reply:
            self.slot_table.fill(reply["slots"], "This tutor has no open slots.")

    def book_slot(self):
        slot = self.slot_table.selected()
        if not slot:
            self.app.set_status("Select a tutor and a time slot first.", True)
            return
        reply = self.app.api("/bookings/add", data={"slot_id": slot["id"], "topic": self.topic.get()})
        if reply:
            self.topic.set("")
            self.search_tutors()  # refreshes the open-slot counts
            self.app.set_status(reply["message"])
        else:
            self.load_slots()  # the slot may have been taken: show the current list

    # ---------- My Bookings ----------
    def build_bookings(self):
        bar = ttk.Frame(self.bookings_tab)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Button(bar, text="Refresh", style="Plain.TButton", command=self.load_bookings).pack(side="left")
        ttk.Button(bar, text="Cancel booking", style="Danger.TButton", command=self.cancel_booking).pack(side="right")
        self.booking_table = Table(self.bookings_tab, [
            ("slot_date", "Date", 100), ("start_time", "Time", 70), ("tutor_name", "Tutor", 150),
            ("subject", "Subject", 120), ("topic", "Topic", 260), ("status_text", "Status", 100)], height=12)
        self.booking_table.pack(fill="both", expand=True)
        self.booking_table.on_select(self.show_notes)
        self.notes_label = ttk.Label(self.bookings_tab, text="", style="Muted.TLabel")
        self.notes_label.pack(anchor="w", pady=8)

    def load_bookings(self):
        reply = self.app.api("/bookings", params={"role": "student"})
        if reply is None:
            return
        for row in reply["bookings"]:
            row["status_text"] = row["status"].title()
        self.booking_table.fill(reply["bookings"], "No bookings yet. Find a tutor and book a slot.")
        self.notes_label.configure(text="")

    def show_notes(self, row):
        if row and row["status"] == "completed":
            self.notes_label.configure(text=f"Tutor notes: {row['notes'] or 'No notes added.'}")
        else:
            self.notes_label.configure(text="")

    def cancel_booking(self):
        row = self.booking_table.selected()
        if not row:
            self.app.set_status("Select a booking first.", True)
            return
        if not messagebox.askyesno("Cancel booking", f"Cancel your session on {row['slot_date']} at {row['start_time']}?"):
            return
        reply = self.app.api(f"/bookings/{row['id']}/cancel", data={})
        self.load_bookings()
        if reply:
            self.app.set_status(reply["message"])

    # ---------- Timetable ----------
    def build_timetable(self):
        ttk.Label(self.timetable_tab, text="Your confirmed sessions", style="Heading.TLabel").pack(anchor="w", pady=(0, 10))
        self.timetable_table = Table(self.timetable_tab, [
            ("slot_date", "Date", 110), ("start_time", "From", 80), ("end_time", "To", 80),
            ("tutor_name", "Tutor", 170), ("subject", "Subject", 130), ("topic", "Topic", 280)], height=14)
        self.timetable_table.pack(fill="both", expand=True)

    def load_timetable(self):
        reply = self.app.api("/bookings", params={"role": "student", "status": "approved"})
        if reply:
            self.timetable_table.fill(reply["bookings"], "No confirmed sessions yet.")
