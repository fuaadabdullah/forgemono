# Unity Hub: "Not Enough Storage" Error — Troubleshooting Guide

Summary

This guide lists common causes and fixes for Unity Hub / Unity Editor installations that report a “not enough storage” error. It focuses on practical diagnostics and step-by-step fixes for Windows and macOS users, with commands and log locations to help you collect details for support requests.

Why it happens (common reasons)

- Temp folder / download staging area is on a low-space drive.
- Unity Hub validation may check the drive where Hub is installed, even if Editor installs elsewhere.
- Optional modules (Docs, Language packs) sometimes report 0 bytes and fail.
- Permissions prevent write operations to the staging or install location.
- Network issues or corrupted download cause an install failure reported as a space issue.
- Target folder is a network, removable, or non-standard filesystem that prevents proper writes.

Quick Checklist (what to gather first)

- OS & version (Windows/macOS + version)
- Unity Hub version
- Unity Editor version you tried to install
- Exact error message and a screenshot (if helpful)
- Path where you’re installing the Editor and where Unity Hub is installed
- Free space on relevant drives (Hub drive, target drive, and OS drive)
- Any logs from Unity Hub and installation steps

Diagnostic steps and fixes

1. Check disk space

macOS / Linux (Terminal):

- Check overall free space:

  df -h

- Check a specific path/drive:

  df -h /Volumes/MyDrive

- Find largest directories to free space if needed:

  sudo du -sh /* | sort -hr | head -n 25

Windows (PowerShell):

- Check drive space:

  Get-PSDrive -PSProvider FileSystem | Format-Table -AutoSize

- Check free space of the C: drive or target drive

1. Check the Download Staging / Temp folder

Why: Unity Hub often downloads installation files to a staging folder (often the system TEMP). If that folder is on a small drive (e.g., C:), you’ll get a storage error.

Windows

- TEMP/TMP variables are commonly at: `%TEMP%` and `%TMP%`.
- Show their current values in PowerShell:

  echo $env:TEMP
  echo $env:TMP

- To change them for the current user (replace D:\Temp with valid path):

  [Environment]::SetEnvironmentVariable("TEMP", "D:\Temp", "User")
  [Environment]::SetEnvironmentVariable("TMP", "D:\Temp", "User")

  (Log out and back in or reboot for GUI apps to pick the new values.)

macOS

- GUI apps don’t always respect shell variables, but you can test Hub with a temporary TMPDIR:

  TMPDIR=/Volumes/BigDrive/tmp open -a "Unity Hub"

- For GUI changes you may use launchctl (not always recommended):

  launchctl setenv TMPDIR /Volumes/BigDrive/tmp

If changing temp is not practical, ensure the drive where the TEMP folder sits has enough free space, or install Hub on the drive where you want the Editor installed.

1. Unity Hub disk path / bug

If Hub is installed on a small drive, it may validate or use that drive during downloads. Workarounds:

- Install Unity Hub and the Editor on the same drive where you have enough space.
- If they must be on separate drives, move Hub to the larger drive to avoid staging issues.

1. Optional modules (Docs, Language Packs)

- Deselect optional modules like Documentation and Language packs during Editor install.
- Install the core Editor first, then add modules later.

1. Permissions and admin rights

- Windows: Run Unity Hub as Administrator while installing.
- macOS: Ensure you have write permission for the install target. Consider running the installer with elevated permissions via sudo or an admin account.

1. Network / download integrity

- Re-download the Editor or try installing from the Unity Download Archive instead of through Hub.
- Sometimes an intermittent network causes corrupt downloads that report space errors.

1. Remove partial installs & caches

- Remove partially downloaded editor files and Hub cache locations.
- Windows (common cache paths):
  - `%LOCALAPPDATA%\Unity\cache`
  - `%USERPROFILE%\AppData\Roaming\UnityHub\logs`
- macOS (common cache paths):
  - `~/Library/Application Support/Unity/`
  - `~/Library/Application Support/UnityHub/`
  - `~/Library/Logs/Unity` or `~/Library/Logs/UnityHub`

1. Check Unity Hub logs

- Unity Hub logs often reveal the precise step that’s failing. Check these locations:

macOS:

- `~/Library/Application Support/UnityHub/logs/`
- Console.app (search for Unity or Unity Hub)

Windows:

- `%APPDATA%\UnityHub\logs\`
- `%LOCALAPPDATA%\Unity\logs\`

Linux (common path):

- `~/.config/UnityHub/logs/`

1. If you suspect a Hub bug

- Update to the latest Unity Hub (or try a known stable version).
- Try installing the Editor from the Unity Download Archive (direct install).
- File a bug report in the Unity Issue Tracker and attach logs, environment, and steps to reproduce.

Helpful Unity links:

- Unity Download Archive: [Unity Download Archive](https://unity.com/releases/editor/archive)
- Unity Issue Tracker: [Unity Issue Tracker](https://issuetracker.unity.com)

Automated log collector (scripts)

To make this easier, I added two scripts to collect logs & system info:

- Mac/Linux: `tools/scripts/collect_unityhub_report.sh`
- Windows (PowerShell): `tools/scripts/collect_unityhub_report.ps1`

Usage (macOS/Linux):

  chmod +x tools/scripts/collect_unityhub_report.sh
  ./tools/scripts/collect_unityhub_report.sh

Usage (Windows - PowerShell):

  .\tools\scripts\collect_unityhub_report.ps1

The scripts collect OS info, disk usage, environment variables (TMP/TEMP/TMPDIR), Unity Hub logs, Editor logs where available and zip them for easy sharing.

If you'd like, I can add a bug template or pre-filled report example that includes the report output.

Last updated: 2025-11-19

---

