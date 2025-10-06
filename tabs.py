#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
from pathlib import Path

SESSION_FILE = Path.home() / ".miniplexer_session.json"
WM_CLASS = "miniplexer_tab"
LOG_FILE = Path.home() / ".miniplexer.log"

def log_message(message):
    """Appends a message to the log file."""
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time.time()}] {message}\n")

def read_session():
    """Reads the session file and returns the data."""
    if not SESSION_FILE.exists():
        return {"windows": [], "active": None}
    with open(SESSION_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"windows": [], "active": None}

def write_session(data):
    """Writes the given data to the session file."""
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=2)



def run_command(cmd):
    """Runs a command and returns its output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def launch_terminal():
    """Launches a new alacritty terminal."""
    # Using --class allows us to identify our windows easily
    subprocess.Popen(["alacritty", "--class", f"{WM_CLASS},{WM_CLASS}"])

def find_windows():
    """Finds all window IDs managed by this script."""
    output = run_command(["xdotool", "search", "--class", WM_CLASS])
    if not output:
        return []
    return [int(w_id) for w_id in output.split()]

def handle_start():
    """Starts a new session."""
    if SESSION_FILE.exists():
        # Before starting a new one, end the old session to clean up any zombie windows
        handle_end()

    print("Starting new session...")
    launch_terminal()

    # Poll for up to 5 seconds for the new window to appear
    new_window = None
    for _ in range(50):  # 50 * 0.1s = 5s timeout
        windows = find_windows()
        if windows:
            new_window = windows[0]
            break
        time.sleep(0.1)

    if not new_window:
        print("Failed to start and find the new terminal window.")
        return

    session = {"windows": [new_window], "active": new_window}
    write_session(session)
    print(f"New session started with window {new_window}")

def handle_new():
    """Creates a new tab."""
    log_message("--- handle_new called ---")
    session = read_session()
    log_message(f"Initial session: {session}")

    if not session.get("windows"):
        log_message("No active session. Aborting.")
        print("No active session. Use 'start' first.")
        return

    active_window = session.get("active")
    windows_before = set(find_windows())
    log_message(f"Windows before launch: {windows_before}")

    log_message("Launching new terminal...")
    launch_terminal()

    # Poll for up to 5 seconds for the new window to appear
    new_window = None
    for i in range(50):
        windows_after = set(find_windows())
        new_windows = windows_after - windows_before
        if new_windows:
            log_message(f"Found new window(s) {new_windows} on attempt {i + 1}")
            new_window = new_windows.pop()
            break
        time.sleep(0.1)

    if not new_window:
        log_message("Polling timed out. No new window found.")
        print("Failed to create a new terminal window.")
        return

    log_message(f"Hiding old active window: {active_window}")
    if active_window:
        run_command(["xdotool", "windowunmap", str(active_window)])

    session["windows"].append(new_window)
    session["active"] = new_window
    log_message(f"Writing new session: {session}")
    write_session(session)
    log_message("--- handle_new finished ---")
    print(f"New tab created with window {new_window}")

def _switch_to_window(current_active, new_active):
    """Hides the current window and shows the new one."""
    if current_active:
        run_command(["xdotool", "windowunmap", str(current_active)])
    run_command(["xdotool", "windowmap", str(new_active)])
    run_command(["xdotool", "windowactivate", str(new_active)])

def handle_next():
    """Switches to the next tab."""
    session = read_session()
    windows = session.get("windows", [])
    if len(windows) < 2:
        return # Nothing to switch

    active = session.get("active")
    try:
        current_idx = windows.index(active)
        next_idx = (current_idx + 1) % len(windows)
    except ValueError:
        next_idx = 0 # Default to first window

    new_active = windows[next_idx]
    _switch_to_window(active, new_active)

    session["active"] = new_active
    write_session(session)

def handle_prev():
    """Switches to the previous tab."""
    session = read_session()
    windows = session.get("windows", [])
    if len(windows) < 2:
        return # Nothing to switch

    active = session.get("active")
    try:
        current_idx = windows.index(active)
        prev_idx = (current_idx - 1 + len(windows)) % len(windows)
    except ValueError:
        prev_idx = 0 # Default to first window

    new_active = windows[prev_idx]
    _switch_to_window(active, new_active)

    write_session(session)

def handle_end():
    """Ends the current session, closing all windows."""
    print("Ending session...")
    session = read_session()
    for w_id in session.get("windows", []):
        run_command(["xdotool", "windowclose", str(w_id)])
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
    print("Session ended.")


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # If no command, default to starting a session
        handle_start()
        return

    command = sys.argv[1]
    commands = {
        "start": handle_start,
        "new": handle_new,
        "next": handle_next,
        "prev": handle_prev,
        "end": handle_end,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(f"Available commands: {list(commands.keys())}")
        sys.exit(1)

if __name__ == "__main__":
    main()
