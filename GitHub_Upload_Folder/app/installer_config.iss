[Setup]
AppName=Medication Lookup
AppVersion=1.0
; Install to LocalAppData to avoid Admin privileges and write-permission issues
DefaultDirName={localappdata}\MedicationLookup
DefaultGroupName=Medication Lookup
OutputBaseFilename=Install_MedicationLookup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
OutputDir=..\

[Files]
Source: "dist\MedicationLookup\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Medication Lookup"; Filename: "{app}\MedicationLookup.exe"
Name: "{userdesktop}\Medication Lookup"; Filename: "{app}\MedicationLookup.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"
