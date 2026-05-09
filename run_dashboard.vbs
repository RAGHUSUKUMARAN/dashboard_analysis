Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "D:\NCCC_DASHBOARD\run_dashboard.bat" & Chr(34), 0
Set WshShell = Nothing