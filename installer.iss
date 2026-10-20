; Script generated for Inno Setup Compiler
; Boltools Desktop Suite - Production Installer

#define MyAppName "Boltools"
#define MyAppVersion "1.1.3"
#define MyAppPublisher "The SurfBoard"
#define MyAppURL "https://thesurfboard.in"
#define MyAppExeName "Boltools.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{5E9F8E41-C684-4866-9F0A-8C21F7715DA2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist_installer
OutputBaseFilename=Boltools_Setup
SetupIconFile=assets\boltools.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
RestartApplications=no
CloseApplicationsFilter=*.exe
UninstallDisplayIcon={app}\boltools.ico
UninstallDisplayName={#MyAppName} (Built by The SurfBoard)

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; Windows asks for admin once: registering the right-click menu package needs it.
Name: "rightclick"; Description: "Add ""Open with Boltools"" to the right-click menu"; GroupDescription: "File Explorer:"; MinVersion: 10.0.22000

[Files]
Source: "dist\Boltools\*"; DestDir: "{app}"; Excludes: "*.pdb,*.lib"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\boltools.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\boltools.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\boltools.ico"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -Command ""Add-AppxPackage -Path '{app}\BoltoolsMenu.msix' -ExternalLocation '{app}' -AllowUnsigned -ForceUpdateFromAnyVersion"""; Verb: "runas"; Flags: shellexec waituntilterminated runhidden; StatusMsg: "Adding Boltools to the right-click menu..."; Tasks: rightclick
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Removing a package for the current user needs no admin rights.
Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -Command ""Get-AppxPackage Boltools.ExplorerMenu | Remove-AppxPackage"""; Flags: runhidden waituntilterminated; RunOnceId: "RemoveBoltoolsMenu"
