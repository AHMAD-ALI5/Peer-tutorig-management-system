"""Report helper: asks Flask for all saved bookings and writes a text report
using one Thread.  Run (Flask must be running):  python report_helper.py"""
import json
import threading
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

URL = "http://127.0.0.1:5050/report-data"
REPORT_FILE = "tutor_report.txt"


def write_report(bookings, result):
    """Runs inside the thread. Saves the file and stores success or failure in result."""
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as file:
            file.write("PEER TUTOR HUB - BOOKING REPORT\n")
            file.write("=" * 34 + "\n")
            if not bookings:
                file.write("No bookings saved yet.\n")
            for b in bookings:
                file.write(f"#{b['id']} {b['slot_date']} {b['start_time']} | {b['subject']} | "
                           f"tutor {b['tutor_name']} | student {b['student_name']} | {b['status']}\n")
            file.write(f"\nTotal bookings: {len(bookings)}\n")
        result["saved"] = True
    except OSError as error:
        result["saved"] = False
        result["error"] = str(error)


def main():
    try:
        with urlopen(URL, timeout=5) as reply:
            bookings = json.loads(reply.read().decode("utf-8"))["bookings"]
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        print(f"Could not get records from Flask: {error}")
        return
    result = {}
    worker = threading.Thread(target=write_report, args=(bookings, result))
    worker.start()
    worker.join()
    if result.get("saved"):
        print(f"Report saved to {REPORT_FILE} ({len(bookings)} bookings).")
    else:
        print(f"Report failed: {result.get('error')}")


if __name__ == "__main__":
    main()
