# Minecraft Forge Server Manager (Windows GUI)

**Version 8**

A no-console Python **.pyw** GUI for starting/stopping a **Forge (Java) Minecraft server** on Windows.
It uses Forge’s official arg files (`@user_jvm_args.txt` and `@...\win_args.txt`), shows live logs,
lets you send server commands, manage the whitelist, view online players, and integrates with backups
and Windows Task Scheduler.

> This repo archives the manager script so it’s easy to move to a new PC.  
> It does **not** include the Forge server files themselves.

---

## Features

- **One-click start/stop** (or auto-start on launch).
- **Command box** (send any server command).
- **Whitelist tools**: add/remove and view current list.
- **Online players panel** (auto-refresh every 30 s; manual refresh button).
- **Backup button** (runs `backup.bat`; refuses if the server is running).
- Watches **`stop.flag`** (handy for Task Scheduler shutdowns).
- Optional **splash image** (PNG/ICO) and **player join/leave log**.
- Runs as **.pyw** → no black console window.
- **Stable filename:** `minecraft_server_manager.pyw` (version noted in header comment).

---

## Requirements

- Windows 10/11
- Java (JDK 17+; tested with **JDK 21**). Update `JAVA_PATH` in the script.
- A Forge server folder created with **“Install server”** (this produces `libraries\...\forge\...\win_args.txt`).

Optional:
- **Tailscale** (or similar) if you’re letting friends connect privately.
- **Pillow** only if you want to generate a `.ico` from the PNG for a desktop shortcut icon.

---

## Quick start

1. **Place the manager in your server root**, e.g.
   ```
   C:\Users\<you>\Minecraft\IceAndFireServer\
   ```
   alongside `user_jvm_args.txt`, `libraries\`, `mods\`, etc.

2. Open `minecraft_server_manager.pyw` in a text editor and adjust:
   ```python
   JAVA_PATH = r"C:\Program Files\Java\jdk-21\bin\java.exe"
   XMS = "2G"   # initial heap
   XMX = "10G"  # max heap
   ```
   Optional splash image at: `assets\IceFireYinYangTransparent.png`

3. **Run it**:
   - Double-click the `.pyw`, or
   - Shortcut target:
     ```
     %SystemRoot%\pyw.exe "C:\...\minecraft_server_manager.pyw"
     ```
   The GUI opens and (by default) **auto-starts** the server.

> If you see *“Forge win_args.txt not found”*, run the **Forge installer** with **Install server** pointed at this folder.

---

## Buttons & panels

- **Start / Stop** – Launch/quit the server (clean stop).
- **Save All** – Flush world to disk.
- **Backup** – Runs `backup.bat` (refuses while server is running).
- **Make stop.flag** – Creates a `stop.flag`; the app detects it and issues `stop` (great for Task Scheduler).
- **Exit** – `save-all` → clean stop → small delay → closes GUI.
- **Whitelist** – Add/remove players and view the list (remove works offline by editing `whitelist.json` if needed).
- **Online Players** – Shows who’s on; auto-refreshes every 30 s; **Refresh** sends `list` on demand.
- **Command** – Send any server command (e.g., `whitelist on`, `op <name>`, `gamerule keepInventory true`).

---

## Backups

- Add your own `backup.bat` in the server root.
- The **Backup** button streams script output into the GUI log.
- The app **refuses to run backup while the server is running** (to avoid corrupt snapshots).

Example `backup.bat` (sample – adjust paths):
```bat
@echo off
set SRC=%CD%
set DST=D:\Backups\MinecraftBackups
if not exist "%DST%" mkdir "%DST%"
set TS=%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%_%TIME:~0,2%-%TIME:~3,2%
set TS=%TS: =0%
powershell -NoProfile -Command "Compress-Archive -Path '%SRC%\world' -DestinationPath '%DST%\world_%TS%.zip' -Force"
echo Done.
```

---

## Scheduling (start/stop daily)

`Windows_task_creator.ps1` builds the Windows Task Scheduler entries for you. Edit the times at the top of the script and run it from an elevated PowerShell prompt to register start tasks (launch `minecraft_server_manager.pyw`) and stop tasks (run `StopServer-And-Hibernate.ps1`).

Typical plan:

- **Start tasks** (wake PC) → run the GUI; auto-start kicks in.
- **Stop tasks** → drop `stop.flag`, wait for a clean exit, **hibernate** or **shutdown**.

Make sure **Power Options → Allow wake timers** is enabled.

If `StopServer-And-Hibernate.ps1` is blocked by antivirus, add it as an exception. Bitdefender steps:

1. Open Bitdefender.
2. Go to **Protection → Antivirus → Settings**.
3. In **Exceptions**, click **Add exception**.
4. Browse to `StopServer-And-Hibernate.ps1` and add it, keeping both *On-access* and *On-demand* scanning enabled.
5. Save. The script runs normally afterwards.

---

## Optional helper scripts

- `Windows_task_creator.ps1` – registers start/stop tasks in Windows Task Scheduler based on configurable times.
- `StopServer-And-Hibernate.ps1` – drops `stop.flag`, waits for exit, then hibernates (add to AV exceptions if flagged).
- `make_icon.py` – turns `assets\IceFireYinYangTransparent.png` → `assets\IceFireYinYang.ico` (requires Pillow).
- `create_shortcut.ps1` – creates a desktop shortcut that points to the `.pyw` and assigns the icon.

---

## Folder layout (suggested)

```
MinecraftServerManager/
├─ minecraft_server_manager.pyw
├─ StopServer-And-Hibernate.ps1
├─ make_icon.py                 # optional
├─ create_shortcut.ps1          # optional
├─ README.md
├─ .gitignore
├─ CHANGELOG.md
└─ assets/
   └─ IceFireYinYangTransparent.png  # optional splash/icon
```

> Do **not** commit your actual server (`world/`, `libraries/`, `mods/`, `whitelist.json`, etc.). Those are large and/or private.

---

## Troubleshooting

- **Java not found** – Update `JAVA_PATH`.
- **Forge args missing** – Re-run **Forge Installer → Install server** into this folder.
- **Firewall** – If using a 3rd-party firewall, allow Java for local LAN; for Tailscale, no inbound port-forwarding is needed.
- **Backup fails** – Stop the server first (the app enforces this on the Backup button).

---

## License

MIT License (see `LICENSE` in this repo).
