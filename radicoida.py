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

# === PER-COMMANDER COUNTERS ===
# commanders[name] = {"on_hand": int, "submitted": int}
commanders = {}

# Track processed lines
processed = set()

# === DRAGGABLE OVERLAY ===
def create_overlay():
    root = tk.Tk()
    root.title("Radicoida Tracker")
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.attributes("-alpha", 0.80)

    # Move overlay left so extra text fits
    root.geometry("+30+400")
    
    # Esc key exits the application
    root.bind("<Escape>", lambda e: root.destroy())


    var = StringVar()
    var.set("Radicoida Scans\n(no data yet)")

    label = tk.Label(
        root,
        textvariable=var,
        font=("Euro Caps", 16, "normal"),
        fg="lime",
        bg="black",
        padx=20,      # widened
        pady=10,
        justify="left",
        anchor="w",   # align text left
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

    global commanders
    current_cmr = None

    while True:
        try:
            files = [
                f for f in os.listdir( JOURNAL_FOLDER )
                if f.startswith(JOURNAL_PREFIX)
            ]
            files.sort()

            for fname in files:
                path = os.path.join(JOURNAL_FOLDER, fname)

                with open(path, "r", encoding="utf-8") as f:
                    for raw in f:
                        if raw in processed:
                            continue
                        processed.add(raw)

                        line = raw.strip()
                        if not line.startswith("{"):
                            continue

                        try:
                            event = json.loads(line)
                        except:
                            continue

                        ev = event.get("event")

                        # === Detect commander via LoadGame ===
                        if ev == "LoadGame":
                            cmr = event.get("Commander")
                            
                            if cmr:
                                current_cmr = cmr
                                if cmr not in commanders:
                                    commanders[cmr] = {"on_hand": 0, "submitted": 0}
                            continue

                        # === Skip until LoadGame detected ===
                        if not current_cmr:
                            continue  

                        # === Add commander to commander list ===
                        if current_cmr not in commanders:
                            commanders[current_cmr] = {"on_hand": 0, "submitted": 0}

                        # === Get Current Commander Data===
                        cmrdata = commanders[current_cmr]

                        # === Analyse scan ===
                        if ev == "ScanOrganic":
                            if (event.get("ScanType") == "Analyse" and
                                event.get("Genus_Localised") == TARGET_GENUS):
                                cmrdata["on_hand"] += 1

                        # === SellOrganicData ===
                        if ev == "SellOrganicData":
                            cmrdata["submitted"] += cmrdata["on_hand"]
                            cmrdata["on_hand"] = 0

                        # === Update overlay text ===
                        var.set(
                            f"Radicoida Scans by {current_cmr}\n"
                            f"Submitted: {cmrdata['submitted']}\n"
                            f"On-hand: {cmrdata['on_hand']}\n"
                            f"Esc to Exit"
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
