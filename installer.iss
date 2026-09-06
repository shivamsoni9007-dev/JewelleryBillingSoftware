#define MyAppName "Shree Ram Kumar Jewellers"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Shree Ram Kumar Jewellers"
#define MyAppExeName "Shree Ram Kumar Jewellers.exe"

[Setup]
AppId={{B9148A32-BC4C-4C79-9B7A-1D04F7AFA122}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Shree Ram Kumar Jewellers
DefaultGroupName=Shree Ram Kumar Jewellers
SetupIconFile=shop-logo.ico
DisableProgramGroupPage=yes

PrivilegesRequired=lowest

OutputDir=installer
OutputBaseFilename=Shree Ram Kumar Jewellers Setup

Compression=lzma
SolidCompression=yes

WizardStyle=modern

UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible


[Languages]

Name: "english"; \
MessagesFile: "compiler:Default.isl"


[Tasks]

Name: "desktopicon"; \
Description: "Create a desktop shortcut"; \
GroupDescription: "Additional shortcuts:"; \
Flags: checkedonce


[Files]

Source: "dist\Shree Ram Kumar Jewellers.exe"; \
DestDir: "{app}"; \
Flags: ignoreversion


[Icons]

[Icons]
Name: "{autoprograms}\Shree Ram Kumar Jewellers"; \
Filename: "{app}\Shree Ram Kumar Jewellers.exe"; \
IconFilename: "{app}\Shree Ram Kumar Jewellers.exe"

Name: "{autodesktop}\Shree Ram Kumar Jewellers"; \
Filename: "{app}\Shree Ram Kumar Jewellers.exe"; \
IconFilename: "{app}\Shree Ram Kumar Jewellers.exe"; \
Tasks: desktopicon


[Run]

Filename: "{app}\Shree Ram Kumar Jewellers.exe"; \
Description: "Launch Shree Ram Kumar Jewellers"; \
Flags: nowait postinstall skipifsilent