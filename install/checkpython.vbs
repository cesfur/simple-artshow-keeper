Const msiDoActionStatusSuccess = 1
Const msiDoActionStatusUserExit = 2
Const msiDoActionStatusFailure = 3

Const pyFatalFailure = -1
Const pyResultSuccess = 0
Const pyResultFailure = 128
Const pyResultModuleNotFound = 129
Const pyResultVersionNotFound = 130

Dim testProperties

Sub TestAssert(boolExpr, message)
    If Not boolExpr Then
        Err.Raise vbObjectError + 99999, , message
    End If
End Sub

Sub TestAssertValue(value, expectedValue, message)
    If value <> expectedValue Then
        Err.Raise vbObjectError + 99999, , _
                "[Expected " & expectedValue & ", Received " & value & "]: " & message
    End If
End Sub

Function IsTestRun
    If IsEmpty(WScript) Then
        IsTestRun = False
    ElseIf WScript.Arguments.Count <= 0 Then
        IsTestRun = False
    Else
        IsTestRun = (WScript.Arguments(0)="TESTRUN")
    End If
End Function

Function GetScriptPath
    Set wsShell = Wscript.CreateObject("Wscript.Shell")

    Set fso = CreateObject("Scripting.FileSystemObject")
    Set file = fso.GetFile(Wscript.ScriptFullName)
    GetScriptPath = fso.GetParentFolderName(file) & "\"

    Set file = Nothing
    Set fso = Nothing
    Set wsShell = Nothing
End Function

Function GetMsiProperty(name)
    If IsTestRun Then
        TestAssert testProperties.Exists(name), "Property " & name & " not found"
        GetMsiProperty = testProperties.Item(name)
    Else
        customActionData = Split(Session.Property("CustomActionData"), ";")
        For Each nameValuePair In customActionData
            pair = Split(nameValuePair, "=")
            If pair(0) = name Then
                GetMsiProperty = pair(1)
                Exit Function
            End If
        Next
        
        GetMsiProperty = ""        
    End If
End Function

Sub SetMsiProperty(name, value)
    If IsTestRun Then
        If testProperties.Exists(name) Then
            testProperties.Item(name) = value
        Else
            testProperties.Add name, value
        End If
    Else
        'Not supported
    End If
End Sub

Sub ShowMsiError(message)
    If IsTestRun Then
        MsgBox(message)
    Else
        Const msiMessageTypeError = &H01000000
        Set rec = Session.Installer.CreateRecord(1)
        rec.StringData(0) = message
        Session.Message msiMessageTypeError, rec
        Set rec = Nothing
    End If
End Sub

Sub UpdateMsiProgress:
    If IsTestRun Then
        WScript.Echo "Progress update..."
    Else
        Const msiMessageTypeProgress = &H0A000000
        Set rec = Session.Installer.CreateRecord(2)
        rec.IntegerData(0) = 3
        rec.IntegerData(1) = 1
        Session.Message msiMessageTypeProgress, rec
    End If
End Sub

Sub LogMsiMessage(message)
    If IsTestRun Then
        WScript.Echo message
    Else
        Const msiMessageTypeInfo = &H04000000
        Set rec = Session.Installer.CreateRecord(1)
        rec.StringData(0) = message
        Session.Message msiMessageTypeInfo, rec
    End If
End Sub

Function CheckPython
    On Error Resume Next

    Set wsShell = CreateObject("WScript.Shell")
    path = wsShell.RegRead("HKLM\SOFTWARE\Python\PythonCore\" & _
            GetMsiProperty("RequiredPythonVersion") & _
            "\InstallPath\")

    If Err.Number <> 0 Then
        CheckPython = msiDoActionStatusFailure
        Err.Clear
    Else
        SetMsiProperty "PythonPath", path
        CheckPython = msiDoActionStatusSuccess
    End If        

    Set wsShell = Nothing
End Function

Function IsPythonPackage(moduleName, moduleVersion)
    On Error Resume Next
    
    cmd = GetMsiProperty("PythonPath") & _
            "python.exe """ & GetMsiProperty("InstallHelperDir") & "checkversion.py"" " & _
            moduleName & " " & moduleVersion

    Set wsShell = CreateObject("WScript.Shell")
    returnCode = wsShell.Run(cmd, 0, True)
    If Err.Number <> 0 Then
        LogMsiMessage "Running cmd '" & cmd & "' failed with an error code " & Err.Number
        returnCode = pyFatalFailure
        Err.Clear
    End If
    Set wsShell = Nothing
    
    If Not returnCode=pyResultSuccess Then
        LogMsiMessage "Running cmd '" & cmd & "' returned " & returnCode
    End If
    IsPythonPackage = returnCode
End Function

Sub UnZip(srcZip, targetFolder):
    Set shell = CreateObject("Shell.Application")
    Set source = shell.NameSpace(srcZip).Items()
    Set target = shell.NameSpace(targetFolder)
    options = 4 + 512 + 1024
    target.CopyHere source, options
    LogMsiMessage "Unzipped '" & srcZip & "' to a folder '" & targetFolder & "'"
End Sub
    
Sub CreateFolder(folderPath):
    Set fso = CreateObject("Scripting.FileSystemObject")
    If Not fso.FolderExists(folderPath) Then
        fso.CreateFolder folderPath
    End If
End Sub    
    
Sub DeleteFolder(folderPath):
    Set fso = CreateObject("Scripting.FileSystemObject")
    fso.DeleteFile folderPath & "\*", True
    fso.DeleteFolder folderPath & "\*", True
    fso.DeleteFolder folderPath, True
End Sub    
    
Function RunSetup(extractedModuleFolderPath):
    On Error Resume Next

    ' We need to change the current folder because 
    ' some packages (e.g. itsdangerous, markupsafe) are not able to run
    ' if the current folder does not match the folder of the unzipped package.
    cmd = "cmd /C CD """ & extractedModuleFolderPath & """ & " &_    
            GetMsiProperty("PythonPath") & "python.exe setup.py install"

    Set wsShell = CreateObject("WScript.Shell")
    returnCode = wsShell.Run(cmd, 0, True)
    If Err.Number <> 0 Then
        LogMsiMessage "Running cmd '" & cmd & "' failed with an error code " & Err.Number
        RunSetup = False
        Err.Clear
    Else        
        LogMsiMessage "Cmd '" & cmd & "' has been run successfully."
        RunSetup = True
    End If
End Function

Function InstallPythonPackage(packageName, packageVersion, requestVersion):
    checkedVersion = packageVersion
    If Not requestVersion Then
        checkedVersion = "0"
    End If
        
    If Not IsPythonPackage(packageName, checkedVersion) = pyResultSuccess Then
        LogMsiMessage "Installing " & packageName & " (version: " & packageVersion & ")"

        packageFullName = packageName & "-" & packageVersion 
        tempPath = GetMsiProperty("TempFolder") & "ArtShowTemp"
        
        CreateFolder tempPath
        UpdateMsiProgress

        UnZip GetMsiProperty("InstallDependenciesDir") & packageFullName & ".zip", tempPath
        UpdateMsiProgress
        
        If Not RunSetup(tempPath & "\" & packageFullName) Then
            LogMsiMessage "Setup of a package " & packageName & " (version: " & packageVersion & ") failed."
            InstallPythonPackage = False
            Exit Function
        End If
        UpdateMsiProgress
        
        If Not(IsPythonPackage(packageName, checkedVersion)=pyResultSuccess) Then
            LogMsiMessage "Package " & packageName & " (version: " & packageVersion & ") has failed installing."
            InstallPythonPackage = False
            Exit Function
        End If 
        UpdateMsiProgress

        InstallPythonPackage = True
        
        DeleteFolder tempPath
        UpdateMsiProgress
    Else
        LogMsiMessage "Package " & packageName & " (version: " & packageVersion & " or newer) is already installed"
        InstallPythonPackage = True
        UpdateMsiProgress    
    End If

End Function

Function InstallAllPythonPackages:

    If Not InstallPythonPackage("setuptools", "3.4.1", True) Then
        InstallAllPythonPackages = msiDoActionStatusFailure
        Exit Function
    End If

    If Not InstallPythonPackage("itsdangerous", "0.24", False) Then
        InstallAllPythonPackages = msiDoActionStatusFailure
        Exit Function
    End If

    If Not InstallPythonPackage("werkzeug", "0.9.4", True) Then
        InstallAllPythonPackages = msiDoActionStatusFailure
        Exit Function
    End If
    
    If Not InstallPythonPackage("markupsafe", "0.19", False) Then
        InstallAllPythonPackages = msiDoActionStatusFailure
        Exit Function
    End If

    If Not InstallPythonPackage("jinja2", "2.7.2", True) Then
        InstallAllPythonPackages = msiDoActionStatusFailure
        Exit Function
    End If

    If Not InstallPythonPackage("flask", "0.10", True) Then
        InstallAllPythonPackages = msiDoActionStatusFailure
        Exit Function
    End If
End Function

If IsTestRun Then
    Set testProperties = CreateObject("Scripting.Dictionary")

    SetMsiProperty "InstallHelperDir", GetScriptPath()    
    SetMsiProperty "RequiredPythonVersion", "50.99"
    TestAssert CheckPython()=msiDoActionStatusFailure, "CheckPython is not Failure"
    SetMsiProperty "RequiredPythonVersion", "3.3"
    TestAssert CheckPython()=msiDoActionStatusSuccess, "CheckPython is not Success"
    TestAssert GetMsiProperty("PythonPath")="C:\Python33\", "Python path is not correct"

    TestAssertValue IsPythonPackage("flask", "0.10"), pyResultSuccess, "Flask not found"
    TestAssertValue IsPythonPackage("flask", "0.1.2"), pyResultSuccess, "Request on having lower version not matched"
    TestAssertValue IsPythonPackage("flask", "0.50.2"), pyResultVersionNotFound, "Request on having higher version matched"
    TestAssertValue IsPythonPackage("fflask", "0.10.1"), pyResultModuleNotFound, "Non-existing module"
    TestAssertValue IsPythonPackage("setuptools", "3.4.1"), pyResultSuccess, "Setuptools not found"
    
    SetMsiProperty "InstallDependenciesDir", GetScriptPath() & "\dependencies\"
    SetMsiProperty "TempFolder", GetScriptPath() & "\temp\"
    TestAssert InstallPythonPackage("setuptools", "3.4.1", True), "Setuptools installation failed"
    TestAssert InstallPythonPackage("itsdangerous", "0.24", False), "Setuptools installation failed"
End If
