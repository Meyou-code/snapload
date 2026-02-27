[Setup]
AppId={{9F5C8A2E-6F7B-4D1A-9E45-123456789ABC}
AppName=SnapLoad
AppVersion=1.0.0
AppPublisher=SnapLoad
AppPublisherURL=https://github.com/meyou-code/snapload
AppSupportURL=https://github.com/meyou-code/snapload
AppUpdatesURL=https://github.com/meyou-code/snapload
DefaultDirName={autopf}\SnapLoad
DefaultGroupName=SnapLoad
OutputDir=.\installer
OutputBaseFilename=SnapLoad_Installer
SetupIconFile=..\assets\logo.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
CloseApplications=no
DisableProgramGroupPage=yes
DisableDirPage=yes


[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\SnapLoad\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\logo.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\logo.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\SnapLoad"; Filename: "{app}\SnapLoad.exe"; IconFileName: "{app}\assets\logo.ico"
Name: "{autodesktop}\SnapLoad"; Filename: "{app}\SnapLoad.exe"; IconFileName: "{app}\assets\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\SnapLoad.exe"; Description: "{cm:LaunchProgram,SnapLoad}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: dirifempty; Name: "{app}"
