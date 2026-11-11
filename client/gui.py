"""Peer Tutor Hub - Tkinter front end.
Start Flask first (python server/app.py), then run: python client/gui.py"""
import tkinter as tk
from tkinter import ttk

import widgets
from api_client import ApiError, request
from student_view import StudentView
from tutor_view import TutorView
from widgets import add_field


class LoginFrame(ttk.Frame):
    """Login tab and Create-account tab."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        card = ttk.Frame(self, style="Card.TFrame", padding=30)
        card.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(card, text="Peer Tutor Hub", style="CardTitle.TLabel").pack()
        ttk.Label(card, text="Find a tutor. Book a session. Learn faster.",
                  style="CardMuted.TLabel").pack(pady=(0, 12))
        tabs = ttk.Notebook(card)
        tabs.pack()
        login_tab = ttk.Frame(tabs, style="Card.TFrame", padding=16)
        register_tab = ttk.Frame(tabs, style="Card.TFrame", padding=16)
        tabs.add(login_tab, text="Log in")
        tabs.add(register_tab, text="Create account")

        # --- login ---
        self.login_user = tk.StringVar()
        self.login_pass = tk.StringVar()
        add_field(login_tab, "Username", self.login_user, 0, label_style="Card.TLabel")
        password_box = add_field(login_tab, "Password", self.login_pass, 1, show="*", label_style="Card.TLabel")
        password_box.bind("<Return>", lambda event: self.login())
        ttk.Button(login_tab, text="Log in", style="Accent.TButton", command=self.login).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Label(login_tab, text="Demo (after seed.py): sara or ali, password 1234",
                  style="CardMuted.TLabel").grid(row=3, column=0, columnspan=2, pady=(10, 0))

        # --- register ---
        self.name = tk.StringVar()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.role = tk.StringVar(value="student")
        self.subject = tk.StringVar()
        self.rate = tk.StringVar()
        add_field(register_tab, "Full name", self.name, 0, label_style="Card.TLabel")
        add_field(register_tab, "Username", self.username, 1, label_style="Card.TLabel")
        add_field(register_tab, "Password", self.password, 2, show="*", label_style="Card.TLabel")
        ttk.Label(register_tab, text="I am a", style="Card.TLabel").grid(row=3, column=0, sticky="w")
        roles = ttk.Frame(register_tab, style="Card.TFrame")
        roles.grid(row=3, column=1, sticky="w")
        for text, value in (("Student", "student"), ("Tutor", "tutor")):
            ttk.Radiobutton(roles, text=text, value=value, variable=self.role,
                            style="Card.TRadiobutton").pack(side="left", padx=(0, 14))
        add_field(register_tab, "Subject (tutors only)", self.subject, 4, label_style="Card.TLabel")
        add_field(register_tab, "Rate SAR/hour (tutors)", self.rate, 5, label_style="Card.TLabel")
        ttk.Button(register_tab, text="Create account", style="Accent.TButton", command=self.register).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(14, 0))

    def login(self):
        reply = self.app.api("/login", data={"username": self.login_user.get(), "password": self.login_pass.get()})
        if reply:
            self.app.show_dashboard(reply["user"])

    def register(self):
        reply = self.app.api("/register", data={
            "name": self.name.get(), "username": self.username.get(), "password": self.password.get(),
            "role": self.role.get(), "subject": self.subject.get(), "hourly_rate": self.rate.get()})
        if reply:
            self.app.show_dashboard(reply["user"])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Peer Tutor Hub")
        self.geometry("1100x720")
        self.minsize(1000, 660)
        widgets.apply_theme(self)
        self.user = None  # the logged-in user (a dictionary) or None

        header = ttk.Frame(self, style="Header.TFrame", padding=(22, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Peer Tutor Hub", style="Header.TLabel").pack(side="left")
        self.logout_button = ttk.Button(header, text="Log out", style="Plain.TButton", command=self.show_login)
        self.user_label = ttk.Label(header, style="HeaderSub.TLabel")

        self.status_label = tk.Label(self, anchor="w", padx=18, pady=8, font=widgets.FONT)
        self.status_label.pack(side="bottom", fill="x")
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)
        self.show_login()

    def clear_body(self):
        for child in self.body.winfo_children():
            child.destroy()

    def show_login(self):
        self.user = None
        self.clear_body()
        self.logout_button.pack_forget()
        self.user_label.pack_forget()
        LoginFrame(self.body, self).pack(fill="both", expand=True)
        self.set_status("Welcome! Log in or create an account.")

    def show_dashboard(self, user):
        self.user = user
        self.clear_body()
        self.logout_button.pack(side="right")
        self.user_label.pack(side="right", padx=18)
        self.refresh_header()
        screen = StudentView if user["role"] == "student" else TutorView
        screen(self.body, self).pack(fill="both", expand=True)
        self.set_status(f"Welcome, {user['name']}!")

    def refresh_header(self):
        self.user_label.configure(text=f"{self.user['name']}   |   {self.user['role'].title()}")

    def set_status(self, message, is_error=False):
        """Green message for success, red message for errors."""
        self.status_label.configure(text=message, bg="#FEE2E2" if is_error else "#DCFCE7",
                                    fg="#991B1B" if is_error else "#166534")

    def api(self, path, data=None, params=None):
        """Send a request to Flask. Returns the reply, or None after showing the error.
        The logged-in user's id is added to every request automatically."""
        if self.user:
            if data is not None:
                data = {"user_id": self.user["id"], **data}
            else:
                params = {"user_id": self.user["id"], **(params or {})}
        try:
            return request(path, data=data, params=params)
        except ApiError as error:
            self.set_status(str(error), True)
            return None


if __name__ == "__main__":
    App().mainloop()
