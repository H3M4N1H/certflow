[Setup]
AppName=CertFlow
AppVersion=2.0.0
DefaultDirName={localappdata}\Programs\CertFlow
DefaultGroupName=CertFlow
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=CertFlow-Windows-Setup
SetupIconFile=certflow.ico
UninstallDisplayIcon={app}\CertFlow.exe
Compression=lzma2
SolidCompression=yes
[Files]
Source: "..\dist\CertFlow\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\CertFlow"; Filename: "{app}\CertFlow.exe"
Name: "{autodesktop}\CertFlow"; Filename: "{app}\CertFlow.exe"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"
[Run]
Filename: "{app}\CertFlow.exe"; Description: "Launch CertFlow"; Flags: postinstall nowait skipifsilent
