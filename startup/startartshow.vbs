Const Title = "Artshow Keeper"
Const ArtShowFolder = "\\ArtShow\\"
Const CommonAppData = &H23&  ' the second & denotes a long integer '
Const WshRunning = 0

Sub Log(message)
    If WScript.Arguments.Count > 0 Then
        If WScript.Arguments(0) = "TESTRUN" Then
            WScript.Echo message
            Exit Sub
        End If
    End If
    
    Const ForAppending = 8
    
    On Error Resume Next
    Set commonAppDataFolder = app.Namespace(CommonAppData).Self
    Set logFile = fso.OpenTextFile( _
        commonAppDataFolder.Path & ArtShowFolder & "startupartshow.log", _
        ForAppending, True)
    logFile.WriteLine Date & " " & Time & " " & message
    logFile.Close
End Sub

Function LockServer(app, fso)
    On Error Resume Next
    Set commonAppDataFolder = app.Namespace(CommonAppData).Self
    Set file = fso.CreateTextFile(commonAppDataFolder.Path & ArtShowFolder & "app.lock", True, False)
    If Err.Number <> 0 Then
        Log "LockServer: Error " & Err.Description
        Err.Clear
        Set LockServer = Nothing
        Exit Function
    End If

    file.WriteLine "locked " & Date & " " & Time
    Set LockServer = file
End Function

Sub UnlockServer(app, fso, lock)
    If Not lock Is Nothing Then
        lock.WriteLine "unlocked " & Date & " " & Time
        lock.Close
        Set lock = Nothing
    End If
End Sub 

Function GetScriptPath(fso)
    ' Returns a path to the executed script.
    Set file = fso.GetFile(Wscript.ScriptFullName)
    GetScriptPath = fso.GetParentFolderName(file) & "\"
End Function

Function StartProcess(shell, command, validExitCode)
    Set scriptExec = shell.Exec(command)
    WScript.Sleep 200
    If Not scriptExec.Status = WshRunning Then
        If scriptExec.ExitCode <> validExitCode Then
            Log "StartProcess: Cmd " & command
            Log "StartProcess: Process did not start with an return value " & scriptExec.ExitCode
            Log "StartProcess: Process stderr: " & scriptExec.StdErr.ReadAll
            Set scriptExec = Nothing
        End If
    End If
    Set StartProcess = scriptExec
End Function

Function StartServer(shell, fso)
    ' Starts a server.
    ' Returns an instance of object WshScriptExec.
    pythonCmd = shell.RegRead("HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\python.exe\")
    scriptCmd = GetScriptPath(fso) & "..\app\main.py"

    Log "StartServer: Python cmd = " & pythonCmd
    Log "StartServer: Script cmd = " & scriptCmd
    
    Set StartServer = StartProcess(shell, _
            "cmd /C " & _
                "title " & Title & " & " & _
                """" & pythonCmd & """ """ & scriptCmd & """", _
            0)
            
    WScript.Sleep 1000            
End Function

Function StartClient(shell, fso)
    firefoxCmd = shell.RegRead("HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe\")

    Log "StartClient: Firefox cmd = " & firefoxCmd

    Set clientExec = StartProcess(shell, _
            """" & firefoxCmd & """ -new-window ""127.0.0.1:5000""", _
            1)
    StartClient = Not clientExec Is Nothing
End Function

Sub WaitForServer(serverExec)
    Log "WaitForServer: Waiting for a server"
    Do While serverExec.Status = WshRunning
         WScript.Sleep 1000
    Loop

    Log "WaitForServer: Server exited with exit code " & serverExec.ExitCode
    If serverExec.ExitCode <> 0 Then
        Log "WaitForServer: stderr: " & serverExec.StdErr.ReadAll    
    End If
End Sub

Sub Main(shell, app, fso)
    ' Start server
    Set lock = LockServer(app, fso)
    Set serverExec = Nothing
    If lock Is Nothing Then
        Log "Main: Server is already running."
    Else
        Set serverExec = StartServer(shell, fso)
        If serverExec Is Nothing Then
            Log "Main: Server did not start"

            UnlockServer app, fso, lock
            Set lock = Nothing

            MsgBox "Application failed to start.", vbOKOnly + vbCritical, Title
            Exit Sub
        End If
    End If

    ' Start client
    Log "Main: Starting client"
    If Not StartClient(shell, fso) Then
        MsgBox "Application client failed to start.", vbOKOnly + vbCritical, Title
    End If
    
    ' Wait for server (if any)
    If Not serverExec Is Nothing Then
        WaitForServer(serverExec)
    End If

    ' Cleanup
    UnlockServer app, fso, lock
End Sub

' Initialize
Set shell = CreateObject("WScript.Shell")
Set app = CreateObject("Shell.Application")
Set fso = CreateObject("Scripting.FileSystemObject")

Main shell, app, fso

