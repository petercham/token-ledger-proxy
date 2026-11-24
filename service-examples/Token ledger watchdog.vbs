' Token ledger - Windows logon auto-start (hidden window). Engine backends: Strata / Basalt.
'
' DO NOT copy this .vbs into the Startup folder - the Startup folder takes a
' SHORTCUT to this file only (Win+R -> shell:startup). This .vbs lives in
' service-examples/ inside the package; 'pkg' below resolves the package root
' one level up from the real .vbs path (WScript.ScriptFullName follows the
' shortcut target correctly), then launches gateway\ledger_watchdog.py.
' Copying the .vbs itself into the Startup folder breaks that anchor and the
' launch fails silently.
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
Dim shell, here, pkg, py, q, launchLine
here = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
' this .vbs lives in service-examples/ inside the package -> package root is one level up
pkg = Left(here, Len(here) - 1)
pkg = Left(pkg, InStrRev(pkg, "\"))
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = pkg
py = shell.ExpandEnvironmentStrings("%TOKEN_LEDGER_PYTHON%")
If py = "%TOKEN_LEDGER_PYTHON%" Or py = "" Then py = shell.ExpandEnvironmentStrings("%STRATA_PYTHON%")
If py = "%STRATA_PYTHON%" Or py = "" Then py = "python"
q = Chr(34)
launchLine = q & py & q & " " & q & pkg & "gateway\ledger_watchdog.py" & q & " --lock-wait 86400"
shell.Run launchLine, 0, False
