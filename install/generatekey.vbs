Const msiDoActionStatusSuccess = 1
Const msiDoActionStatusUserExit = 2
Const msiDoActionStatusFailure = 3

Function GenerateKeyLength(length)
    Randomize()
    Const digits = "0123456789ABCDEF"
    key = ""
    count = 0
    Do While count < length
        number = Int(Rnd * 255)
        key = key & _
            Mid(digits, ((number / 16) Mod 16) + 1, 1) & _
            Mid(digits, (number Mod 16) + 1, 1)
        count = count + 1
    Loop
    GenerateKeyLength = key
End Function

Function GenerateKey
    Session.Property("SECRET_KEY") = GenerateKeyLength(24)
    GenerateKey = msiDoActionStatusSuccess
End Function

' Test
If Not IsEmpty(WScript) Then
    key = GenerateKeyLength(24)
    WScript.Echo(key)
    If Len(key) <> 48 Then
        WScript.Echo("Key length (" & Len(key) & ") is not 48.")
    End If
End If
