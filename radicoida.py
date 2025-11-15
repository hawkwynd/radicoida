import os
import json
import time
import threading
import tkinter as tk
from tkinter import StringVar

# === CONFIG ===
JOURNAL_FOLDER = os.path.expanduser(
    "~/Saved Games/Frontier Developments/Elite Dangerous/"
)
JOURNAL_PREFIX = "Journal.2025-11-"
TARGET_GENUS = "Radicoida"

# === COUNTERS ===
on_hand = 0
submitted = 0

# Track processed lines
processed = set()


# === DRAGGABLE OVERLAY ===
def create_overlay():
    root = tk.Tk()
    root.title("Radicoida Tracker")
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.attributes("-alpha", 0.80)

    # Initial position
    root.geometry("+100+450")

    var = StringVar()
    var.set("Radicoida Scans\nSubmitted:\t0\nOn-hand:\t0")

    label = tk.Label(
        root,
        textvariable=var,
        font=("Euro Caps", 18, "bold"),
        fg="lime",
        bg="black",
        padx=10,
        pady=8,
        justify="left",
    )
    label.pack()

    # === DRAG LOGIC ===
    def start_move(event):
        root.x = event.x
        root.y = event.y

    def do_move(event):
        x = root.winfo_x() + (event.x - root.x)
        y = root.winfo_y() + (event.y - root.y)
        root.geometry(f"+{x}+{y}")

    label.bind("<Button-1>", start_move)
    label.bind("<B1-Motion>", do_move)

    return root, var


# === JOURNAL SCANNER ===
def scan_journals(var):
    global on_hand, submitted

    while True:
        try:
            files = [
                f for f in os.listdir(JOURNAL_FOLDER)
                if f.startswith(JOURNAL_PREFIX)
            ]
            files.sort()

            for fname in files:
                path = os.path.join(JOURNAL_FOLDER, fname)

                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line in processed:
                            continue
                        processed.add(line)

                        line = line.strip()
                        if not line.startswith("{"):
                            continue

                        try:
                            event = json.loads(line)
                        except:
                            continue

                        ev = event.get("event")

                        # Analyse scan
                        if ev == "ScanOrganic":
                            if (
                                event.get("ScanType") == "Analyse"
                                and event.get("Genus_Localised") == TARGET_GENUS
                            ):
                                on_hand += 1

                        # SellOrganicData resets
                        if ev == "SellOrganicData":
                            submitted += on_hand
                            on_hand = 0

                        # Update overlay
                        var.set(
                            f"Radicoida Scans\n"
                            f"Submitted: {submitted}\n"
                            f"On-hand: {on_hand}"
                        )

            time.sleep(1)

        except Exception as e:
            print("Error:", e)
            time.sleep(2)


# === MAIN ===
if __name__ == "__main__":
    root, var = create_overlay()
    t = threading.Thread(target=scan_journals, args=(var,), daemon=True)
    t.start()
    root.mainloop()
