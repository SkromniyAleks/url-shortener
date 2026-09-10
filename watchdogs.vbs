' Watchdog: hidden background process.
' Waits until the runner window process (parent cmd.exe) dies,
' then stops Docker Compose services. Logs actions to watchdog.log.
Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = WScript.Arguments(0)
If Right(folder, 1) = "\" Then folder = Left(folder, Len(folder) - 1)
logPath = folder & "\watchdog.log"
Sub Log(msg)
    Set f = fso.OpenTextFile(logPath, 8, True)
    f.WriteLine Now & " " & msg
    f.Close
End Sub
Log "launched: " & WScript.ScriptFullName
' Find own process by own script name (case-insensitive), take newest PID
needle = LCase(WScript.ScriptName)
myPid = 0
For Each p In wmi.ExecQuery("Select * From Win32_Process Where Name='wscript.exe'")
    If Not IsNull(p.CommandLine) Then
        If InStr(LCase(p.CommandLine), needle) > 0 Then
            If p.ProcessId > myPid Then myPid = p.ProcessId
        End If
    End If
Next
If myPid = 0 Then
    Log "ERROR: own process not found"
    WScript.Quit
End If
parentPid = wmi.Get("Win32_Process.Handle='" & myPid & "'").ParentProcessId
Log "started: myPid=" & myPid & " parentPid=" & parentPid
Do While True
    WScript.Sleep 1000
    If wmi.ExecQuery("Select * From Win32_Process Where ProcessId=" & parentPid).Count = 0 Then
        Log "parent window closed -> stopping services"
        Exit Do
    End If
Loop
Set sh = CreateObject("WScript.Shell")
sh.Run "cmd /c cd /d """ & folder & """ && docker compose down >> """ & logPath & """ 2>&1", 0, True
Log "docker compose down finished"