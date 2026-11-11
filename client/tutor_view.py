"""Tutor dashboard: availability, booking requests, sessions and profile."""
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, simpledialog, ttk

from widgets import Table, add_field


class TutorView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=14)
        self.tabs = []
        for name in ("Availability", "Requests", "My Sessions", "Profile"):
            tab = ttk.Frame(self.notebook, padding=14)
            self.notebook.add(tab, text=name)
            self.tabs.append(tab)
        self.build_availability(self.tabs[0])
        self.build_requests(self.tabs[1])
        self.build_sessions(self.tabs[2])
        self.build_profile(self.tabs[3])
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.load_slots()

    def on_tab_change(self, event):
        index = self.notebook.index("current")
        if index == 0:
            self.load_slots()
        elif index == 1:
            self.load_requests()
        elif index == 2:
            self.load_sessions()

    # ---------- Availability ----------
    def build_availability(self, tab):
        ttk.Label(tab, text="Your time slots (students can book the open ones)", style="Heading.TLabel").pack(
            anchor="w", pady=(0, 10))
        self.slot_table = Table(tab, [("slot_date", "Date", 140), ("start_time", "From", 100),
                                      ("end_time", "To", 100), ("status_text", "Status", 100)], height=10)
        self.slot_table.pack(fill="both", expand=True)

        form = ttk.LabelFrame(tab, text="Add a new slot", padding=12)
        form.pack(fill="x", pady=(12, 0))
        self.slot_date = tk.StringVar(value=(date.today() + timedelta(days=1)).isoformat())
        self.start_time = tk.StringVar(value="16:00")
        self.end_time = tk.StringVar(value="17:00")
        for column, (text, variable, width) in enumerate([("Date (YYYY-MM-DD)", self.slot_date, 14),
                                                          ("From (HH:MM)", self.start_time, 8),
                                                          ("To (HH:MM)", self.end_time, 8)]):
            ttk.Label(form, text=text, style="Muted.TLabel").grid(row=0, column=column, sticky="w", padx=(0, 12))
            ttk.Entry(form, textvariable=variable, width=width).grid(row=1, column=column, padx=(0, 12))
        ttk.Button(form, text="Add slot", style="Accent.TButton", command=self.add_slot).grid(row=1, column=3)
        ttk.Button(form, text="Delete selected slot", style="Danger.TButton", command=self.delete_slot).grid(
            row=1, column=4, padx=(20, 0))

    def load_slots(self):
        reply = self.app.api("/slots", params={"tutor_id": self.app.user["id"]})
        if reply is None:
            return
        for slot in reply["slots"]:
            slot["status_text"] = slot["status"].title()
        self.slot_table.fill(reply["slots"], "No slots yet. Add your first time slot below.")

    def add_slot(self):
        reply = self.app.api("/slots/add", data={"slot_date": self.slot_date.get(),
                                                 "start_time": self.start_time.get(),
                                                 "end_time": self.end_time.get()})
        self.load_slots()
        if reply:
            self.app.set_status(reply["message"])

    def delete_slot(self):
        row = self.slot_table.selected()
        if not row:
            self.app.set_status("Select a slot first.", True)
            return
        if not messagebox.askyesno("Delete slot", f"Delete the slot on {row['slot_date']} at {row['start_time']}?"):
            return
        reply = self.app.api(f"/slots/{row['id']}/delete", data={})
        self.load_slots()
        if reply:
            self.app.set_status(reply["message"])

    # ---------- Requests ----------
    def build_requests(self, tab):
        bar = ttk.Frame(tab)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Label(bar, text="Pending requests from students", style="Heading.TLabel").pack(side="left")
        ttk.Button(bar, text="Reject", style="Danger.TButton", command=self.reject).pack(side="right")
        ttk.Button(bar, text="Approve", style="Success.TButton", command=self.approve).pack(side="right", padx=8)
        ttk.Button(bar, text="Refresh", style="Plain.TButton", command=self.load_requests).pack(side="right")
        self.request_table = Table(tab, [("slot_date", "Date", 110), ("start_time", "Time", 80),
                                         ("student_name", "Student", 180), ("topic", "Topic", 400)], height=14)
        self.request_table.pack(fill="both", expand=True)

    def load_requests(self):
        reply = self.app.api("/bookings", params={"role": "tutor", "status": "pending"})
        if reply:
            self.request_table.fill(reply["bookings"], "No pending requests right now.")

    def answer_request(self, action, question=None):
        row = self.request_table.selected()
        if not row:
            self.app.set_status("Select a request first.", True)
            return
        if question and not messagebox.askyesno("Confirm", question):
            return
        reply = self.app.api(f"/bookings/{row['id']}/{action}", data={})
        self.load_requests()
        if reply:
            self.app.set_status(reply["message"])

    def approve(self):
        self.answer_request("approve")

    def reject(self):
        self.answer_request("reject", "Reject this request?")

    # ---------- My Sessions ----------
    def build_sessions(self, tab):
        bar = ttk.Frame(tab)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Label(bar, text="All your sessions", style="Heading.TLabel").pack(side="left")
        ttk.Button(bar, text="Mark completed + add notes", style="Success.TButton",
                   command=self.complete).pack(side="right")
        ttk.Button(bar, text="Refresh", style="Plain.TButton", command=self.load_sessions).pack(side="right", padx=8)
        self.session_table = Table(tab, [("slot_date", "Date", 100), ("start_time", "Time", 70),
                                         ("student_name", "Student", 150), ("topic", "Topic", 240),
                                         ("status_text", "Status", 100), ("notes", "Notes", 240)], height=14)
        self.session_table.pack(fill="both", expand=True)

    def load_sessions(self):
        reply = self.app.api("/bookings", params={"role": "tutor"})
        if reply is None:
            return
        for row in reply["bookings"]:
            row["status_text"] = row["status"].title()
        self.session_table.fill(reply["bookings"], "No sessions yet.")

    def complete(self):
        row = self.session_table.selected()
        if not row:
            self.app.set_status("Select a session first.", True)
            return
        notes = simpledialog.askstring("Session notes", "Short note about the session (optional):", parent=self)
        if notes is None:  # the tutor pressed Cancel
            return
        reply = self.app.api(f"/bookings/{row['id']}/complete", data={"notes": notes})
        self.load_sessions()
        if reply:
            self.app.set_status(reply["message"])

    # ---------- Profile ----------
    def build_profile(self, tab):
        card = ttk.LabelFrame(tab, text="Your public profile", padding=16)
        card.pack(anchor="nw")
        self.p_name = tk.StringVar(value=self.app.user["name"])
        self.p_subject = tk.StringVar(value=self.app.user["subject"])
        self.p_rate = tk.StringVar(value=f"{self.app.user['hourly_rate']:g}")
        add_field(card, "Name", self.p_name, 0)
        add_field(card, "Subject", self.p_subject, 1)
        add_field(card, "Rate (SAR / hour)", self.p_rate, 2)
        ttk.Button(card, text="Save changes", style="Accent.TButton", command=self.save_profile).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def save_profile(self):
        reply = self.app.api("/profile", data={"name": self.p_name.get(), "subject": self.p_subject.get(),
                                               "hourly_rate": self.p_rate.get()})
        if reply:
            self.app.user = reply["user"]
            self.app.refresh_header()
            self.app.set_status(reply["message"])
