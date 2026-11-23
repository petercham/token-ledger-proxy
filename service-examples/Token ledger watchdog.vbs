' Token ledger - Windows logon auto-start (hidden window). Engine backends: Strata / Basalt.
'
' DO NOT copy this .vbs into the Startup folder. Leave it in the package
' directory (the watchdog now lives in the gateway/ subdirectory), and put a SHORTCUT to this file into
' the Startup folder (Win+R -> open the Startup folder). WScript.ScriptFullName
' resolves to the real .vbs path even when launched through a shortcut, so
' 'here' below stays the package directory. Copying the .vbs itself into the
' Startup folder makes 'here' point there instead: the watchdog is never
' found and the launch fails silently.
'
' It starts ONLY the watchdog; the watchdog starts the ledger proxy.
' --lock-wait 86400 keeps this logon copy waiting as a hot standby when an
' older watchdog still owns the single-instance lock, then takes over the
' moment the old one exits (zero-gap handoff).
'
' Python: by default this uses 'python' from PATH. If Python is not on PATH,
' set TOKEN_LEDGER_PYTHON to the full path of python.exe (a user environment
' variable works; the legacy name STRATA_PYTHON still works as fallback).
' Never use pythonw.exe: the script prints and pythonw has no console.
Option Explicit
Dim shell, here, py, q, launchLine
here = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = here
py = shell.ExpandEnvironmentStrings("%TOKEN_LEDGER_PYTHON%")
If py = "%TOKEN_LEDGER_PYTHON%" Or py = "" Then py = shell.ExpandEnvironmentStrings("%STRATA_PYTHON%")
If py = "%STRATA_PYTHON%" Or py = "" Then py = "python"
q = Chr(34)
launchLine = q & py & q & " " & q & here & "gateway\ledger_watchdog.py" & q & " --lock-wait 86400"
shell.Run launchLine, 0, False
