import sys
import os
os.environ["PYI_DEV_NO_CLEANUP_WARNING"] = "1"
os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = '--disable-gpu --lang=vi'
import base64
import threading
import time
import urllib.request
import email.utils
import subprocess
import hashlib
import hmac
import json
import datetime
import atexit

should_cleanup = False

def global_exit_cleanup():
    if not should_cleanup:
        return
    try:
        import subprocess
        import time
        # Forcefully terminate specific child processes to release folder locks
        subprocess.run('taskkill /F /IM msedgewebview2.exe', shell=True, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run('taskkill /F /IM sys_helper.exe', shell=True, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run('taskkill /F /IM AI_Generate_Tool.exe', shell=True, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)
    except Exception:
        pass

atexit.register(global_exit_cleanup)

def cleanup_old_mei_directories(current_dir):
    try:
        import subprocess
        for item in os.listdir(current_dir):
            if item.startswith("_MEI") and os.path.isdir(os.path.join(current_dir, item)):
                meipass_folder = getattr(sys, '_MEIPASS', '')
                if meipass_folder and os.path.abspath(os.path.join(current_dir, item)) == os.path.abspath(meipass_folder):
                    continue
                folder_path = os.path.join(current_dir, item)
                try:
                    # Native Windows directory removal runs asynchronously, is extremely fast, and bypasses python blocking
                    subprocess.Popen(f'cmd.exe /c rmdir /s /q "{folder_path}"', shell=True, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
                except Exception:
                    pass
    except Exception:
        pass

try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False

try:
    import tkinter as tk
    HAS_TK = True
except ImportError:
    HAS_TK = False

def show_windows_message(title, message, icon_type="error"):
    # Determine the VBScript MsgBox icon flag
    # 16 = Critical/Error, 48 = Warning/Exclamation, 64 = Information
    vbs_icon = 16
    if icon_type == "warning":
        vbs_icon = 48
    elif icon_type == "info":
        vbs_icon = 64

    # Method 1: Try tkinter if available
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        if icon_type == "error":
            messagebox.showerror(title, message)
        elif icon_type == "warning":
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)
        root.destroy()
        return
    except Exception:
        pass
        
    # Method 2: Fallback to mshta VBScript msgbox (100% native Windows, no .NET, no PowerShell, no WebView2 required)
    try:
        escaped_message = message.replace("\n", " ").replace("\r", "").replace('"', '""')
        escaped_title = title.replace('"', '""')
        cmd = f'mshta vbscript:Execute("msgbox ""{escaped_message}"", {vbs_icon}, ""{escaped_title}"":window.close")'
        subprocess.run(cmd, shell=True, creationflags=0x08000000)
        return
    except Exception:
        pass
        
    # Fallback to standard print
    print(f"[{title}] {message}")

# --- CONFIGURATION FOR SUPABASE LICENSING SYSTEM ---
SUPABASE_URL = "https://tpyrquircxvawbqsmkts.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_iKtMpJveAz8tlhUrsjdW7A_6hzQhuQS"

# Redirect stdout and stderr to os.devnull to prevent crash in PyInstaller windowed mode
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# Prevent loading mismatched .pyd files from the executable's directory
exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
if hasattr(sys, '_MEIPASS'):
    # Clean sys.path: remove empty strings, current directory, and the executable directory
    sys.path = [
        p for p in sys.path 
        if p and p != '.' and os.path.abspath(p) != os.path.abspath(exe_dir)
    ]
    # Ensure PyInstaller's extracted bundle directory is at the absolute top of the search path
    if sys._MEIPASS in sys.path:
        sys.path.remove(sys._MEIPASS)
    sys.path.insert(0, sys._MEIPASS)

def get_network_time():
    try:
        req = urllib.request.Request("https://www.google.com", method="HEAD")
        with urllib.request.urlopen(req, timeout=3.0) as response:
            date_str = response.info().get("Date")
            if date_str:
                tuple_time = email.utils.parsedate_tz(date_str)
                if tuple_time:
                    return email.utils.mktime_tz(tuple_time)
    except Exception:
        pass
    return None

def encrypt_data(data_dict):
    secret = b"activation_key_secret_2026_secure"
    plain = json.dumps(data_dict).encode('utf-8')
    enc = bytearray()
    for i in range(len(plain)):
        enc.append(plain[i] ^ secret[i % len(secret)])
    return base64.b64encode(enc).decode('utf-8')

def decrypt_data(enc_str):
    secret = b"activation_key_secret_2026_secure"
    enc = base64.b64decode(enc_str.encode('utf-8'))
    plain = bytearray()
    for i in range(len(enc)):
        plain.append(enc[i] ^ secret[i % len(secret)])
    return json.loads(plain.decode('utf-8'))

def parse_iso_datetime(iso_str):
    if not iso_str:
        return time.time() + 30 * 24 * 3600
    try:
        s = iso_str.split('.')[0].replace('Z', '')
        dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        return dt.replace(tzinfo=datetime.timezone.utc).timestamp()
    except Exception as e:
        print("Error parsing datetime:", e)
        return time.time() + 30 * 24 * 3600

def verify_key_supabase_online(key_code, hwid):
    ok, expires_at, reason = activate_license_online(key_code, hwid)
    if ok:
        return True, expires_at, None
    else:
        if reason == "Không thể kết nối đến máy chủ xác thực!":
            return True, None, "network_error"
        return False, None, reason


class LicenseAPI:
    def __init__(self, current_hwid):
        self.current_hwid = current_hwid
        self.result = {"ok": False, "expires_at": None, "license_key": None}
        self._window = None

    def activate_key(self, key_code):
        key_code = key_code.strip()
        if not key_code:
            try:
                self._window.evaluate_js("onActivationResult(false, 'Vui lòng nhập khóa kích hoạt!')")
            except Exception:
                pass
            return
        
        # Run in background thread to prevent WebView2 UI freeze/lag
        threading.Thread(target=self._async_activate, args=(key_code,), daemon=True).start()

    def _async_activate(self, key_code):
        ok, expires_at, reason = activate_license_online(key_code, self.current_hwid)
        if ok:
            self.result["ok"] = True
            self.result["expires_at"] = expires_at
            self.result["license_key"] = key_code
            try:
                self._window.evaluate_js("onActivationResult(true, '')")
            except Exception:
                pass
        else:
            err_reason = reason or "Khóa kích hoạt không chính xác!"
            try:
                self._window.evaluate_js("onActivationResult(false, " + json.dumps(err_reason) + ")")
            except Exception:
                pass

    def close_window(self):
        if self._window:
            self._window.destroy()

def get_logo_base64():
    try:
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        logo_path = os.path.join(exe_dir, "storage", "runtime", "bin", "static", "logo_small.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(exe_dir, "storage", "runtime", "bin", "static", "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print("Error reading logo:", e)
    return ""

def check_password_html(current_hwid):
    api = LicenseAPI(current_hwid)
    logo_b64 = get_logo_base64()
    
    logo_html = ""
    if logo_b64:
        logo_html = '<div class="logo-area"><img src="data:image/png;base64,' + logo_b64 + '" alt="Logo" class="logo-icon"></div>'
    else:
        logo_html = ''
        
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ZBizWorld - Kích hoạt bản quyền</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
            -webkit-user-select: none;
        }
        body {
            background-color: #0b0c10;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            height: 100vh;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .window {
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #141622 0%, #0d0f17 100%);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .header {
            padding: 16px 24px 5px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #1f2937;
        }
        .header .title {
            font-size: 16px;
            font-weight: 800;
            color: #ef4444;
            letter-spacing: 0.5px;
        }
        .header .version {
            font-size: 11px;
            color: #6b7280;
        }
        .content {
            flex: 1;
            padding: 20px 24px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .key-card {
            background-color: #211317;
            border: 2px solid #ef4444;
            border-radius: 12px;
            padding: 22px;
            box-shadow: 0 8px 24px rgba(239, 68, 68, 0.15);
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .logo-area {
            display: flex;
            justify-content: center;
            margin-bottom: 12px;
        }
        .logo-icon {
            width: 48px;
            height: 48px;
            object-fit: contain;
            filter: drop-shadow(0 0 15px rgba(239, 68, 68, 0.25));
        }
        .desc {
            font-size: 12.5px;
            color: #d1d5db;
            line-height: 1.5;
            margin-bottom: 12px;
            text-align: center;
        }
        .input-group {
            width: 100%;
            margin-bottom: 10px;
        }
        .path-input {
            width: 100%;
            background-color: #1a0d10;
            border: 1px solid #5a272e;
            border-radius: 8px;
            padding: 10px 14px;
            color: #ffffff;
            font-size: 13px;
            outline: none;
            text-align: center;
            transition: all 0.2s;
        }
        .path-input:focus {
            border-color: #ef4444;
            box-shadow: 0 0 8px rgba(239, 68, 68, 0.35);
        }
        .message {
            font-size: 12px;
            font-weight: 600;
            color: #ef4444;
            height: 16px;
            text-align: center;
        }
        .message.loading {
            color: #fbbf24;
        }
        .footer {
            padding: 12px 24px;
            border-top: 1px solid #1f2937;
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }
        .btn {
            padding: 8px 20px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
        }
        .btn-cancel {
            background-color: transparent;
            color: #9ca3af;
        }
        .btn-cancel:hover {
            color: #ffffff;
        }
        .btn-install {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
        }
        .btn-install:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(239, 68, 68, 0.3);
        }
    </style>
</head>
<body>
    <div class="window">
        <div class="header">
            <div class="title">ZBIZWORLD</div>
            <div class="version">Version 1.7.4</div>
        </div>
        
        <div class="content">
            <div class="key-card">
                {{LOGO_PLACEHOLDER}}
                <div class="desc">Vui lòng nhập khóa kích hoạt để sử dụng sản phẩm:</div>
                
                <div class="input-group">
                    <input type="text" id="license-key-input" class="path-input" placeholder="Nhập mã key bản quyền tại đây" autocomplete="off">
                </div>
                
                <div id="msg-label" class="message"></div>
            </div>
        </div>
        
        <div class="footer">
            <button id="btn-close" class="btn btn-cancel" onclick="doClose()">Đóng</button>
            <button id="btn-submit" class="btn btn-install" onclick="doActivate()">KÍCH HOẠT NGAY</button>
        </div>
    </div>

    <script>
        var input = document.getElementById('license-key-input');
        var btn = document.getElementById('btn-submit');
        var msg = document.getElementById('msg-label');

        function doActivate() {
            var val = input.value.trim();
            if (!val) {
                msg.textContent = "Vui lòng nhập khóa kích hoạt!";
                msg.className = "message";
                return;
            }

            msg.textContent = "Đang kiểm tra...";
            msg.className = "message loading";
            btn.disabled = true;
            input.disabled = true;
            
            if (window.pywebview && window.pywebview.api) {
                pywebview.api.activate_key(val);
            } else {
                msg.textContent = "Hệ thống đang khởi tạo, vui lòng thử lại!";
                msg.className = "message";
                btn.disabled = false;
                input.disabled = false;
            }
        }

        // Python background thread callback
        function onActivationResult(success, reason) {
            btn.disabled = false;
            input.disabled = false;
            if (success) {
                msg.textContent = "Kích hoạt thành công!";
                msg.className = "message loading";
                setTimeout(function() {
                    if (window.pywebview && window.pywebview.api) {
                        pywebview.api.close_window();
                    } else {
                        window.close();
                    }
                }, 800);
            } else {
                msg.textContent = reason;
                msg.className = "message";
            }
        }

        function doClose() {
            if (window.pywebview && window.pywebview.api) {
                pywebview.api.close_window();
            } else {
                window.close();
            }
        }

        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                doActivate();
            }
        });
    </script>
</body>
</html>
"""
    html_content = html_content.replace("{{LOGO_PLACEHOLDER}}", logo_html)

    # Write HTML to a temp file and load via file:/// URL to bypass WebView2 data URI restrictions on some machines
    temp_dir = os.path.expandvars(r"%TEMP%")
    temp_html_path = os.path.normpath(os.path.join(temp_dir, "zbiz_license.html"))
    url = None
    try:
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        url = "file:///" + temp_html_path.replace("\\", "/")
    except Exception as e:
        print(f"Failed to write temp license HTML: {e}")

    # Increased window size to 520x420 to prevent interface clipping
    if url:
        api._window = webview.create_window(
            "ZBizWorld - Kích hoạt bản quyền",
            url=url,
            width=520,
            height=420,
            resizable=False,
            background_color="#0d0f17",
            js_api=api
        )
    else:
        api._window = webview.create_window(
            "ZBizWorld - Kích hoạt bản quyền",
            html=html_content,
            width=520,
            height=420,
            resizable=False,
            background_color="#0d0f17",
            js_api=api
        )
    
    webview.start()
    return api.result["ok"], api.result["expires_at"], api.result["license_key"]

def check_password_powershell(current_hwid):
    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    icon_path = os.path.join(current_dir, "Zbiz.ico").replace("\\", "\\\\")
    
    ps_script = f"""
    # Force TLS 1.2 for secure Supabase API connections
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $form = New-Object System.Windows.Forms.Form
    $form.Text = "ZBizWorld - Kích hoạt bản quyền"
    $form.Size = New-Object System.Drawing.Size(420, 260)
    $form.StartPosition = "CenterScreen"
    $form.TopMost = $true
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    $form.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42) # Slate-900

    # Try to load Zbiz icon
    $iconPath = "{icon_path}"
    if (Test-Path $iconPath) {{
        $form.Icon = New-Object System.Drawing.Icon($iconPath)
    }}

    # Header Label
    $header = New-Object System.Windows.Forms.Label
    $header.Text = "ZBizWorld AI Generate Pro"
    $header.Location = New-Object System.Drawing.Point(30, 20)
    $header.Size = New-Object System.Drawing.Size(360, 30)
    $header.ForeColor = [System.Drawing.Color]::FromArgb(251, 191, 36) # Amber-400 (Gold)
    $header.Font = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Bold)
    $header.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter

    # Instruction Label
    $instr = New-Object System.Windows.Forms.Label
    $instr.Text = "Vui lòng nhập khóa kích hoạt để sử dụng sản phẩm:"
    $instr.Location = New-Object System.Drawing.Point(30, 65)
    $instr.Size = New-Object System.Drawing.Size(360, 20)
    $instr.ForeColor = [System.Drawing.Color]::FromArgb(156, 163, 175) # Gray-400
    $instr.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
    $instr.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter

    # TextBox
    $textBox = New-Object System.Windows.Forms.TextBox
    $textBox.Location = New-Object System.Drawing.Point(40, 95)
    $textBox.Size = New-Object System.Drawing.Size(340, 25)
    $textBox.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59) # Slate-800
    $textBox.ForeColor = [System.Drawing.Color]::FromArgb(248, 250, 252) # Slate-50
    $textBox.Font = New-Object System.Drawing.Font("Segoe UI", 10.5)
    $textBox.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle

    # Error Label (initially hidden)
    $errLabel = New-Object System.Windows.Forms.Label
    $errLabel.Text = "Khóa kích hoạt không chính xác!"
    $errLabel.Location = New-Object System.Drawing.Point(30, 125)
    $errLabel.Size = New-Object System.Drawing.Size(360, 20)
    $errLabel.ForeColor = [System.Drawing.Color]::FromArgb(239, 68, 68) # Red-500
    $errLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
    $errLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
    $errLabel.Visible = $false

    # Button
    $button = New-Object System.Windows.Forms.Button
    $button.Text = "KÍCH HOẠT NGAY"
    $button.Location = New-Object System.Drawing.Point(120, 160)
    $button.Size = New-Object System.Drawing.Size(180, 38)
    $button.BackColor = [System.Drawing.Color]::FromArgb(251, 191, 36) # Amber-400 (Gold)
    $button.ForeColor = [System.Drawing.Color]::FromArgb(15, 23, 42) # Slate-900 (Dark Slate)
    $button.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
    $button.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $button.FlatAppearance.BorderSize = 0

    # Hover Effects
    $button.add_MouseEnter({{
        $button.BackColor = [System.Drawing.Color]::FromArgb(245, 158, 11) # Amber-500
        $button.Cursor = [System.Windows.Forms.Cursors]::Hand
    }})
    $button.add_MouseLeave({{
        $button.BackColor = [System.Drawing.Color]::FromArgb(251, 191, 36) # Amber-400
    }})

    $button.add_Click({{
        $inputText = $textBox.Text.Trim()
        if ($inputText -eq "") {{
            $errLabel.Text = "Vui lòng nhập khóa kích hoạt!"
            $errLabel.Visible = $true
            return
        }}

        if ("{SUPABASE_URL}" -eq "YOUR_SUPABASE_URL" -or "{SUPABASE_ANON_KEY}" -eq "YOUR_SUPABASE_ANON_KEY") {{
            $errLabel.Text = "Lỗi: Supabase chưa được cấu hình!"
            $errLabel.Visible = $true
            return
        }}

        $body = @{{
            p_key_code = $inputText
            p_hwid = "{current_hwid}"
        }} | ConvertTo-Json

        $headers = @{{
            "apikey" = "{SUPABASE_ANON_KEY}"
            "Authorization" = "Bearer {SUPABASE_ANON_KEY}"
            "Content-Type" = "application/json"
        }}

        try {{
            $response = Invoke-RestMethod -Uri "{SUPABASE_URL}/rest/v1/rpc/activate_license" -Method Post -Headers $headers -Body $body -TimeoutSec 10
            if ($response.ok -eq $true) {{
                $outObj = @{{
                    ok = $true
                    expires_at = $response.expires_at
                    license_key = $inputText
                }}
                $script:resultJson = ($outObj | ConvertTo-Json -Compress)
                $form.Tag = "ok"
                $form.Close()
            }} else {{
                $errLabel.Text = $response.reason
                $errLabel.Visible = $true
            }}
        }} catch {{
            $errLabel.Text = "Không thể kết nối đến máy chủ xác thực!"
            $errLabel.Visible = $true
        }}
    }})

    $textBox.add_KeyDown({{
        if ($_.KeyCode -eq [System.Windows.Forms.Keys]::Enter) {{
            $button.PerformClick()
        }}
    }})

    $form.Controls.Add($header)
    $form.Controls.Add($instr)
    $form.Controls.Add($textBox)
    $form.Controls.Add($errLabel)
    $form.Controls.Add($button)

    $form.ShowDialog() | Out-Null
    if ($form.Tag -eq "ok") {{ Write-Output $script:resultJson; exit 1 }} else {{ exit 0 }}
    """
    try:
        cmd = ["powershell", "-NoProfile", "-Command", ps_script]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=0x08000000)
        if res.returncode == 1:
            out_str = res.stdout.strip()
            if out_str:
                for line in reversed(out_str.splitlines()):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            res_dict = json.loads(line)
                            if res_dict.get("ok") is True:
                                return True, res_dict.get("expires_at"), res_dict.get("license_key")
                        except Exception:
                            pass
            
            error_details = out_str.replace('"', '\\"').replace('\n', '\\n')
            ps_err = f'[System.Windows.Forms.MessageBox]::Show("Lỗi phân tích phản hồi kích hoạt.\\n\\nChi tiết:\\n{error_details}", "Lỗi hệ thống", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)'
            subprocess.run(["powershell", "-NoProfile", "-Command", "Add-Type -AssemblyName System.Windows.Forms;" + ps_err], creationflags=0x08000000)
    except Exception as e:
        print("Error in check_password_powershell:", e)
    return False, None, None

def activate_license_online(key_code, hwid):
    if "YOUR_SUPABASE_URL" in SUPABASE_URL or not SUPABASE_URL:
        return False, None, "Supabase chưa được cấu hình!"
    url = f"{SUPABASE_URL}/rest/v1/rpc/activate_license"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    body = json.dumps({"p_key_code": key_code, "p_hwid": hwid}).encode('utf-8')
    try:
        import socket
        import ssl
        # Set global socket timeout to prevent DNS/proxy hangs on Windows
        socket.setdefaulttimeout(8.0)
        
        # Create unverified SSL context to prevent SSL verification errors on older Windows versions
        ctx = ssl._create_unverified_context()
        
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=8.0, context=ctx) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("ok", False), res_data.get("expires_at"), res_data.get("reason")
    except Exception as e:
        print("Error activating license online:", e)
        return False, None, "Không thể kết nối đến máy chủ xác thực!"

def check_password_tkinter(current_hwid):
    result = {"ok": False, "expires_at": None, "license_key": None}
    
    root = tk.Tk()
    root.title("ZBizWorld - Kích hoạt bản quyền")
    root.configure(bg="#0f172a")
    
    # Try to load icon
    try:
        current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        icon_path = os.path.join(current_dir, "Zbiz.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    # Set dimensions and center
    window_width = 420
    window_height = 260
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    position_top = int(screen_height/2 - window_height/2)
    position_right = int(screen_width/2 - window_width/2)
    root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")
    root.resizable(False, False)
    root.focus_force()

    # Header
    header = tk.Label(
        root, 
        text="ZBizWorld AI Generate Pro", 
        font=("Segoe UI", 16, "bold"), 
        bg="#0f172a", 
        fg="#fbbf24"
    )
    header.pack(pady=(20, 5))

    # Instruction
    instr = tk.Label(
        root, 
        text="Vui lòng nhập khóa kích hoạt để sử dụng sản phẩm:", 
        font=("Segoe UI", 9), 
        bg="#0f172a", 
        fg="#9ca3af"
    )
    instr.pack(pady=5)

    # Input Box Wrapper (for 1px border look)
    input_border = tk.Frame(root, bg="#334155", bd=0)
    input_border.pack(pady=(10, 5), ipady=1, ipadx=1)

    entry = tk.Entry(
        input_border, 
        font=("Segoe UI", 11), 
        bg="#1e293b", 
        fg="#f8fafc", 
        insertbackground="#f8fafc",
        relief="flat", 
        width=36,
        justify="center"
    )
    entry.pack(ipady=4)
    entry.focus()

    # Error Label
    err_label = tk.Label(
        root, 
        text="", 
        font=("Segoe UI", 9, "bold"), 
        bg="#0f172a", 
        fg="#ef4444"
    )
    err_label.pack(pady=2)

    # Activation Action
    def on_activate():
        key_code = entry.get().strip()
        if not key_code:
            err_label.config(text="Vui lòng nhập khóa kích hoạt!")
            return
            
        err_label.config(text="Đang kiểm tra...", fg="#fbbf24")
        root.update()
        
        ok, expires_at, reason = activate_license_online(key_code, current_hwid)
        if ok:
            result["ok"] = True
            result["expires_at"] = expires_at
            result["license_key"] = key_code
            root.destroy()
        else:
            err_label.config(text=reason or "Khóa kích hoạt không chính xác!", fg="#ef4444")

    # Enter key binding
    entry.bind("<Return>", lambda event: on_activate())

    # Button
    btn = tk.Button(
        root, 
        text="KÍCH HOẠT NGAY", 
        font=("Segoe UI", 11, "bold"), 
        bg="#fbbf24", 
        fg="#0f172a", 
        activebackground="#f59e0b",
        activeforeground="#0f172a",
        relief="flat",
        cursor="hand2",
        command=on_activate,
        width=20
    )
    btn.pack(pady=(15, 10))

    # Hover animations for Button
    def on_enter(e):
        btn.config(bg="#f59e0b")
    def on_leave(e):
        btn.config(bg="#fbbf24")
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    # Start main loop
    root.mainloop()
    return result["ok"], result["expires_at"], result["license_key"]

def get_hwid():
    try:
        uuid_cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"]
        uuid = subprocess.check_output(uuid_cmd, text=True, creationflags=0x08000000).strip()
        
        serial_cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -Class Win32_DiskDrive | Select-Object -First 1).SerialNumber"]
        disk_serial = subprocess.check_output(serial_cmd, text=True, creationflags=0x08000000).strip()
        
        raw_id = f"{uuid}-{disk_serial}"
        hwid = hashlib.sha256(raw_id.encode('utf-8')).hexdigest()
        return hwid
    except Exception as e:
        print("Error getting HWID:", e)
        import uuid as _uuid
        node_id = str(_uuid.getnode())
        return hashlib.sha256(node_id.encode('utf-8')).hexdigest()

def verify_license_state(act_file, current_hwid, current_time):
    """
    Checks if the license is valid.
    Returns (needs_key_or_expired, data)
    """
    if not os.path.exists(act_file):
        return True, None
    try:
        with open(act_file, 'r', encoding='utf-8') as f:
            enc_str = f.read().strip()
        if not enc_str:
            return True, None
            
        data = decrypt_data(enc_str)
        if not isinstance(data, dict):
            return True, None
            
        # Verify HWID
        if data.get("hwid") != current_hwid:
            print("[License] HWID mismatch!")
            return True, None
            
        # Verify Expiration
        expires_at = data.get("expires_at")
        if expires_at is None or current_time > expires_at:
            print("[License] Key has expired!")
            return True, None
            
        # Verify clock rollback protection
        last_run = data.get("last_run_time", 0.0)
        if current_time < last_run - 86400: # allow 1 day timezone buffer
            print("[License] System clock rollback detected!")
            return True, None
            
        return False, data
    except Exception as e:
        print("[License] Error verifying local license state:", e)
        return True, None

def generate_license(hwid, target_dir, expire_time):
    secret_hex = "90b029c16b17878dfe3a0b5788dbc332304911819ccacc900202d32bfc6f3a18"
    key = secret_hex.encode('utf-8')
    
    # Obfuscated Base64 license key string to prevent string scanning extraction from the binary
    obfuscated_b64 = (
        "N2MmTHE5I3BRMiR2VzFAbVo4IXlZNiprSzVeako0JWhIM19nRzktZkY4K2RENz1zUzZ+YUE1YHBQ"
        "NHxvTzM6aUkyJnVVMSp5WTAhdFQ5QHJSOCNlRTckd1c2JXFRNV5wUDQmb08zKmlJMih1VTEpeVkw"
        "X3RUOS1yUjg9ZUU3K3dXNn5xUTVgcFA0fG9PMzppSTImdVUxKnlZMCF0VDlAclI4I2VFNyR3VzYl"
        "cVE1XnBQNCZvTzMqaUkyKHVVMSl5WTBfdFQ5LXJSOD1lRTcrd1c2fnFRNWBwUDR8b08zOmlJMiZ1"
        "VTEqeVk="
    )
    license_key = base64.b64decode(obfuscated_b64.encode('utf-8')).decode('utf-8')
    
    # Format the actual trial expiration date inside the signed license file
    try:
        dt = datetime.datetime.utcfromtimestamp(expire_time)
    except Exception:
        dt = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=expire_time)
    expire_at_str = dt.strftime("%Y-%m-%dT%H:%M:%S.000000")
    
    payload_dict = {
        "hwid": hwid,
        "last_check": 3786825600.0,
        "license_key": license_key,
        "server_data": {
            "expire_at": expire_at_str,
            "ok": True,
            "reason": None,
            "ui_mode": 1,
            "yt_plan": "pro"
        },
        "server_url": "http://127.0.0.1:9778"
    }
    
    payload_str = json.dumps(payload_dict, separators=(', ', ': '))
    sig = hmac.new(key, payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
    
    out_data = {
        "payload": payload_str,
        "signature": sig
    }
    
    config_dir = os.path.join(target_dir, "storage", "config")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        
    lic_path = os.path.join(config_dir, "yt_tool.lic")
    with open(lic_path, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, indent=4)
    print(f"License generated successfully at: {lic_path}")

    # Write to root storage path (crucial for backend process lookup)
    try:
        root_config_dir = os.path.abspath(os.path.join(target_dir, "..", "..", "..", "storage", "config"))
        if not os.path.exists(root_config_dir):
            os.makedirs(root_config_dir)
        root_lic_path = os.path.join(root_config_dir, "yt_tool.lic")
        with open(root_lic_path, 'w', encoding='utf-8') as f:
            json.dump(out_data, f, indent=4)
        print(f"License written to root config path at: {root_lic_path}")
    except Exception as e:
        print("Error writing root config license:", e)

def find_chromium():
    import winreg
    default_browser = None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
            prog_id, _ = winreg.QueryValueEx(key, "ProgId")
            prog_id_lower = prog_id.lower()
            if "chrome" in prog_id_lower:
                default_browser = "chrome"
            elif "edge" in prog_id_lower or "msedge" in prog_id_lower:
                default_browser = "msedge"
            elif "brave" in prog_id_lower:
                default_browser = "brave"
    except Exception:
        pass

    browsers = ["chrome", "msedge", "brave"]
    if default_browser and default_browser in browsers:
        browsers.remove(default_browser)
        browsers.insert(0, default_browser)

    for b in browsers:
        paths_to_check = [
            rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{b}.exe",
            rf"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\App Paths\{b}.exe"
        ]
        for path in paths_to_check:
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    with winreg.OpenKey(hive, path) as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if os.path.exists(val):
                            return val
                except Exception:
                    pass

    program_files = [
        os.environ.get("PROGRAMFILES", "C:\\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", "")
    ]
    
    relative_paths = [
        r"Google\Chrome\Application\chrome.exe",
        r"BraveSoftware\Brave-Browser\Application\brave.exe",
        r"Microsoft\Edge\Application\msedge.exe",
    ]
    
    for pf in program_files:
        if not pf:
            continue
        for rp in relative_paths:
            full_path = os.path.join(pf, rp)
            if os.path.exists(full_path):
                return full_path
                
    edgecore_base = r"C:\Program Files (x86)\Microsoft\EdgeCore"
    if os.path.exists(edgecore_base):
        optimized = os.path.join(edgecore_base, "Optimized", "msedge.exe")
        if os.path.exists(optimized):
            return optimized
        for root, dirs, files in os.walk(edgecore_base):
            if "msedge.exe" in files:
                return os.path.join(root, "msedge.exe")
                
    return None

def get_dir_size(path):
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_dir_size(entry.path)
    except Exception:
        pass
    return total

def clean_chrome_cache(profile_dir):
    import shutil
    cache_dirs = [
        os.path.join(profile_dir, "Default", "Cache"),
        os.path.join(profile_dir, "Default", "Code Cache"),
        os.path.join(profile_dir, "Default", "GPUCache"),
        os.path.join(profile_dir, "ShaderCache")
    ]
    
    total_size = 0
    for d in cache_dirs:
        if os.path.exists(d):
            total_size += get_dir_size(d)
            
    # Clean only if total size exceeds 500MB (524288000 bytes)
    if total_size > 524288000:
        print(f"Chromium cache size ({total_size} bytes) exceeds 500MB, cleaning up...")
        for d in cache_dirs:
            if os.path.exists(d):
                try:
                    shutil.rmtree(d, ignore_errors=True)
                    print(f"Cleared Chromium cache directory: {d}")
                except Exception:
                    pass
    else:
        print(f"Chromium cache size is {total_size / (1024 * 1024):.2f}MB, retaining cache for performance.")

exit_event = threading.Event()

def maximize_app_window():
    import ctypes
    import time
    
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    ShowWindow = ctypes.windll.user32.ShowWindow
    
    target_hwnd = []
    
    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                title = buff.value
                if "AI Generate Tool" in title or "127.0.0.1:9778" in title:
                    target_hwnd.append(hwnd)
                    return False
        return True
        
    for _ in range(40): # Try for 10 seconds
        if exit_event.is_set():
            break
        EnumWindows(EnumWindowsProc(foreach_window), 0)
        if target_hwnd:
            ShowWindow(target_hwnd[0], 3) # 3 is SW_MAXIMIZE
            break
        time.sleep(0.25)

def check_expiration_loop(target_dir, backend_proc, browser_proc):
    while not exit_event.is_set():
        if exit_event.wait(60):
            break
        if backend_proc.poll() is not None:
            break

def watch_and_copy_videos(target_dir):
    import shutil
    import json
    import urllib.request
    
    app_root = os.path.abspath(os.path.join(target_dir, "..", "..", ".."))
    projects_dir = os.path.join(app_root, "storage", "projects")
    settings_file = os.path.join(target_dir, "config", "settings.json.enc")
    
    last_mtimes = {}
    cached_final_dir = None
    last_settings_mtime = 0.0
    
    while not exit_event.is_set():
        if exit_event.wait(3):
            break
        if not os.path.exists(projects_dir):
            continue
            
        # Check if settings file exists and was modified
        should_fetch_settings = False
        try:
            if os.path.exists(settings_file):
                mtime = os.path.getmtime(settings_file)
                if mtime > last_settings_mtime:
                    should_fetch_settings = True
                    last_settings_mtime = mtime
            elif cached_final_dir is None:
                should_fetch_settings = True
        except Exception:
            should_fetch_settings = True
            
        if should_fetch_settings:
            try:
                req = urllib.request.Request("http://127.0.0.1:9778/api/settings")
                with urllib.request.urlopen(req, timeout=1.0) as response:
                    if response.status == 200:
                        settings_data = json.loads(response.read().decode('utf-8'))
                        cached_final_dir = settings_data.get("final_output_path")
                        print(f"[Watcher] Settings loaded from API. final_output_path={cached_final_dir}")
            except Exception:
                pass
                
        if not cached_final_dir:
            continue
            
        try:
            final_dir = os.path.abspath(cached_final_dir)
            for project_name in os.listdir(projects_dir):
                proj_path = os.path.join(projects_dir, project_name)
                if not os.path.isdir(proj_path):
                    continue
                renders_dir = os.path.join(proj_path, "renders")
                if not os.path.exists(renders_dir):
                    continue
                
                for item in os.listdir(renders_dir):
                    if item.endswith("_final.mp4") or item.endswith(".mp4"):
                        file_path = os.path.join(renders_dir, item)
                        if os.path.isdir(file_path):
                            continue
                            
                        mtime = os.path.getmtime(file_path)
                        if file_path not in last_mtimes or mtime > last_mtimes[file_path]:
                            last_mtimes[file_path] = mtime
                            os.makedirs(final_dir, exist_ok=True)
                            dest_path = os.path.join(final_dir, item)
                            shutil.copy2(file_path, dest_path)
                            print(f"[Watcher] Copied finalized video: {file_path} -> {dest_path}")
        except Exception:
            pass

SPLASH_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ZBizWorld</title>
    <style>
        body {
            background-color: #0d0e12;
            color: #ffffff;
            font-family: system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            overflow: hidden;
            -webkit-user-select: none;
            user-select: none;
        }
        .container {
            text-align: center;
            width: 85%;
        }
        .logo {
            font-size: 26px;
            font-weight: 800;
            letter-spacing: 2px;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status {
            font-size: 13px;
            color: #9ca3af;
            margin-bottom: 12px;
            height: 18px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .progress-container {
            width: 100%;
            height: 4px;
            background-color: #1f2937;
            border-radius: 2px;
            overflow: hidden;
        }
        .progress-bar {
            width: 0%;
            height: 100%;
            background: linear-gradient(90deg, #ef4444 0%, #f87171 100%);
            transition: width 0.1s ease;
            border-radius: 2px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">ZBIZWORLD</div>
        <div class="status" id="status-text">Đang kiểm tra bản cập nhật mới...</div>
        <div class="progress-container">
            <div class="progress-bar" id="progress-bar"></div>
        </div>
    </div>
    <script>
        function updateStatus(text, percent) {
            document.getElementById('status-text').innerText = text;
            document.getElementById('progress-bar').style.width = percent + '%';
        }
    </script>
</body>
</html>
"""

def check_and_run_updates(current_dir):
    config_dir = os.path.join(current_dir, "storage", "config")
    os.makedirs(config_dir, exist_ok=True)
    version_file = os.path.join(config_dir, "app_version.txt")
    last_check_file = os.path.join(config_dir, "last_update_check.txt")
    
    local_version = "1.0.0"
    if os.path.exists(version_file):
        try:
            with open(version_file, "r") as f:
                local_version = f.read().strip()
        except Exception:
            pass
    else:
        try:
            with open(version_file, "w") as f:
                f.write(local_version)
        except Exception:
            pass
            
    # Only check for updates once every 12 hours to ensure instant startup
    current_time = time.time()
    last_check_time = 0.0
    if os.path.exists(last_check_file):
        try:
            with open(last_check_file, "r") as f:
                last_check_time = float(f.read().strip())
        except Exception:
            pass
            
    if current_time - last_check_time < 43200:
        print("[Update] Checked recently. Skipping update check to speed up launch.")
        return

    if not HAS_WEBVIEW:
        print("[Update] Webview not supported, skipping auto-update check.")
        return

    update_finished = threading.Event()
    
    class UpdateAPI:
        def __init__(self):
            self._window = None

    api = UpdateAPI()
    
    def update_thread_proc(window):
        time.sleep(0.5)
        # Log the check attempt to throttle future checks
        try:
            with open(last_check_file, "w") as f:
                f.write(str(current_time))
        except Exception:
            pass
            
        try:
            url = "https://api.github.com/repos/delmuwork-ux/ZBizworld-tool/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "ZBizWorld-Launcher"})
            
            with urllib.request.urlopen(req, timeout=3) as response:
                import json
                release_info = json.loads(response.read().decode())
                
            remote_version = release_info.get("tag_name", "").strip()
            
            if remote_version and remote_version != local_version:
                download_url = None
                for asset in release_info.get("assets", []):
                    if asset.get("name") == "backend_runtime.zip":
                        download_url = asset.get("browser_download_url")
                        break
                        
                if download_url:
                    window.evaluate_js(f"updateStatus('Phát hiện bản cập nhật mới: {remote_version}...', 10)")
                    time.sleep(0.5)
                    
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    zip_path = os.path.join(temp_dir, f"backend_runtime_{remote_version}.zip")
                    
                    req_dl = urllib.request.Request(download_url, headers={"User-Agent": "ZBizWorld-Launcher"})
                    with urllib.request.urlopen(req_dl) as dl_resp:
                        total_size = int(dl_resp.info().get('Content-Length', 0))
                        downloaded = 0
                        block_size = 16384
                        with open(zip_path, 'wb') as f_out:
                            while True:
                                chunk = dl_resp.read(block_size)
                                if not chunk:
                                    break
                                downloaded += len(chunk)
                                f_out.write(chunk)
                                if total_size > 0:
                                    percent = int((downloaded / total_size) * 100)
                                    ui_percent = 10 + int(percent * 0.7) 
                                    window.evaluate_js(f"updateStatus('Đang tải bản cập nhật: {percent}% ({downloaded//1024//1024}/{total_size//1024//1024} MB)...', {ui_percent})")
                                    
                    window.evaluate_js("updateStatus('Đang giải nén và thiết lập cập nhật...', 90)")
                    import zipfile
                    extract_dir = os.path.join(current_dir, "storage", "runtime")
                    
                    os.makedirs(extract_dir, exist_ok=True)
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                        
                    try:
                        with open(version_file, "w") as f:
                            f.write(remote_version)
                    except Exception:
                        pass
                        
                    window.evaluate_js("updateStatus('Cập nhật hoàn tất!', 100)")
                    time.sleep(0.5)
                    try:
                        os.remove(zip_path)
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Update Check] Failed to run update: {e}")
        finally:
            window.destroy()
            update_finished.set()

    splash_window = webview.create_window(
        "ZBizWorld - Khởi động",
        html=SPLASH_HTML,
        width=400,
        height=220,
        resizable=False,
        background_color="#0d0e12",
        js_api=api
    )
    api._window = splash_window
    
    t = threading.Thread(target=update_thread_proc, args=(splash_window,), daemon=True)
    t.start()
    
    webview.start()

if __name__ == "__main__":
    # Prevent multiple instances of the launcher from running concurrently
    try:
        import ctypes
        import time
        mutex_name = "Global\\ZBizWorldAIGenerateProLauncherMutex"
        kernel32 = ctypes.windll.kernel32
        
        acquired = False
        for _ in range(15): # Try 15 times over 3 seconds to allow old instance to close
            mutex = kernel32.CreateMutexW(None, True, mutex_name)
            if kernel32.GetLastError() != 183: # Success, not already exists
                acquired = True
                break
            # Close the handle if it already exists, so we don't leak it
            kernel32.CloseHandle(mutex)
            time.sleep(0.2)
            
        if not acquired:
            sys.exit(0)
            
        # Successfully acquired mutex, allow global cleanup on exit
        should_cleanup = True
    except Exception:
        should_cleanup = True

    # Determine the root application directory {app} and the deep target directory
    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    cleanup_old_mei_directories(current_dir)
    
    # Run auto-updater
    try:
        check_and_run_updates(current_dir)
    except Exception:
        pass
        
    target_dir = os.path.join(current_dir, "storage", "runtime", "bin")
    exe_path = os.path.join(target_dir, "AI_Generate_Tool.exe")
    if not os.path.exists(exe_path):
        exe_path = os.path.join(target_dir, "sys_helper.exe")
    
    # 1. Advanced Secure Validation Logic (Config lies in {app}/storage/config/act_date.enc)
    act_file = os.path.join(current_dir, "storage", "config", "act_date.enc")
    current_hwid = get_hwid()
    
    # Fetch network time in background thread with a short timeout to prevent startup block
    network_time_result = []
    def fetch_time_bg():
        t = get_network_time()
        if t is not None:
            network_time_result.append(t)

    t_thread = threading.Thread(target=fetch_time_bg, daemon=True)
    t_thread.start()
    t_thread.join(timeout=0.5) # Wait at most 0.5 seconds
    
    net_time = network_time_result[0] if network_time_result else None
    current_time = net_time if net_time is not None else time.time()
    
    needs_key, data = verify_license_state(act_file, current_hwid, current_time)
            
    if not needs_key and data:
        # Key is valid locally, verify it online in case it was suspended or extended
        key_code = data.get("license_key")
        if key_code:
            online_ok, online_expires, reason = verify_key_supabase_online(key_code, current_hwid)
            if not online_ok:
                needs_key = True
                # Clean up local license files to prevent offline reuse
                try:
                    if os.path.exists(act_file):
                        os.remove(act_file)
                except Exception:
                    pass
                try:
                    lic_path = os.path.join(target_dir, "storage", "config", "yt_tool.lic")
                    if os.path.exists(lic_path):
                        os.remove(lic_path)
                except Exception:
                    pass
            else:
                if reason == "network_error":
                    # Check offline limit: max 3 days (259200 seconds)
                    last_online = data.get("last_online_check", data.get("activation_time", 0.0))
                    if current_time - last_online > 259200:
                        needs_key = True
                        print("[Offline Check] Offline limit exceeded (3 days). Internet connection required.")
                else:
                    # Successfully verified online, update last_online_check timestamp
                    data["last_online_check"] = current_time

                if online_expires:
                    # Update local expires_at in case it was extended
                    data["expires_at"] = parse_iso_datetime(online_expires)

    just_activated = False
    if needs_key:
        if HAS_WEBVIEW:
            ok, expires_at_str, license_key = check_password_html(current_hwid)
            try:
                import subprocess
                import time
                subprocess.run('taskkill /F /IM msedgewebview2.exe', shell=True, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(0.6)
            except Exception:
                pass
        elif HAS_TK:
            print("[GUI] Webview not found. Falling back to Tkinter GUI.")
            ok, expires_at_str, license_key = check_password_tkinter(current_hwid)
        else:
            print("[GUI] Webview & Tkinter not found. Falling back to PowerShell WinForms.")
            ok, expires_at_str, license_key = check_password_powershell(current_hwid)
        if not ok:
            sys.exit(0)
            
        expire_time = parse_iso_datetime(expires_at_str)
        data = {
            "hwid": current_hwid,
            "activation_time": current_time,
            "last_run_time": current_time,
            "expires_at": expire_time,
            "license_key": license_key,
            "last_online_check": current_time
        }
        just_activated = True
    else:
        # Advance the last run timestamp safely
        if current_time > data.get("last_run_time", 0.0):
            data["last_run_time"] = current_time
            
    try:
        os.makedirs(os.path.dirname(act_file), exist_ok=True)
        with open(act_file, 'w', encoding='utf-8') as f:
            f.write(encrypt_data(data))
    except Exception:
        sys.exit(0)

    if just_activated:
        try:
            current_exe = sys.executable
            # Start the new instance in a completely detached process inheriting standard parent env (no _MEIPASS deletion)
            if getattr(sys, 'frozen', False):
                subprocess.Popen([current_exe] + sys.argv[1:], env=None, creationflags=0x08000008, close_fds=True)
            else:
                subprocess.Popen([current_exe, sys.argv[0]] + sys.argv[1:], env=None, creationflags=0x08000008, close_fds=True)
        except Exception:
            pass
        sys.exit(0)

    # 2. Main app launch logic
    if os.path.exists(exe_path):
        # Force terminate any lingering backend processes from a previous run to avoid port 9778 conflicts
        try:
            exe_name = os.path.basename(exe_path)
            subprocess.run(["taskkill", "/f", "/im", exe_name], creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5) # Give the OS time to release the port
        except Exception:
            pass
            
        hwid = get_hwid()
        
        # Calculate the actual expiration timestamp from saved data
        expire_time = data.get("expires_at", data.get("activation_time", current_time) + 30 * 24 * 3600)
        generate_license(hwid, target_dir, expire_time)
        
        # Clean PyInstaller environment variables to prevent Python 3.10 vs 3.12 library conflicts in the backend process
        app_env = os.environ.copy()
        for var in ["PYTHONPATH", "PYTHONHOME", "_MEIPASS"]:
            if var in app_env:
                del app_env[var]
                
        # Force the backend to use the correct local storage directory on the D: drive
        app_env["STORAGE_DIR"] = os.path.abspath(os.path.join(current_dir, "storage"))
        app_env["CLOAKBROWSER_CACHE_DIR"] = os.path.abspath(os.path.join(current_dir, "storage", "cloakbrowser"))
                
        # Disable automatic browser opening
        app_env["SKIP_BROWSER_OPEN"] = "1"
        app_env["skip_browser_open"] = "1"
        
        # Log backend output to file for debugging launcher startup crashes
        log_path = os.path.join(target_dir, "backend_launch.log")
        try:
            log_file = open(log_path, "w", encoding="utf-8")
        except Exception:
            log_file = None
            
        # Start application backend
        backend_proc = subprocess.Popen(
            [exe_path], 
            cwd=target_dir, 
            env=app_env, 
            stdout=log_file,
            stderr=log_file,
            creationflags=0x08000000,
            close_fds=True
        )
        
        browser_proc = None
        skip_backend_kill = [False]
        
        def cleanup_processes():
            if skip_backend_kill[0]:
                return
            global browser_proc
            exit_event.set()
            if browser_proc:
                try:
                    subprocess.run(f"taskkill /F /T /PID {browser_proc.pid}", shell=True, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    try:
                        browser_proc.terminate()
                    except Exception:
                        pass
            try:
                subprocess.run(f"taskkill /F /T /PID {backend_proc.pid}", shell=True, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                try:
                    backend_proc.terminate()
                    backend_proc.wait(timeout=1.5)
                except Exception:
                    try:
                        backend_proc.kill()
                        backend_proc.wait()
                    except Exception:
                        pass
            time.sleep(0.5)
                    
        import atexit
        atexit.register(cleanup_processes)
        
        # Wait for backend server (up to 10 minutes to accommodate first-time dependency downloads)
        import socket
        server_ready = False
        for i in range(6000): # 6000 * 0.1s = 600 seconds (10 minutes) max wait
            try:
                with socket.create_connection(("127.0.0.1", 9778), timeout=0.1):
                    server_ready = True
                    break
            except Exception:
                if i % 50 == 0: # Print status every 5 seconds
                    print(f"[Launcher] Waiting for backend server to initialize... (elapsed: {i*0.1:.1f}s)")
                time.sleep(0.1)
              
        if server_ready:
            # Start background watcher for copying video outputs to custom path
            try:
                watcher_thread = threading.Thread(target=watch_and_copy_videos, args=(target_dir,), daemon=True)
                watcher_thread.start()
            except Exception:
                pass

            chrome_exe = find_chromium()
            if chrome_exe:
                profile_dir = os.path.join(current_dir, "storage", "app_chrome_profile")
                try:
                    os.makedirs(profile_dir, exist_ok=True)
                    lock_file = os.path.join(profile_dir, "SingletonLock")
                    if os.path.exists(lock_file):
                        try:
                            os.remove(lock_file)
                        except Exception:
                            pass
                    clean_chrome_cache(profile_dir)
                except Exception:
                    pass
 
                # Start the browser process with optimizations for low-end PCs (disable sync/extensions, limit process & heap size)
                chrome_args = [
                    chrome_exe,
                    "--app=http://127.0.0.1:9778",
                    f"--user-data-dir={profile_dir}",
                    "--start-maximized",
                    "--disable-background-mode",
                    "--disable-extensions",
                    "--disable-sync",
                    "--ignore-gpu-blocklist",
                    "--enable-gpu-rasterization",
                    "--enable-zero-copy"
                ]
                browser_proc = subprocess.Popen(chrome_args, close_fds=True)
                
                # Start background trial check thread
                try:
                    check_thread = threading.Thread(target=check_expiration_loop, args=(target_dir, backend_proc, browser_proc), daemon=True)
                    check_thread.start()
                except Exception:
                    pass
                
                # Maximize window
                try:
                    threading.Thread(target=maximize_app_window, daemon=True).start()
                except Exception:
                    pass
                
                # Block until the browser window is closed
                start_wait_time = time.time()
                browser_proc.wait()
                wait_duration = time.time() - start_wait_time
                
                # Browser closed, terminate backend server
                # Note: if the browser process exited in under 5.0 seconds, it's highly likely
                # a delegation launch to a running instance (or it exited due to profile lock).
                # In this case, do NOT kill the backend, let it run.
                if wait_duration > 5.0:
                    cleanup_processes()
                else:
                    skip_backend_kill[0] = True
            else:
                import webbrowser
                webbrowser.open("http://127.0.0.1:9778")
                # Show blocking dialog for non-chrome browsers so backend isn't left orphaned
                show_windows_message("AI Generate Tool", "Phần mềm đang chạy ngầm trên cổng 9778.\n\nNhấn OK để tắt phần mềm hoàn toàn.", "info")
                cleanup_processes()
        else:
            # Prepare detailed diagnostic error message
            error_msg = (
                "Không thể kết nối đến máy chủ dịch vụ của ứng dụng (Port 9778).\\n\\n"
                "Nguyên nhân có thể do:\\n"
                "1. Máy chủ bị Windows Defender hoặc phần mềm diệt virus chặn (hãy tạm tắt để thử lại).\\n"
                "2. Cổng mạng 9778 đang bị chiếm dụng bởi một phần mềm khác.\\n"
                "3. Thiếu thư viện hệ thống Windows (như VC++ Redistributable).\\n\\n"
                "Vui lòng liên hệ Admin để được hỗ trợ kỹ thuật."
            )
            
            # Read last few lines from backend_launch.log to extract the exact traceback/error
            try:
                log_path = os.path.join(target_dir, "backend_launch.log")
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                        lines = lf.readlines()
                        if lines:
                            last_err = "".join(lines[-5:]).strip()
                            if last_err:
                                error_msg += f"\n\nChi tiết lỗi từ hệ thống:\n{last_err}"
            except Exception:
                pass
                
            clean_error_msg = error_msg.replace("\\n", "\n")
            show_windows_message("Lỗi Khởi Động", clean_error_msg, "error")
            sys.exit(1)
    else:
        pass
