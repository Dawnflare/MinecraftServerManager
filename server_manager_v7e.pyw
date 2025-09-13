# Dawnflare Minecraft Forge Server Manager (v7e)
# - Logo above Whitelist (top-right, column 1)
# - New: Backup button refuses to run while server is running; streams output when allowed
# - New: Auto-refresh Online list every N seconds (default 30s) by sending 'list'
# - Keeps: auto-start, whitelist tools, persistent join/leave log, stop.flag watcher,
#          Exit = save-all → stop → 3s delay, command box, no extra console

from pathlib import Path
import os, subprocess, threading, queue, time, json, re, tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

APP_NAME = "Dawnflare Minecraft Forge Server Manager"
AUTO_START = True

# ---- USER SETTINGS -----------------------------------------------------------
JAVA_PATH = r"C:\\Program Files\\Java\\jdk-21\\bin\\java.exe"
XMS = "2G"
XMX = "10G"
PLAYER_LOG_PATH = Path(r"D:\\Backups\\MinecraftBackups\\player_activity.log")
SPLASH_IMAGE = "IceFireYinYangTransparent.png"
AUTO_ONLINE_REFRESH_SECS = 30   # how often to auto-run 'list' while running
# -----------------------------------------------------------------------------

SERVER_DIR = Path(".").resolve()
LOG_PATH = SERVER_DIR / "wrapper.log"
STOP_FLAG = SERVER_DIR / "stop.flag"
USER_ARGS = SERVER_DIR / "user_jvm_args.txt"
WL_PATH = SERVER_DIR / "whitelist.json"
BACKUP_BAT = SERVER_DIR / "backup.bat"


def find_win_args():
    base = SERVER_DIR / "libraries" / "net" / "minecraftforge" / "forge"
    if not base.exists():
        return None
    vers = sorted((p for p in base.iterdir() if p.is_dir()), key=lambda p: p.name, reverse=True)
    for v in vers:
        f = v / "win_args.txt"
        if f.exists():
            return f
    return None


WIN_ARGS = find_win_args()


class Manager:
    def __init__(self):
        self.proc = None
        self.q = queue.Queue()
        self.online = set()
        self.ui_update_online = None
        try:
            PLAYER_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    # ----- logging ------------------------------------------------------------
    def _append_logfile(self, path: Path, line: str):
        try:
            with open(path, "a", encoding="utf-8", errors="ignore") as fp:
                fp.write(line)
        except Exception:
            pass

    def log(self, txt):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {txt}\n"
        self._append_logfile(LOG_PATH, line)
        self.q.put(line)

    # ----- start/stop ---------------------------------------------------------
    def build_command(self):
        if not Path(JAVA_PATH).exists():
            raise FileNotFoundError(f"Java not found at: {JAVA_PATH}")
        if WIN_ARGS is None or not WIN_ARGS.exists():
            raise FileNotFoundError("Forge win_args.txt not found. Run the Forge installer here (Install server).")
        USER_ARGS.write_text(f"-Xms{XMS}\n-Xmx{XMX}\n", encoding="utf-8")
        return [JAVA_PATH, f"@{USER_ARGS.name}", f"@{WIN_ARGS}", "nogui"]

    def start(self):
        if self.proc and self.proc.poll() is None:
            self.log("Server already running.")
            return
        try:
            cmd = self.build_command()
        except Exception as e:
            try: messagebox.showerror(APP_NAME, str(e))
            except Exception: pass
            self.log(str(e)); return
        try:
            if STOP_FLAG.exists(): STOP_FLAG.unlink()
        except Exception: pass
        self.log("Starting: " + " ".join(map(str, cmd)))
        creationflags = 0; startupinfo = None
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.proc = subprocess.Popen(
            cmd, cwd=str(SERVER_DIR), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True, creationflags=creationflags, startupinfo=startupinfo
        )
        threading.Thread(target=self._reader, daemon=True).start()
        threading.Thread(target=self._watch_stopflag, daemon=True).start()

    JOIN_RE  = re.compile(r"\]:\s*([A-Za-z0-9_]+)\s+joined the game")
    LEAVE_RE = re.compile(r"\]:\s*([A-Za-z0-9_]+)\s+left the game")
    LIST_RE  = re.compile(r"players online:\s*(.*)$")

    def _parse_line_for_events(self, line: str):
        m = self.JOIN_RE.search(line)
        if m:
            name = m.group(1)
            if name not in self.online:
                self.online.add(name)
                self._player_event("JOIN", name)
                self._refresh_online_ui()
            return
        m = self.LEAVE_RE.search(line)
        if m:
            name = m.group(1)
            if name in self.online:
                self.online.discard(name)
                self._player_event("LEAVE", name)
                self._refresh_online_ui()
            return
        m = self.LIST_RE.search(line)
        if m:
            names_str = m.group(1).strip()
            names = [] if not names_str else [x.strip() for x in names_str.split(',') if x.strip()]
            self.online = set(names)
            self._refresh_online_ui()

    def _player_event(self, kind: str, name: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self._append_logfile(PLAYER_LOG_PATH, f"[{ts}] {kind}: {name}\n")

    def _refresh_online_ui(self):
        if self.ui_update_online:
            try: self.ui_update_online(sorted(self.online))
            except Exception: pass

    def _reader(self):
        try:
            for raw in self.proc.stdout:
                if not raw: continue
                line = raw.rstrip(); self.log(line)
                try: self._parse_line_for_events(line)
                except Exception: pass
        finally:
            rc = self.proc.poll(); self.log(f"Server exited with code {rc}.")

    def _watch_stopflag(self):
        while self.proc and self.proc.poll() is None:
            if STOP_FLAG.exists():
                try: STOP_FLAG.unlink()
                except Exception: pass
                self.log("stop.flag detected — sending 'stop'..."); self.stop(); break
            time.sleep(1)

    def send_command(self, cmd_text: str):
        if not self.proc or self.proc.poll() is not None:
            self.log("Cannot send command: server is not running.")
            return False
        try:
            self.proc.stdin.write(cmd_text.strip() + "\n"); self.proc.stdin.flush(); self.log(f"> {cmd_text.strip()}")
            return True
        except Exception as e:
            self.log(f"stdin error: {e}"); return False

    def stop(self):
        if not self.proc or self.proc.poll() is not None:
            self.log("Server not running."); return
        try:
            self.proc.stdin.write("save-all\n"); self.proc.stdin.flush(); time.sleep(1)
            self.log("Sending 'stop'..."); self.proc.stdin.write("stop\n"); self.proc.stdin.flush()
        except Exception as e:
            self.log(f"stdin error: {e}")
        for _ in range(20):
            if self.proc.poll() is not None: break
            time.sleep(1)
        if self.proc.poll() is None:
            self.log("Grace over, terminating...")
            try: self.proc.terminate()
            except Exception: pass
        for _ in range(5):
            if self.proc.poll() is not None: break
            time.sleep(1)
        if self.proc.poll() is None:
            self.log("Force kill...")
            try: self.proc.kill()
            except Exception: pass


mgr = Manager()
root = tk.Tk(); root.title(APP_NAME); root.geometry("1280x780")
frm = tk.Frame(root, padx=8, pady=6); frm.pack(fill="both", expand=True)

# Optional splash image intended above Whitelist (column 1)
img_obj = None
img_path = SERVER_DIR / SPLASH_IMAGE
if img_path.exists():
    try:
        img_obj = tk.PhotoImage(file=str(img_path))
        factor = 1
        while img_obj.width() // factor > 360: factor *= 2
        if factor > 1: img_obj = img_obj.subsample(factor, factor)
    except Exception: img_obj = None

# Info labels occupy column 0 only (so column 1 is free for the image)
for r, text in enumerate([
    f"Server folder: {SERVER_DIR}",
    f"Java: {JAVA_PATH}",
    f"Forge args: {WIN_ARGS if WIN_ARGS else '(not found)'}",
    f"Heap: -Xms{XMS} -Xmx{XMX}",
]):
    tk.Label(frm, text=text).grid(row=r, column=0, sticky="w")

# Splash image at rows 0-3, column 1 (above Whitelist)
if img_obj is not None:
    tk.Label(frm, image=img_obj, borderwidth=0, highlightthickness=0).grid(row=0, column=1, rowspan=4, sticky="ne", padx=(10,0))

# Button row (Start / Stop / Save All / Backup / Make stop.flag / Exit)
btns = tk.Frame(frm); btns.grid(row=4, column=0, columnspan=2, pady=(4,4), sticky="w")

def save_all(): mgr.send_command("save-all")

def run_backup():
    # Refuse to run while server is running
    if mgr.proc and mgr.proc.poll() is None:
        msg = "Backup refused: stop the server before running Backup."
        try: messagebox.showwarning(APP_NAME, msg)
        except Exception: pass
        mgr.log(msg)
        return
    if not BACKUP_BAT.exists():
        messagebox.showerror(APP_NAME, f"backup.bat not found at {BACKUP_BAT}")
        return
    mgr.log(f"Running backup script: {BACKUP_BAT}")
    def worker():
        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            p = subprocess.Popen(["cmd", "/c", str(BACKUP_BAT)], cwd=str(SERVER_DIR),
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, creationflags=creationflags)
            for line in p.stdout:
                if line: mgr.log(f"[backup] {line.rstrip()}")
            rc = p.wait()
            mgr.log(f"Backup finished with code {rc}.")
        except Exception as e:
            mgr.log(f"Backup error: {e}")
    threading.Thread(target=worker, daemon=True).start()

def make_flag():
    STOP_FLAG.write_text("stop", encoding="utf-8")
    messagebox.showinfo(APP_NAME, "stop.flag created (server will stop within ~20s).")

def exit_app():
    try: mgr.send_command("save-all")
    except Exception: pass
    try:
        if mgr.proc and mgr.proc.poll() is None: mgr.stop()
        if STOP_FLAG.exists(): STOP_FLAG.unlink()
    except Exception: pass
    root.after(3000, root.destroy)

for label, cmd in (("Start Server", mgr.start), ("Stop Server", mgr.stop), ("Save All", save_all), ("Backup", run_backup), ("Make stop.flag", make_flag), ("Exit", exit_app)):
    tk.Button(btns, text=label, width=16, command=cmd).pack(side="left", padx=5)

# Left: log + command
log = scrolledtext.ScrolledText(frm, width=90, height=26, state="disabled")
log.grid(row=5, column=0, sticky="nsew", padx=(0,10))
cmd_row = tk.Frame(frm); cmd_row.grid(row=6, column=0, pady=(6,0), sticky="we")
tk.Label(cmd_row, text="Command:").pack(side="left")
cmd_var = tk.StringVar(); cmd_entry = tk.Entry(cmd_row, textvariable=cmd_var)
cmd_entry.pack(side="left", padx=6, fill="x", expand=True)

def send_cmd_event(event=None):
    txt = cmd_var.get().strip()
    if txt: mgr.send_command(txt); cmd_var.set("")

tk.Button(cmd_row, text="Send", command=send_cmd_event).pack(side="left")
cmd_entry.bind("<Return>", send_cmd_event)

# Middle: Whitelist
wl_frame = tk.LabelFrame(frm, text="Whitelist", padx=8, pady=8)
wl_frame.grid(row=5, column=1, rowspan=2, sticky="nsew")
wl_frame.grid_rowconfigure(0, weight=1); wl_frame.grid_columnconfigure(0, weight=1)
wl_list = tk.Listbox(wl_frame); wl_list.grid(row=0, column=0, sticky="nsew")
wl_btns = tk.Frame(wl_frame); wl_btns.grid(row=1, column=0, sticky="we", pady=(8,0))

def refresh_wl():
    wl_list.delete(0, tk.END)
    try:
        if WL_PATH.exists():
            data = json.loads(WL_PATH.read_text(encoding="utf-8"))
            for e in sorted({d.get("name", "").strip() for d in data if isinstance(d, dict)}):
                if e: wl_list.insert(tk.END, e)
    except Exception as e:
        mgr.log(f"Whitelist read error: {e}")

def wl_add():
    if not (mgr.proc and mgr.proc.poll() is None):
        messagebox.showwarning(APP_NAME, "Server is not running. Start it before adding to whitelist.")
        return
    name = simpledialog.askstring(APP_NAME, "Minecraft username to whitelist:")
    if name: mgr.send_command(f"whitelist add {name.strip()}"); root.after(1500, refresh_wl)

def wl_remove():
    sel = wl_list.curselection()
    if not sel: messagebox.showinfo(APP_NAME, "Select a player to remove."); return
    name = wl_list.get(sel[0])
    if mgr.proc and mgr.proc.poll() is None:
        mgr.send_command(f"whitelist remove {name}"); root.after(1500, refresh_wl)
    else:
        try:
            if WL_PATH.exists():
                data = json.loads(WL_PATH.read_text(encoding="utf-8"))
                data = [d for d in data if not (isinstance(d, dict) and d.get("name", "").lower() == name.lower())]
                WL_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
                mgr.log(f"(offline) Removed {name} from whitelist.json")
                refresh_wl()
        except Exception as e:
            mgr.log(f"Whitelist write error: {e}")

for lbl, fn in (("Refresh", refresh_wl), ("Add…", wl_add), ("Remove", wl_remove)):
    tk.Button(wl_btns, text=lbl, width=10, command=fn).pack(side="left", padx=4)

# Right: Online players
online_frame = tk.LabelFrame(frm, text="Online Players", padx=8, pady=8)
online_frame.grid(row=5, column=2, rowspan=2, sticky="nsew")
online_frame.grid_rowconfigure(0, weight=1); online_frame.grid_columnconfigure(0, weight=1)

online_list = tk.Listbox(online_frame); online_list.grid(row=0, column=0, sticky="nsew")
ob = tk.Frame(online_frame); ob.grid(row=1, column=0, sticky="we", pady=(8,0))

def online_refresh(): mgr.send_command("list")

tk.Button(ob, text="Refresh", width=10, command=online_refresh).pack(side="left", padx=4)

# Callback so the manager can update the online list

def ui_update_online(names):
    online_list.delete(0, tk.END)
    for n in names: online_list.insert(tk.END, n)

mgr.ui_update_online = ui_update_online

# Grid weights
frm.grid_rowconfigure(5, weight=1)
frm.grid_columnconfigure(0, weight=3)
frm.grid_columnconfigure(1, weight=2)
frm.grid_columnconfigure(2, weight=2)

# Periodic tasks ---------------------------------------------------------------

def _auto_refresh_online():
    try:
        if mgr.proc and mgr.proc.poll() is None:
            mgr.send_command("list")
    finally:
        root.after(AUTO_ONLINE_REFRESH_SECS * 1000, _auto_refresh_online)

# Pump loop

def pump():
    try:
        while True:
            line = mgr.q.get_nowait()
            log.configure(state="normal"); log.insert("end", line); log.see("end"); log.configure(state="disabled")
    except queue.Empty:
        pass
    root.after(150, pump)

mgr.q.put("Tip: Use the Command box or top-row buttons. Whitelist panel adds/removes; Online panel shows who is connected.\n")
mgr.q.put("This app watches for 'stop.flag' in the server folder (good for Task Scheduler on shutdown).\n")

if AUTO_START: root.after(200, mgr.start)
refresh_wl(); ui_update_online(sorted(mgr.online))
root.after(10000, _auto_refresh_online)  # start auto refresh after 10s
pump(); root.mainloop()
