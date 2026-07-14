import subprocess
import os
import shutil

# Make sure we run PyInstaller to build html_installer.py as a lightweight web bootstrapper
cmd = [
    "pyinstaller",
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--uac-admin",
    "--name=Setup_AI_Generate_Tool_Pro_HTML",
    "--icon=Zbiz.ico",
    "html_installer.py"
]

print("Running PyInstaller to compile the premium HTML installer...")
try:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode == 0:
        print("SUCCESS: HTML installer compiled successfully!")
        
        # Copy compiled installer to target folder D:\all my code stuff\Ai-new
        src_exe = r"D:\all my code stuff\Ai-new\AI_Generate_Tool\dist\Setup_AI_Generate_Tool_Pro_HTML.exe"
        dst_exe = r"D:\all my code stuff\Ai-new\Setup_AI_Generate_Tool_Pro_HTML.exe"
        
        if os.path.exists(src_exe):
            print(f"Copying {src_exe} to {dst_exe}...")
            shutil.copy(src_exe, dst_exe)
            print("Successfully copied to destination!")
        else:
            print("Error: Compiled file not found in dist/ folder!")
    else:
        print(f"FAILED: Return code {result.returncode}")
        print("Stdout:")
        print(result.stdout)
        print("Stderr:")
        print(result.stderr)
except Exception as e:
    print(f"Exception during build: {e}")
