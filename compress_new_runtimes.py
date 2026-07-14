import os
import zipfile
import time

def zip_directory(folder_path, output_zip):
    print(f"Starting compression of '{folder_path}' to '{output_zip}'...")
    start_time = time.time()
    
    # Exclude personal keys, logs and cache directories
    excludes = ['settings.json.enc', 'backend_launch.log']
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for root, dirs, files in os.walk(folder_path):
            # Skip python cache, projects, chrome profiles and log directories
            path_parts = root.replace('\\', '/').split('/')
            if any(part in path_parts for part in ['__pycache__', '.pytest_cache', 'projects', 'chrome_profiles', 'logs']):
                continue
            for file in files:
                if file in excludes or file.endswith('.log') or file.endswith('.bak') or file.endswith('.tmp'):
                    continue
                file_path = os.path.join(root, file)
                # Resolve relative path inside the zip
                rel_path = os.path.relpath(file_path, folder_path)
                zip_ref.write(file_path, rel_path)
                
    elapsed = time.time() - start_time
    print(f"SUCCESS: Compressed to {output_zip} in {elapsed:.1f} seconds!")

if __name__ == "__main__":
    cloak_src = r"D:\all my code stuff\Ai-new\AI_Generate_Tool\storage\cloakbrowser"
    cloak_dst = r"D:\all my code stuff\Ai-new\cloakbrowser.zip"
    
    runtime_src = r"D:\all my code stuff\Ai-new\AI_Generate_Tool\storage\runtime"
    runtime_dst = r"D:\all my code stuff\Ai-new\backend_runtime.zip"
    
    # 1. Compress cloakbrowser
    if os.path.exists(cloak_src):
        zip_directory(cloak_src, cloak_dst)
    else:
        print(f"Error: Source folder not found: {cloak_src}")
        
    # 2. Compress backend runtime
    if os.path.exists(runtime_src):
        zip_directory(runtime_src, runtime_dst)
    else:
        print(f"Error: Source folder not found: {runtime_src}")
