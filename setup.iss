; Script dong goi cai dat cho AI Generate Tool Pro (Chuyen nghiep, kem Icon Zbiz)
[Setup]
AppName=ZBizWorld AI Generate Pro
AppVersion=1.7.4
AppPublisher=ZBizWorld
; Cai dat vao thu muc AppData cua User (Giong VS Code, Discord, Minecraft)
DefaultDirName={localappdata}\Programs\AI_Generate_Tool_Pro
DefaultGroupName=AI Generate Tool Pro
UninstallDisplayIcon={app}\zbizworld.exe
Compression=lzma2/max
SolidCompression=yes
OutputDir=D:\all my code stuff\Ai-new
OutputBaseFilename=Setup_AI_Generate_Tool_Pro_v2
; Chay o quyen Admin de khoi dong duoc launcher
PrivilegesRequired=admin
; Thiet lap Icon cho file Setup cai dat
SetupIconFile=D:\all my code stuff\Ai-new\AI_Generate_Tool\Zbiz.ico
WizardImageFile=setup_banner.bmp
WizardSmallImageFile=setup_logo.bmp
WizardResizable=yes

[InstallDelete]
; Xoa sach se thu muc storage cu truoc khi ghi de file moi (Xoa sach du an va license cu)
Type: filesandordirs; Name: "{app}\storage"; Check: IsCleanInstall

[Files]
; Copy icon and launcher to "{app}" (clean root folder)
Source: "D:\all my code stuff\Ai-new\AI_Generate_Tool\Zbiz.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\all my code stuff\Ai-new\AI_Generate_Tool\zbizworld.exe"; DestDir: "{app}"; Flags: ignoreversion

; Copy the deep backend files and DLLs to "{app}\storage\runtime\bin"
Source: "D:\all my code stuff\Ai-new\AI_Generate_Tool\storage\runtime\bin\*"; DestDir: "{app}\storage\runtime\bin"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.bak,*.tmp,*.log,settings.json.enc,__pycache__,.pytest_cache,app_chrome_profile,chrome_profiles,logs,projects"

; Copy simulated/initial config files (expired license testing config) to "{app}\storage\config"
Source: "D:\all my code stuff\Ai-new\AI_Generate_Tool\storage\config\*"; DestDir: "{app}\storage\config"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.enc,*.lic"

; Copy pre-downloaded Stealth Chromium to "{app}\storage\cloakbrowser" for instant offline launch (Commented out to load from GitHub)
; Source: "C:\Users\delmu\.cloakbrowser\*"; DestDir: "{app}\storage\cloakbrowser"; Flags: ignoreversion recursesubdirs createallsubdirs

; Copy bo cai dat Microsoft Edge WebView2 Setup vao folder tam thoi va tu dong xoa sau khi cai xong
Source: "D:\all my code stuff\Ai-new\AI_Generate_Tool\MicrosoftEdgeWebview2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

; Copy bo cai dat Microsoft Visual C++ Redistributable vao folder tam thoi va tu dong xoa sau khi cai xong
Source: "D:\all my code stuff\Ai-new\AI_Generate_Tool\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
; Tao shortcut ngoai Desktop kem Icon Zbiz
Name: "{userdesktop}\ZBizWorld AI Generate"; Filename: "{app}\zbizworld.exe"; WorkingDir: "{app}"; IconFilename: "{app}\Zbiz.ico"
; Tao shortcut trong Start Menu kem Icon Zbiz
Name: "{userprograms}\ZBizWorld AI Generate"; Filename: "{app}\zbizworld.exe"; WorkingDir: "{app}"; IconFilename: "{app}\Zbiz.ico"

[Run]
; Cai dat Microsoft Visual C++ Redistributable neu may cua khach chua co truoc khi khoi dong ung dung
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/quiet /norestart"; StatusMsg: "Dang tu dong tai va cai dat Microsoft Visual C++ Redistributable..."; Check: not IsVCRedistInstalled

; Cai dat Microsoft Edge WebView2 Runtime neu may cua khach chua co truoc khi khoi dong ung dung
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Dang tu dong tai va cai dat Microsoft Edge WebView2 Runtime..."; Check: not IsWebView2Installed

; Giai nen trinh duyet Stealth Chromium neu co tai tu GitHub ve
Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -Command ""Expand-Archive -Path '{tmp}\cloakbrowser.zip' -DestinationPath '{app}\storage' -Force"""; StatusMsg: "Dang giai nen trinh duyet Stealth Chromium..."; Flags: runhidden; Check: FileExists(ExpandConstant('{tmp}\cloakbrowser.zip'))

; Giai nen thanh phan he thong backend va dll tu GitHub ve
Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -Command ""Expand-Archive -Path '{tmp}\backend_runtime.zip' -DestinationPath '{app}\storage\runtime' -Force"""; StatusMsg: "Dang giai nen cac thanh phan he thong..."; Flags: runhidden; Check: FileExists(ExpandConstant('{tmp}\backend_runtime.zip'))

; Whitelist thu muc cai dat vao Windows Defender de tranh bi quet nham hoac chan tuong lai
Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -Command ""Add-MpPreference -ExclusionPath '{app}'"""; StatusMsg: "Dang cau hinh danh sach tin cay Windows Defender..."; Flags: runhidden

; Mo tuong lua cho cac executable va port 9778 de tranh bi chan ket noi local
Filename: "netsh.exe"; Parameters: "advfirewall firewall add rule name=""ZBizWorld AI Generate Backend"" dir=in action=allow program=""{app}\storage\runtime\bin\sys_helper.exe"" enable=yes"; StatusMsg: "Dang thiet lap quy tac tuong lua..."; Flags: runhidden
Filename: "netsh.exe"; Parameters: "advfirewall firewall add rule name=""ZBizWorld AI Generate Launcher"" dir=in action=allow program=""{app}\zbizworld.exe"" enable=yes"; StatusMsg: "Dang thiet lap quy tac tuong lua..."; Flags: runhidden
Filename: "netsh.exe"; Parameters: "advfirewall firewall add rule name=""ZBizWorld Port 9778"" dir=in action=allow protocol=TCP localport=9778 enable=yes"; StatusMsg: "Dang thiet lap quy tac tuong lua..."; Flags: runhidden

; Khoi dong app sau khi cai xong bang ShellExecute de tranh loi Code 740
Filename: "{app}\zbizworld.exe"; Description: "Khoi dong ZBizWorld AI Generate ngay"; Flags: postinstall nowait skipifsilent shellexec

[UninstallDelete]
; Xoa sach storage (du lieu runtime cua app)
Type: filesandordirs; Name: "{app}\storage"
; Xoa sach thu muc chrome_profiles neu con ton tai
Type: filesandordirs; Name: "{app}\chrome_profiles"
; Xoa sach backend config
Type: filesandordirs; Name: "{app}\backend"

[Code]
// Kiem tra xem Microsoft Visual C++ Redistributable 2015-2022 da duoc cai dat chua
function IsVCRedistInstalled(): Boolean;
var
  Installed: Cardinal;
begin
  Result := RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) or
            RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed);
  if Result and (Installed = 1) then
    Result := True
  else
    Result := False;
end;

// Kiem tra xem Microsoft Edge WebView2 Runtime da duoc cai dat tren may chua
function IsWebView2Installed(): Boolean;
var
  Version: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8ABB-7D3E50F8FC44}', 'pv', Version) or
            RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8ABB-7D3E50F8FC44}', 'pv', Version) or
            RegQueryStringValue(HKLM64, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8ABB-7D3E50F8FC44}', 'pv', Version);
  if Result and (Version <> '0.0.0.0') and (Version <> '') then
    Result := True
  else
    Result := False;
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  { Kill sys_helper.exe neu dang chay }
  Exec('taskkill.exe', '/F /IM sys_helper.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  { Kill zbizworld.exe neu dang chay }
  Exec('taskkill.exe', '/F /IM zbizworld.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  { Cho 1 giay de Windows release lock tren file }
  Sleep(1000);
  Result := True;
end;

var
  SelectInstallTypePage: TInputOptionWizardPage;
  DownloadPage: TDownloadWizardPage;
  IsUpdateMode: Boolean;

procedure ApplyDarkTheme();
begin
  // Set main wizard form and page backgrounds to sleek pure black (#000000)
  WizardForm.Color := $000000;
  WizardForm.InnerPage.Color := $000000;
  WizardForm.WelcomePage.Color := $000000;
  WizardForm.FinishedPage.Color := $000000;
  WizardForm.SelectDirPage.Color := $000000;
  WizardForm.SelectProgramGroupPage.Color := $000000;
  WizardForm.ReadyPage.Color := $000000;
  WizardForm.InstallingPage.Color := $000000;
  
  // Header Panel - match dark slate gray (#0d0f14 -> BGR: $140F0D)
  WizardForm.MainPanel.Color := $140F0D;
  WizardForm.PageNameLabel.Font.Color := $4444EF; // #ef4444 -> BGR: $4444EF (Soft Red)
  WizardForm.PageNameLabel.Font.Name := 'SF Pro Display';
  WizardForm.PageNameLabel.Font.Style := [fsBold];
  WizardForm.PageDescriptionLabel.Font.Color := $CCCCCC;
  WizardForm.PageDescriptionLabel.Font.Name := 'SF Pro Display';

  // Welcome Page Typography
  WizardForm.WelcomeLabel1.Font.Color := $4444EF; // #ef4444 -> BGR: $4444EF (Soft Red)
  WizardForm.WelcomeLabel1.Font.Name := 'SF Pro Display';
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
  WizardForm.WelcomeLabel2.Font.Color := $CCCCCC;
  WizardForm.WelcomeLabel2.Font.Name := 'SF Pro Display';

  // Directory Selection
  WizardForm.SelectDirLabel.Font.Color := clWhite;
  WizardForm.SelectDirLabel.Font.Name := 'SF Pro Display';
  WizardForm.SelectDirBrowseLabel.Font.Color := clWhite;
  WizardForm.SelectDirBrowseLabel.Font.Name := 'SF Pro Display';
  WizardForm.DirEdit.Color := $140F0D; // #0d0f14 -> BGR: $140F0D
  WizardForm.DirEdit.Font.Color := clWhite;
  WizardForm.DirEdit.Font.Name := 'SF Pro Display';

  // Start Menu Selection
  WizardForm.SelectStartMenuFolderLabel.Font.Color := clWhite;
  WizardForm.SelectStartMenuFolderLabel.Font.Name := 'SF Pro Display';
  WizardForm.SelectStartMenuFolderBrowseLabel.Font.Color := clWhite;
  WizardForm.SelectStartMenuFolderBrowseLabel.Font.Name := 'SF Pro Display';
  WizardForm.GroupEdit.Color := $140F0D; // #0d0f14 -> BGR: $140F0D
  WizardForm.GroupEdit.Font.Color := clWhite;
  WizardForm.GroupEdit.Font.Name := 'SF Pro Display';

  // Ready To Install
  WizardForm.ReadyLabel.Font.Color := clWhite;
  WizardForm.ReadyLabel.Font.Name := 'SF Pro Display';
  WizardForm.ReadyMemo.Color := $140F0D; // #0d0f14 -> BGR: $140F0D
  WizardForm.ReadyMemo.Font.Color := clWhite;
  WizardForm.ReadyMemo.Font.Name := 'SF Pro Display';

  // Progress Page
  WizardForm.FilenameLabel.Font.Color := clWhite;
  WizardForm.FilenameLabel.Font.Name := 'SF Pro Display';
  WizardForm.StatusLabel.Font.Color := clWhite;
  WizardForm.StatusLabel.Font.Name := 'SF Pro Display';

  // Completion Page
  WizardForm.FinishedHeadingLabel.Font.Color := $4444EF; // #ef4444 -> BGR: $4444EF (Soft Red)
  WizardForm.FinishedHeadingLabel.Font.Name := 'SF Pro Display';
  WizardForm.FinishedHeadingLabel.Font.Style := [fsBold];
  WizardForm.FinishedLabel.Font.Color := $CCCCCC;
  WizardForm.FinishedLabel.Font.Name := 'SF Pro Display';
  
  // Custom Option check list
  WizardForm.RunList.Color := $000000;
  WizardForm.RunList.Font.Color := clWhite;
  WizardForm.RunList.Font.Name := 'SF Pro Display';
  
  // Dialog Buttons
  WizardForm.BackButton.Font.Name := 'SF Pro Display';
  WizardForm.NextButton.Font.Name := 'SF Pro Display';
  WizardForm.CancelButton.Font.Name := 'SF Pro Display';
end;

procedure InitializeWizard();
var
  PrevPath: String;
begin
  // Apply dark theme colors to form controls
  ApplyDarkTheme();

  // Tao trang tai ve trinh duyet Stealth Chromium an danh tu GitHub
  DownloadPage := CreateDownloadPage('Tai xuong trinh duyet an danh', 'Vui long cho trong khi tai xuong trinh duyet Stealth Chromium (535 MB) tu GitHub...', nil);

  IsUpdateMode := False;
  // Detect if previous installation exists
  if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ZBizWorld AI Generate Pro_is1', 'InstallLocation', PrevPath) or
     RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ZBizWorld AI Generate Pro_is1', 'InstallLocation', PrevPath) or
     RegQueryStringValue(HKLM, 'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\ZBizWorld AI Generate Pro_is1', 'InstallLocation', PrevPath) or
     RegQueryStringValue(HKCU, 'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\ZBizWorld AI Generate Pro_is1', 'InstallLocation', PrevPath) then
  begin
    if DirExists(PrevPath) then
    begin
      IsUpdateMode := True;
    end;
  end;

  if IsUpdateMode then
  begin
    SelectInstallTypePage := CreateInputOptionPage(
      wpSelectDir,
      'Lựa chọn kiểu cài đặt',
      'Phát hiện phiên bản cũ đã được cài đặt trên máy tính.',
      'Vui lòng chọn phương thức cài đặt tiếp theo:',
      True,
      False
    );

    
    SelectInstallTypePage.Add('Cập nhật ứng dụng (Khuyên dùng - Giữ nguyên toàn bộ dữ liệu, dự án, cấu hình và bản quyền)');
    SelectInstallTypePage.Add('Cài đặt sạch (Xóa hoàn toàn các dự án cũ, cấu hình và khóa bản quyền để cài đặt lại)');
    SelectInstallTypePage.Values[0] := True;
  end;
end;

function IsCleanInstall(): Boolean;
begin
  if not IsUpdateMode then
  begin
    Result := True;
  end
  else
  begin
    Result := SelectInstallTypePage.Values[1];
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  DownloadNeeded: Boolean;
begin
  Result := True;
  if CurPageID = wpReady then begin
    DownloadNeeded := False;
    DownloadPage.Clear;

    // Kiem tra neu thu muc trinh duyet chua ton tai (hoac la cai dat sach) thi moi tai tu GitHub
    if not DirExists(ExpandConstant('{app}\storage\cloakbrowser')) then begin
      DownloadPage.Add('https://github.com/delmuwork-ux/ZBizworld-tool/releases/download/v1.0.0/cloakbrowser.zip', 'cloakbrowser.zip', '');
      DownloadNeeded := True;
    end;

    // Kiem tra neu thu muc backend runtime chua ton tai thi tai tu GitHub
    if not DirExists(ExpandConstant('{app}\storage\runtime\bin')) then begin
      DownloadPage.Add('https://github.com/delmuwork-ux/ZBizworld-tool/releases/download/v1.0.0/backend_runtime.zip', 'backend_runtime.zip', '');
      DownloadNeeded := True;
    end;

    if DownloadNeeded then begin
      DownloadPage.Show;
      try
        DownloadPage.Download;
      except
        if MsgBox('Khong the tai du lieu bo sung tu GitHub: ' + GetExceptionMessage + #13#10#13#10 + 'Ban co muon tiep tuc cai dat khong? (Phan mem se tu dong tai lai cac thanh phan nay khi khoi chay lan dau)', mbConfirmation, MB_YESNO) = IDNO then begin
          Result := False;
        end;
      end;
      DownloadPage.Hide;
    end;
  end;
end;
{ Truoc khi bat dau go cai dat: kill toan bo process cua app dang chay }
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  { Kill sys_helper.exe neu dang chay }
  Exec('taskkill.exe', '/F /IM sys_helper.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  { Kill zbizworld.exe neu dang chay }
  Exec('taskkill.exe', '/F /IM zbizworld.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  { Cho 1 giay de Windows release lock tren file }
  Sleep(1000);
  Result := True;
end;

{ Sau khi go cai dat xong: dung PowerShell xoa sach toan bo thu muc goc }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDir: String;
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDir := ExpandConstant('{app}');
    if DirExists(AppDir) then
    begin
      Exec('powershell.exe',
        '-NoProfile -NonInteractive -Command "Start-Sleep -Seconds 1; Remove-Item -LiteralPath ''' + AppDir + ''' -Recurse -Force -ErrorAction SilentlyContinue"',
        '', SW_HIDE, ewNoWait, ResultCode);
    end;
  end;
end;
