"""Colours and styles, plus two small helpers used by every screen: add_field and Table."""
from tkinter import ttk

PRIMARY = "#4F46E5"
DARK = "#312E81"
SOFT = "#E0E7FF"
BG = "#F4F6FB"
CARD = "#FFFFFF"
TEXT = "#1F2937"
MUTED = "#6B7280"
FONT = ("Segoe UI", 10)
BOLD = ("Segoe UI", 10, "bold")


def apply_theme(root):
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BG, foreground=TEXT, font=FONT)
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"), foreground=DARK)
    style.configure("Header.TFrame", background=DARK)
    style.configure("Header.TLabel", background=DARK, foreground="white", font=("Segoe UI", 15, "bold"))
    style.configure("HeaderSub.TLabel", background=DARK, foreground="#C7D2FE")
    style.configure("Card.TFrame", background=CARD)
    style.configure("Card.TLabel", background=CARD)
    style.configure("CardTitle.TLabel", background=CARD, foreground=PRIMARY, font=("Segoe UI", 22, "bold"))
    style.configure("CardMuted.TLabel", background=CARD, foreground=MUTED)
    style.configure("Card.TRadiobutton", background=CARD)
    style.configure("TLabelframe", background=BG)
    style.configure("TLabelframe.Label", background=BG, foreground=PRIMARY, font=BOLD)
    style.configure("TEntry", padding=5)
    for name, color, hover in (("Accent", PRIMARY, "#3730A3"), ("Success", "#16A34A", "#15803D"),
                               ("Danger", "#DC2626", "#B91C1C"), ("Plain", "#6B7280", "#4B5563")):
        style.configure(f"{name}.TButton", background=color, foreground="white",
                        padding=(14, 7), borderwidth=0, font=BOLD)
        style.map(f"{name}.TButton", background=[("active", hover)])
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(20, 9), font=BOLD, background="#E5E7EB")
    style.map("TNotebook.Tab", background=[("selected", PRIMARY)], foreground=[("selected", "white")])
    style.configure("Treeview", rowheight=30, background=CARD, fieldbackground=CARD, borderwidth=0)
    style.configure("Treeview.Heading", background=SOFT, foreground=DARK, font=BOLD, padding=6, relief="flat")
    style.map("Treeview", background=[("selected", PRIMARY)], foreground=[("selected", "white")])


def add_field(parent, label, variable, row, show=None, label_style="TLabel"):
    """One label + one text box on a grid row. Returns the text box."""
    ttk.Label(parent, text=label, style=label_style).grid(row=row, column=0, sticky="w", pady=5, padx=(0, 14))
    entry = ttk.Entry(parent, textvariable=variable, width=30, show=show)
    entry.grid(row=row, column=1, pady=5)
    return entry


class Table(ttk.Frame):
    """A list of records. columns = [(key, title, width), ...]. rows = list of dictionaries."""

    def __init__(self, parent, columns, height=8):
        super().__init__(parent)
        self.keys = [c[0] for c in columns]
        self.rows = []
        self.tree = ttk.Treeview(self, columns=self.keys, show="headings", height=height, selectmode="browse")
        for key, title, width in columns:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.empty = ttk.Label(self, style="Muted.TLabel")  # message shown when the list is empty
        self.empty.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def fill(self, rows, empty_text="Nothing to show."):
        self.rows = rows
        self.tree.delete(*self.tree.get_children())
        for index, row in enumerate(rows):
            self.tree.insert("", "end", iid=str(index), values=[row.get(key, "") for key in self.keys])
        self.empty.configure(text="" if rows else empty_text)

    def selected(self):
        """The selected row (a dictionary) or None."""
        selection = self.tree.selection()
        return self.rows[int(selection[0])] if selection else None

    def on_select(self, callback):
        self.tree.bind("<<TreeviewSelect>>", lambda event: callback(self.selected()))
