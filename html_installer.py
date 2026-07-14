import os
import sys
os.environ["PYI_DEV_NO_CLEANUP_WARNING"] = "1"
os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = '--disable-gpu --lang=vi'
import ctypes
import shutil
import zipfile
import urllib.request
import subprocess
import winreg
import json
import threading
import time
import webview

# Force run as admin
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Re-run the script with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

# Global configuration
APP_NAME = "ZBizWorld AI Generate Pro"
APP_VERSION = "1.7.4"
DEFAULT_INSTALL_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Programs\AI_Generate_Tool_Pro")
APP_FILES_URL = "https://github.com/delmuwork-ux/ZBizworld-tool/releases/download/v1.0.0/app_files.zip"
CLOAKBROWSER_URL = "https://github.com/delmuwork-ux/ZBizworld-tool/releases/download/v1.0.0/cloakbrowser.zip"
BACKEND_RUNTIME_URL = "https://github.com/delmuwork-ux/ZBizworld-tool/releases/download/v1.0.0/backend_runtime.zip"
VC_REDIST_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
WEBVIEW2_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"

class InstallerAPI:
    def __init__(self):
        self._window = None
        self.install_dir = DEFAULT_INSTALL_DIR
        self.install_type = "update" # or "clean"
        self.is_running = False

    def select_directory(self):
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return result[0]
        return None

    def start_install(self, path, install_type):
        if self.is_running:
            return
        self.install_dir = path or DEFAULT_INSTALL_DIR
        self.install_type = install_type
        self.is_running = True
        
        # Start installation in a separate thread to keep UI responsive
        threading.Thread(target=self._run_installation, daemon=True).start()

    def close_installer(self):
        self._window.destroy()
        os._exit(0)

    def launch_app(self):
        try:
            exe_path = os.path.normpath(os.path.join(self.install_dir, "zbizworld.exe"))
            if os.path.exists(exe_path):
                # Use explorer.exe to launch the app as a standard user (de-elevated from Admin)
                # This prevents WebView2 blank screen rendering issues under elevated Administrator token
                subprocess.Popen(["explorer.exe", exe_path], close_fds=True)
        except Exception as e:
            print(f"Failed to launch app: {e}")
        self._window.destroy()
        os._exit(0)

    def log(self, message):
        print(f"LOG: {message}", flush=True)
        try:
            if self._window:
                self._window.evaluate_js("addLog(" + json.dumps(message) + ")")
        except Exception as e:
            print(f"Failed to log JS: {e}", flush=True)

    def set_progress(self, percent, status):
        print(f"PROGRESS {percent}%: {status}", flush=True)
        try:
            if self._window:
                self._window.evaluate_js("updateProgress(" + str(percent) + ", " + json.dumps(status) + ")")
        except Exception as e:
            print(f"Failed to progress JS: {e}", flush=True)

    def _run_installation(self):
        try:
            base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            self.set_progress(5, "Đang kết thúc các tiến trình cũ...")
            self.log("Đang đóng zbizworld.exe, sys_helper.exe và AI_Generate_Tool.exe...")
            try:
                subprocess.run(["taskkill", "/F", "/IM", "zbizworld.exe", "/T"], capture_output=True, timeout=5)
                subprocess.run(["taskkill", "/F", "/IM", "sys_helper.exe", "/T"], capture_output=True, timeout=5)
                subprocess.run(["taskkill", "/F", "/IM", "AI_Generate_Tool.exe", "/T"], capture_output=True, timeout=5)
            except Exception as e:
                self.log(f"Cảnh báo đóng tiến trình cũ: {e}")
            time.sleep(1.5)

            # Clean install if requested
            if self.install_type == "clean":
                self.set_progress(10, "Đang dọn dẹp thư mục cũ...")
                storage_dir = os.path.join(self.install_dir, "storage")
                if os.path.exists(storage_dir):
                    self.log("Đang xóa sạch dữ liệu cũ (Clean Install)...")
                    try:
                        shutil.rmtree(storage_dir)
                    except Exception as e:
                        self.log(f"Cảnh báo dọn dẹp: {e}. Tiến hành xóa bỏ qua lỗi...")
                        shutil.rmtree(storage_dir, ignore_errors=True)

            os.makedirs(self.install_dir, exist_ok=True)

            # Download and extract app_files.zip containing zbizworld.exe, Zbiz.ico, and config templates
            self.set_progress(15, "Đang tải các tệp ứng dụng cơ bản...")
            self.log("Đang tải app_files.zip từ GitHub...")
            temp_app_zip = os.path.join(os.environ["TEMP"], "app_files.zip")
            self._download_file(APP_FILES_URL, temp_app_zip, 15, 30)

            self.set_progress(30, "Đang giải nén các tệp ứng dụng cơ bản...")
            self.log("Đang giải nén app_files.zip...")
            with zipfile.ZipFile(temp_app_zip, 'r') as zip_ref:
                zip_ref.extractall(self.install_dir)
            os.remove(temp_app_zip)
            self.log("Giải nén các tệp ứng dụng thành công.")

            dst_exe = os.path.join(self.install_dir, "zbizworld.exe")
            dst_ico = os.path.join(self.install_dir, "Zbiz.ico")

            # Check and download Stealth Chromium if missing
            cloak_path = os.path.join(self.install_dir, "storage", "cloakbrowser")
            if not os.path.exists(cloak_path) or self.install_type == "clean":
                self.set_progress(30, "Đang tải trình duyệt ẩn danh Stealth Chromium (535MB)...")
                self.log("Đang tải Stealth Chromium từ GitHub...")
                temp_zip = os.path.join(os.environ["TEMP"], "cloakbrowser.zip")
                self._download_file(CLOAKBROWSER_URL, temp_zip, 30, 60)
                
                self.set_progress(60, "Đang giải nén trình duyệt ẩn danh...")
                self.log("Đang giải nén Stealth Chromium...")
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_ref.extractall(os.path.join(self.install_dir, "storage"))
                os.remove(temp_zip)
                self.log("Giải nén trình duyệt thành công.")

            # Check and download backend runtime if missing
            runtime_bin_path = os.path.join(self.install_dir, "storage", "runtime", "bin")
            if not os.path.exists(runtime_bin_path) or self.install_type == "clean":
                self.set_progress(65, "Đang tải các thành phần hệ thống phụ trợ...")
                self.log("Đang tải Backend Runtime từ GitHub...")
                temp_zip = os.path.join(os.environ["TEMP"], "backend_runtime.zip")
                self._download_file(BACKEND_RUNTIME_URL, temp_zip, 65, 80)
                
                self.set_progress(80, "Đang giải nén các thành phần hệ thống...")
                self.log("Đang giải nén Backend Runtime...")
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_ref.extractall(os.path.join(self.install_dir, "storage", "runtime"))
                os.remove(temp_zip)
                self.log("Giải nén Backend Runtime thành công.")

            # Prerequisites check (VC++ Redist & WebView2)
            self.set_progress(85, "Đang kiểm tra và cài đặt các thành phần phụ thuộc...")
            self._install_dependencies(base_dir)

            # Security rules (Defender exclusion)
            self.set_progress(90, "Đang thêm danh sách tin cậy Windows Defender...")
            self.log("Đang cấu hình Windows Defender Exclusion...")
            subprocess.run([
                "powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
                f"Add-MpPreference -ExclusionPath '{self.install_dir}'"
            ], capture_output=True)

            # Firewall configuration
            self.set_progress(93, "Đang cấu hình tường lửa...")
            self.log("Đang mở tường lửa port 9778 và ứng dụng...")
            subprocess.run([
                "netsh.exe", "advfirewall", "firewall", "add", "rule",
                "name=ZBizWorld AI Generate Backend", "dir=in", "action=allow",
                f"program={self.install_dir}\\storage\\runtime\\bin\\sys_helper.exe", "enable=yes"
            ], capture_output=True)
            subprocess.run([
                "netsh.exe", "advfirewall", "firewall", "add", "rule",
                "name=ZBizWorld AI Generate Launcher", "dir=in", "action=allow",
                f"program={dst_exe}", "enable=yes"
            ], capture_output=True)
            subprocess.run([
                "netsh.exe", "advfirewall", "firewall", "add", "rule",
                "name=ZBizWorld Port 9778", "dir=in", "action=allow",
                "protocol=TCP", "localport=9778", "enable=yes"
            ], capture_output=True)

            # Create Desktop & Start Menu Shortcuts via Powershell
            self.set_progress(96, "Đang tạo phím tắt ứng dụng...")
            self.log("Đang tạo shortcut ngoài Desktop và Start Menu...")
            self._create_shortcuts(dst_exe, dst_ico)

            # Registry integration (Add/Remove Programs)
            self.set_progress(98, "Đang hoàn tất đăng ký hệ thống...")
            self._write_uninstall_registry(dst_exe, dst_ico)

            self.set_progress(100, "Cài đặt thành công!")
            self.log("Cài đặt ZBizWorld AI Generate Pro hoàn tất.")
            try:
                self._window.evaluate_js("showSuccess()")
            except Exception:
                pass

        except Exception as e:
            self.log(f"LỖI CÀI ĐẶT: {str(e)}")
            self.set_progress(0, f"Cài đặt thất bại: {str(e)}")
            try:
                self._window.evaluate_js("showError()")
            except Exception:
                pass

    def _download_file(self, url, dest_path, start_pct, end_pct):
        def progress(block_num, block_size, total_size):
            read_so_far = block_num * block_size
            if total_size > 0:
                percent = read_so_far / total_size
                current_pct = start_pct + (percent * (end_pct - start_pct))
                mb_downloaded = read_so_far / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                self.set_progress(int(current_pct), f"Đang tải: {mb_downloaded:.1f} MB / {mb_total:.1f} MB ({int(percent*100)}%)")
        urllib.request.urlretrieve(url, dest_path, progress)

    def _create_shortcuts(self, exe_path, ico_path):
        desktop_lnk = os.path.expandvars(r"%USERPROFILE%\Desktop\ZBizWorld AI Generate.lnk")
        start_lnk = os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\ZBizWorld AI Generate.lnk")
        
        ps_script = f"""
        $WshShell = New-Object -ComObject WScript.Shell
        
        # Desktop Shortcut
        $Shortcut1 = $WshShell.CreateShortcut("{desktop_lnk}")
        $Shortcut1.TargetPath = "{exe_path}"
        $Shortcut1.WorkingDirectory = "{self.install_dir}"
        $Shortcut1.IconLocation = "{ico_path}"
        $Shortcut1.Save()

        # Start Menu Shortcut
        $Shortcut2 = $WshShell.CreateShortcut("{start_lnk}")
        $Shortcut2.TargetPath = "{exe_path}"
        $Shortcut2.WorkingDirectory = "{self.install_dir}"
        $Shortcut2.IconLocation = "{ico_path}"
        $Shortcut2.Save()
        """
        subprocess.run(["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script], capture_output=True)

    def _install_dependencies(self, base_dir):
        # 1. VC++ Redist
        self.log("Kiểm tra Microsoft Visual C++ Redistributable...")
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
            val, _ = winreg.QueryValueEx(key, "Installed")
            vc_installed = val == 1
        except:
            vc_installed = False

        if not vc_installed:
            vc_installer = os.path.join(base_dir, "vc_redist.x64.exe")
            if not os.path.exists(vc_installer):
                self.log("Đang tải Microsoft Visual C++ Redistributable từ Microsoft...")
                vc_installer = os.path.join(os.environ["TEMP"], "vc_redist.x64.exe")
                try:
                    urllib.request.urlretrieve(VC_REDIST_URL, vc_installer)
                except Exception as e:
                    self.log(f"Lỗi tải VC++ Redist: {e}")
            
            if os.path.exists(vc_installer):
                self.log("Đang cài đặt Microsoft Visual C++ Redistributable...")
                subprocess.run([vc_installer, "/quiet", "/norestart"], capture_output=True)
            else:
                self.log("Cảnh báo: Không thể cài đặt VC++ Redist.")
        else:
            self.log("Microsoft Visual C++ Redistributable đã được cài đặt.")

        # 2. WebView2 Runtime
        self.log("Kiểm tra Microsoft Edge WebView2 Runtime...")
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8ABB-7D3E50F8FC44}")
            val, _ = winreg.QueryValueEx(key, "pv")
            wv_installed = val != "0.0.0.0" and val != ""
        except:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8ABB-7D3E50F8FC44}")
                val, _ = winreg.QueryValueEx(key, "pv")
                wv_installed = val != "0.0.0.0" and val != ""
            except:
                wv_installed = False

        if not wv_installed:
            wv_installer = os.path.join(base_dir, "MicrosoftEdgeWebview2Setup.exe")
            if not os.path.exists(wv_installer):
                self.log("Đang tải Microsoft Edge WebView2 Runtime bootstrapper từ Microsoft...")
                wv_installer = os.path.join(os.environ["TEMP"], "MicrosoftEdgeWebview2Setup.exe")
                try:
                    urllib.request.urlretrieve(WEBVIEW2_URL, wv_installer)
                except Exception as e:
                    self.log(f"Lỗi tải WebView2 bootstrapper: {e}")

            if os.path.exists(wv_installer):
                self.log("Đang cài đặt Microsoft Edge WebView2 Runtime...")
                subprocess.run([wv_installer, "/silent", "/install"], capture_output=True)
            else:
                self.log("Cảnh báo: Không thể cài đặt Microsoft Edge WebView2 Runtime.")
        else:
            self.log("Microsoft Edge WebView2 Runtime đã được cài đặt.")

    def _write_uninstall_registry(self, exe_path, ico_path):
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\ZBizWorldAIGenerate"
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "ZBizWorld")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, ico_path)
            
            # Simple uninstall command using powershell to clean the folders
            uninstall_cmd = f'powershell.exe -NoProfile -Command "Stop-Process -Name zbizworld -Force -ErrorAction SilentlyContinue; Stop-Process -Name sys_helper -Force -ErrorAction SilentlyContinue; Remove-Item -LiteralPath \'{self.install_dir}\' -Recurse -Force; Remove-Item -LiteralPath \'$env:USERPROFILE\\Desktop\\ZBizWorld AI Generate.lnk\' -Force; Remove-Item -LiteralPath \'$env:USERPROFILE\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\ZBizWorld AI Generate.lnk\' -Force; Remove-Item -Path \'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ZBizWorldAIGenerate\' -Force"'
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
        except Exception as e:
            self.log(f"Cảnh báo lỗi ghi registry gỡ cài đặt: {e}")

# HTML/CSS UI
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Setup - ZBizWorld AI Generate Pro</title>
    <style>
        * {
            box-sizing: border-box;
            user-select: none;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            background: #0d0f14;
            color: #e2e8f0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            margin: 0;
            padding: 0;
        }
        .container {
            width: 100%;
            height: 100%;
            background: #0d0f14;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }
        .header {
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .header-logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo-box {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, #8B0000, #400000);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 20px;
            color: #ffffff;
            box-shadow: 0 0 10px rgba(139, 0, 0, 0.6);
        }
        .app-title {
            font-size: 18px;
            font-weight: 700;
            background: linear-gradient(90deg, #ffffff, #f87171);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .app-version {
            font-size: 12px;
            color: #888888;
        }
        .content {
            flex: 1;
            padding: 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .page {
            display: none;
            flex-direction: column;
            gap: 16px;
            height: 100%;
        }
        .page.active {
            display: flex;
        }
        .form-title {
            font-size: 15px;
            font-weight: 500;
            color: #ef4444;
        }
        .option-cards {
            display: flex;
            gap: 16px;
        }
        .card {
            flex: 1;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .card.active {
            background: rgba(139, 0, 0, 0.15);
            border-color: rgba(239, 68, 68, 0.6);
            box-shadow: 0 0 12px rgba(139, 0, 0, 0.3);
        }
        .card-title {
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
        }
        .card-desc {
            font-size: 11px;
            color: #9ca3af;
            line-height: 1.4;
        }
        .path-selector {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .path-label {
            font-size: 12px;
            color: #9ca3af;
        }
        .path-input-group {
            display: flex;
            gap: 8px;
        }
        .path-input {
            flex: 1;
            height: 36px;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(239, 68, 68, 0.45);
            border-radius: 8px;
            color: #ffffff;
            padding: 0 12px;
            font-size: 13px;
            font-family: inherit;
            outline: none;
        }
        .btn-browse {
            height: 36px;
            padding: 0 16px;
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid rgba(239, 68, 68, 0.45);
            border-radius: 8px;
            color: #ffffff;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-browse:hover {
            background: rgba(139, 0, 0, 0.15);
            border-color: rgba(239, 68, 68, 0.8);
        }
        .btn-primary {
            height: 40px;
            background: linear-gradient(180deg, #8B0000 0%, #630000 100%);
            border: 1px solid #4a0000;
            border-radius: 8px;
            color: #ffffff;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(139, 0, 0, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn-primary:hover {
            background: linear-gradient(180deg, #a50000 0%, #7a0000 100%);
            box-shadow: 0 0 16px rgba(139, 0, 0, 0.6);
        }
        .progress-section {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 20px;
        }
        .progress-bar-bg {
            height: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
            width: 100%;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #8B0000, #ef4444);
            width: 0%;
            border-radius: 4px;
            transition: width 0.1s ease-out;
            box-shadow: 0 0 8px #ef4444;
        }
        .status-text {
            font-size: 12px;
            color: #9ca3af;
        }
        .logs-window {
            height: 120px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 12px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 11px;
            color: #a7f3d0;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .log-entry {
            line-height: 1.4;
        }
        .success-checkmark {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 16px;
            margin-top: 30px;
        }
        .checkmark-icon {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(16, 185, 129, 0.1);
            border: 2px solid #10b981;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #10b981;
            font-size: 32px;
            font-weight: bold;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
        }
        .checkbox-container {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            margin-top: 10px;
        }
        .checkbox-container input {
            cursor: pointer;
            accent-color: #ef4444;
        }
        .checkbox-label {
            font-size: 13px;
            color: #9ca3af;
        }
        .footer {
            padding: 16px 24px;
            display: flex;
            justify-content: flex-end;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            background: rgba(0, 0, 0, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-logo">
                <div class="logo-box">Z</div>
                <div>
                    <div class="app-title">ZBizWorld AI Generate Pro</div>
                    <div class="app-version">Phiên bản 1.7.4</div>
                </div>
            </div>
        </div>

        <!-- Content Area -->
        <div class="content">
            <!-- PAGE 1: Welcome & Settings -->
            <div id="pageWelcome" class="page active">
                <div class="form-title">Lựa chọn kiểu cài đặt</div>
                
                <div class="option-cards">
                    <div id="cardUpdate" class="card active" onclick="selectType('update')">
                        <div class="card-title">Cập nhật ứng dụng (Khuyên dùng)</div>
                        <div class="card-desc">Giữ nguyên toàn bộ dự án cũ, kịch bản, cấu hình và khóa bản quyền.</div>
                    </div>
                    <div id="cardClean" class="card" onclick="selectType('clean')">
                        <div class="card-title">Cài đặt sạch (Clean Install)</div>
                        <div class="card-desc">Xóa sạch kịch bản cũ, các dự án cũ và bản quyền để bắt đầu cài đặt lại.</div>
                    </div>
                </div>

                <div class="path-selector">
                    <div class="path-label">Thư mục cài đặt:</div>
                    <div class="path-input-group">
                        <input id="installPath" type="text" class="path-input" readonly>
                        <button class="btn-browse" onclick="browseFolder()">Browse...</button>
                    </div>
                </div>
            </div>

            <!-- PAGE 2: Progress -->
            <div id="pageProgress" class="page">
                <div class="form-title">Đang cài đặt ứng dụng</div>
                <div class="progress-section">
                    <div id="statusLabel" class="status-text">Bắt đầu cài đặt...</div>
                    <div class="progress-bar-bg">
                        <div id="progressBar" class="progress-bar"></div>
                    </div>
                </div>
                <div id="logsWindow" class="logs-window"></div>
            </div>

            <!-- PAGE 3: Success -->
            <div id="pageSuccess" class="page">
                <div class="success-checkmark">
                    <div class="checkmark-icon">✓</div>
                    <div class="form-title" style="color: #10b981; font-size: 18px;">Cài đặt hoàn tất!</div>
                    <label class="checkbox-container">
                        <input type="checkbox" id="launchCheckbox" checked>
                        <span class="checkbox-label">Khởi động ZBizWorld AI Generate Pro ngay</span>
                    </label>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <button id="btnNext" class="btn-primary" onclick="nextStep()" style="width: 140px;">Cài đặt</button>
        </div>
    </div>

    <script>
        let currentStep = 'welcome';
        let selectedInstallType = 'update';
        
        // Initial setup
        document.getElementById('installPath').value = "%DEFAULT_INSTALL_DIR%";

        function selectType(type) {
            selectedInstallType = type;
            document.getElementById('cardUpdate').classList.remove('active');
            document.getElementById('cardClean').classList.remove('active');
            if (type === 'update') {
                document.getElementById('cardUpdate').classList.add('active');
            } else {
                document.getElementById('cardClean').classList.add('active');
            }
        }

        function browseFolder() {
            pywebview.api.select_directory().then(function(res) {
                if (res) {
                    document.getElementById('installPath').value = res;
                }
            });
        }

        function addLog(msg) {
            var logsWin = document.getElementById('logsWindow');
            var entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerText = '> ' + msg;
            logsWin.appendChild(entry);
            logsWin.scrollTop = logsWin.scrollHeight;
        }

        function updateProgress(pct, status) {
            document.getElementById('progressBar').style.width = pct + '%';
            document.getElementById('statusLabel').innerText = status;
        }

        function showSuccess() {
            currentStep = 'success';
            document.getElementById('pageProgress').classList.remove('active');
            document.getElementById('pageSuccess').classList.add('active');
            document.getElementById('btnNext').innerText = 'Hoàn tất';
            document.getElementById('btnNext').disabled = false;
        }

        function showError() {
            document.getElementById('btnNext').innerText = 'Thoát';
            document.getElementById('btnNext').disabled = false;
            currentStep = 'error';
        }

        function nextStep() {
            if (currentStep === 'welcome') {
                currentStep = 'progress';
                document.getElementById('pageWelcome').classList.remove('active');
                document.getElementById('pageProgress').classList.add('active');
                document.getElementById('btnNext').innerText = 'Đang cài đặt...';
                document.getElementById('btnNext').disabled = true;
                
                var path = document.getElementById('installPath').value;
                if (window.pywebview && window.pywebview.api) {
                    pywebview.api.start_install(path, selectedInstallType);
                } else {
                    var retryCount = 0;
                    var checkInterval = setInterval(function() {
                        retryCount++;
                        if (window.pywebview && window.pywebview.api) {
                            clearInterval(checkInterval);
                            pywebview.api.start_install(path, selectedInstallType);
                        } else if (retryCount > 10) {
                            clearInterval(checkInterval);
                            alert("Lỗi kết nối bộ cài đặt (Bridge not ready). Vui lòng tắt đi bật lại hoặc chạy dưới quyền Admin!");
                            showError();
                        }
                    }, 300);
                }
            } else if (currentStep === 'success') {
                var launch = document.getElementById('launchCheckbox').checked;
                if (window.pywebview && window.pywebview.api) {
                    if (launch) {
                        pywebview.api.launch_app();
                    } else {
                        pywebview.api.close_installer();
                    }
                } else {
                    window.close();
                }
            } else if (currentStep === 'error') {
                if (window.pywebview && window.pywebview.api) {
                    pywebview.api.close_installer();
                } else {
                    window.close();
                }
            }
        }
    </script>
</body>
</html>
""".replace("%DEFAULT_INSTALL_DIR%", DEFAULT_INSTALL_DIR.replace("\\", "\\\\"))

if __name__ == "__main__":
    # Redirect stdout and stderr to a log file in Temp folder to prevent permission locks
    try:
        log_file = os.path.expandvars(r"%TEMP%\zbizworld_installer_debug.log")
        sys.stdout = open(log_file, "w", encoding="utf-8", buffering=1)
        sys.stderr = sys.stdout
    except Exception as e:
        pass
    print("Installer starting...")
    
    # Set default network timeout to prevent hanging on downloads
    try:
        import socket
        socket.setdefaulttimeout(30)
        print("Socket default timeout set to 30s")
    except Exception as e:
        print(f"Error setting socket timeout: {e}")

    api = InstallerAPI()
    window = webview.create_window(
        title="Setup - ZBizWorld AI Generate Pro",
        html=HTML_CONTENT,
        width=700,
        height=480,
        resizable=False,
        background_color='#0d0f14',
        js_api=api
    )
    api._window = window
    
    def on_closed():
        import os
        os._exit(0)
        
    window.events.closed += on_closed
    
    # Set unique WebView2 cache directory in AppData to prevent file locks/hangs on launch
    cache_dir = os.path.expandvars(r"%LOCALAPPDATA%\ZBizWorldInstallerCache")
    try:
        os.makedirs(cache_dir, exist_ok=True)
    except:
        cache_dir = None
        
    if cache_dir:
        webview.start(storage_path=cache_dir)
    else:
        webview.start()
