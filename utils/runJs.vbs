myScript = Wscript.Arguments.Item(0)
myPort = WScript.Arguments.Item(1)
myVer = WScript.Arguments.Item(2)
Set myInDesign = CreateObject("InDesign.Application"&"."&myVer)
Set myFileSystemObject = CreateObject("Scripting.FileSystemObject")
Set myFile = myFileSystemObject.GetFile(myScript) 
Set objShell = CreateObject("Wscript.Shell")
strPath = Wscript.ScriptFullName
Set objFile = myFileSystemObject.GetFile(strPath)
strFolder = myFileSystemObject.GetParentFolderName(objFile) 
runFile = myFileSystemObject.GetFile(strFolder & "/jsRunner.jsx")
On Error Resume Next
Dim r
r = myInDesign.DoScript(runFile, 1246973031, Array(myFile,myPort))
If Err.Number<>0 Then
	WScript.Echo "___"
	WScript.Echo  Err.Description
	WScript.Echo  Err.Number
End IF
