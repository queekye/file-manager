#define MyAppName "文件管理系统"
#define MyAppVersion "1.7.1"
#define MyAppPublisher "Kang Chen"
#define MyAppExeName "FileM.exe"

[Setup]
AppId={{8F7E4F1A-5C9E-4F1B-9E1A-9C9E4F1B9E1A}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\FileManager
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=FileManager_Setup
Compression=lzma
SolidCompression=yes
; SetupIconFile=resources\app.ico
PrivilegesRequired=admin

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; 
Name: "startupicon"; Description: "开机自动启动"; GroupDescription: "附加任务:";
Name: "quicklaunchicon"; Description: "创建快速启动栏图标"; GroupDescription: "附加任务:";

[Files]
; 主程序文件
Source: "dist\FileM\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
; README文件
Source: "README.html"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
; 添加右键菜单
Root: HKCR; Subkey: "Directory\Background\shell\FMConfig"; ValueType: string; ValueName: ""; ValueData: "文件管理系统配置"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Directory\Background\shell\FMConfig"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\resources\app.ico"
Root: HKCR; Subkey: "Directory\Background\shell\FMConfig\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --config-editor"

; 添加开机自启动注册表项
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "FileManager"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletekey; Tasks: startupicon

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\配置编辑器"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--config-editor"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon
Name: "{sendto}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\app.ico"

[Run]
; 安装完成后运行配置编辑器
Filename: "{app}\{#MyAppExeName}"; Parameters: "--config-editor"; Flags: postinstall runascurrentuser shellexec unchecked; Description: "运行配置编辑器"
; 安装完成后运行主程序
Filename: "{app}\{#MyAppExeName}"; Description: "立即启动 {#MyAppName}"; Flags: postinstall nowait skipifsilent
; 安装完成后打开README
Filename: "{app}\README.html"; Flags: postinstall shellexec; Description: "查看说明文档"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\resources"
Type: filesandordirs; Name: "{app}\_internal"
Type: dirifempty; Name: "{app}"

[InstallDelete]
; 清理旧版本文件
Type: files; Name: "{app}\*.old"
Type: filesandordirs; Name: "{app}\old_version" 