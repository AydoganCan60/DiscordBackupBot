import os
import requests
import json
import zipfile
import math
import time
import shutil
import subprocess
# from pathlib import Path # Gerekli değil gibi görünüyor, yorumlandı.

class DiscordBackup:
    def __init__(self):
        # Load settings
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.token = self.config['discord_token']
        self.server_id = self.config['server_id']
        self.category_id = self.config.get('category_id', None) # 'kategori_id' -> 'category_id'
        self.headers = {
            'Authorization': f'Bot {self.token}',
            'Content-Type': 'application/json'
        }
        # Set to 10 MB
        self.MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
        
        # Specify the path to WinRAR. Adjust according to your system.
        # self.rar_path = r"C:\Program Files\WinRAR\Rar.exe" # Or the actual path to rar.exe
        # Alternatively, if rar.exe is in your PATH, you can just use "rar".
        # The line below assumes the rar command works directly. If not, specify the full path as above.
        self.rar_path = r"C:\Program Files\WinRAR\Rar.exe" # Or "rar" or "unrar" or the full path

    def create_channel(self, channel_name):
        """Creates a Discord text channel."""
        try:
            url = f"https://discord.com/api/v10/guilds/{self.server_id}/channels"
            data = {
                "name": channel_name.lower().replace(' ', '-').replace('.', '-').replace('_', '-'),
                "type": 0,  # Text channel
                "parent_id": self.category_id if self.category_id else None
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            if response.status_code == 201:
                channel_data = response.json()
                print(f"✅ Channel created: {channel_name} (ID: {channel_data['id']})")
                return channel_data['id']
            else:
                print(f"❌ Channel creation error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Channel creation error: {e}")
            return None
    
    def create_webhook(self, channel_id, webhook_name):
        """Creates a webhook for a channel."""
        try:
            url = f"https://discord.com/api/v10/channels/{channel_id}/webhooks"
            # Remove "discord" from the name and make it safe
            safe_webhook_name = webhook_name.lower().replace('discord', 'backup').replace('  ', ' ').strip()
            # If all letters are removed or it's too short, use a default name
            if not safe_webhook_name or len(safe_webhook_name) < 2:
                safe_webhook_name = "project-backup"
            # Webhook name max 80 characters
            safe_webhook_name = safe_webhook_name[:80]
            data = {
                "name": safe_webhook_name
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            if response.status_code == 200:
                webhook_data = response.json()
                webhook_url = f"https://discord.com/api/webhooks/{webhook_data['id']}/{webhook_data['token']}"
                print(f"✅ Webhook created: {safe_webhook_name}")
                return webhook_url
            else:
                print(f"❌ Webhook creation error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Webhook creation error: {e}")
            return None
    
    def send_file(self, file_path, webhook_url, description=""):
        """Sends a file via webhook."""
        try:
            # Check file size (based on 10 MB limit)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024: # 10 MB check
                print(f"❌ File too large: {file_size / (1024*1024):.2f} MB (Limit: 10 MB)")
                return False
                
            print(f"📤 Sending: {os.path.basename(file_path)} ({file_size / (1024*1024):.2f} MB)")
            
            with open(file_path, 'rb') as f:
                files = {"file": (os.path.basename(file_path), f)}
                data = {}
                if description:
                    data["content"] = description[:2000]  # Discord message limit
                
                response = requests.post(webhook_url, files=files, data=data, timeout=60)
                
                # Rate limit check
                if response.status_code == 429:
                    retry_after = response.json().get('retry_after', 5)
                    print(f"⏳ Rate limit! Waiting {retry_after} seconds...")
                    time.sleep(retry_after + 1)
                    return self.send_file(file_path, webhook_url, description)
                
                # 413 error check (Request entity too large)
                if response.status_code == 413:
                    print(f"❌ 413 Error - File still too large: {file_path}")
                    print(f"   Actual size: {file_size / (1024*1024):.2f} MB")
                    print(f"   Response: {response.text}")
                    return False
                    
                if response.status_code in [200, 204]:
                    print(f"✅ Sent: {os.path.basename(file_path)}")
                    return True
                else:
                    print(f"❌ Send error: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False

    def rar_file(self, file_path, rar_name, max_size_mb=9):
        """
        Converts a file to RAR format and splits it into parts.
        RAR parts are named: rar_name.part1.rar, rar_name.part2.rar, ...
        """
        try:
            # WinRAR command-line command
            # -m0: Compression level (0=fastest, 5=best)
            # -v{max_size_mb}m: Volume size for each part (in MB)
            # {rar_name}.rar: Name of the RAR file to create (including extension)
            # {file_path}: File to compress
            cmd = [
                self.rar_path, 'a', 
                '-m0', 
                f'-v{max_size_mb}m', 
                rar_name + '.rar', 
                file_path
            ]

            print(f"📦 Creating RAR file: {rar_name}.rar (max {max_size_mb} MB parts)")
            
            # Run the command - Prevent UnicodeDecodeError by using text=False and handling stdout/stderr as binary
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                check=True,
                text=False # Use binary mode instead of text=True
            )
            
            # stdout and stderr come as bytes. Decode safely if needed.
            # print("RAR STDOUT:", result.stdout.decode('utf-8', errors='ignore'))
            # print("RAR STDERR:", result.stderr.decode('utf-8', errors='ignore'))
            
            # Find the created RAR parts
            parts = []
            folder = os.path.dirname(rar_name) if os.path.dirname(rar_name) else "."
            base_name = os.path.basename(rar_name)
            
            # Look for .rar, .r00, .r01, ... files
            for item in os.listdir(folder):
                if item.startswith(base_name) and (item.endswith('.rar') or item.endswith('.r00') or item.endswith('.r01') or (item.endswith('.r') and item[:-1].endswith('.')) or '.r' in item.split('.')[-1]):
                     # Safer check
                     if len(item.split('.')) >= 2:
                         ext = item.split('.')[-1]
                         if ext == 'rar' or (ext.startswith('r') and ext[1:].isdigit() and len(ext) == 3):
                             part_path = os.path.join(folder, item)
                             if os.path.isfile(part_path):
                                 parts.append(part_path)
                                 print(f"   📄 RAR Part: {item} ({os.path.getsize(part_path) / (1024*1024):.2f} MB)")

            # Sort parts (important!)
            # Order: .rar, .r00, .r01, ...
            def sort_key(x):
                ext = os.path.splitext(x)[1]
                if ext == '.rar': return (0, 0)
                elif ext.startswith('.r') and ext[1:].isdigit() and len(ext) == 4: return (1, int(ext[1:])) # .r00, .r01
                else: return (2, 0) # Others last
            
            parts.sort(key=sort_key)
            
            # Rename: .rar -> .part1.rar, .r00 -> .part2.rar, .r01 -> .part3.rar, ...
            renamed_parts = []
            for i, part in enumerate(parts):
                new_name = f"{base_name}.part{i+1}.rar"
                new_path = os.path.join(folder, new_name)
                
                # If already the correct name, no need to move
                if os.path.basename(part) == new_name:
                    renamed_parts.append(part)
                else:
                    try:
                        os.rename(part, new_path)
                        renamed_parts.append(new_path)
                        print(f"   🔄 Renamed: {os.path.basename(part)} -> {new_name}")
                    except OSError as e:
                        print(f"   ⚠️  Rename error ({part}): {e}")
                        # Keep the old name
                        renamed_parts.append(part)
                        
            print(f"✅ RAR file created and split into {len(renamed_parts)} parts.")
            return renamed_parts

        except subprocess.CalledProcessError as e:
            print(f"❌ RAR creation error (subprocess): {e}")
            # stderr comes as bytes, decode safely
            if e.stderr:
                try:
                    print(f"   STDERR: {e.stderr.decode('utf-8', errors='ignore')}")
                except Exception:
                    print(f"   STDERR (could not decode): {e.stderr[:200]}...") # First 200 bytes
            if e.stdout:
                 try:
                    print(f"   STDOUT: {e.stdout.decode('utf-8', errors='ignore')}")
                 except Exception:
                    print(f"   STDOUT (could not decode): {e.stdout[:200]}...")
            return []
        except FileNotFoundError:
            print(f"❌ RAR program not found: {self.rar_path}")
            print("   Please ensure WinRAR is installed and rar.exe is in your PATH or provide the correct path.")
            return []
        except Exception as e:
            print(f"❌ RAR creation error (general): {e}")
            import traceback
            traceback.print_exc()
            return []

    
    def zip_folder(self, folder_path, zip_name):
        """Compresses a folder into a ZIP file."""
        print(f"📦 Compressing: {os.path.basename(folder_path)}")
        
        # Create a safe filename
        safe_zip_name = "".join(c for c in zip_name if c.isalnum() or c in ('-', '_', '.')).rstrip()
        if not safe_zip_name.endswith('.zip'):
            safe_zip_name += '.zip'
        
        with zipfile.ZipFile(safe_zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        arcname = os.path.relpath(file_path, folder_path)
                        # Prevent issues with Turkish characters and special characters
                        arcname = arcname.replace('\\', '/').encode('ascii', errors='ignore').decode('ascii')
                        zipf.write(file_path, arcname)
                    except Exception as e:
                        print(f"⚠️  File skipped (character error): {file_path}")
                        continue
        
        size = os.path.getsize(safe_zip_name)
        print(f"📁 ZIP size: {size / (1024*1024):.2f} MB")
        return safe_zip_name
    
    # The `split_file` function is no longer used directly, replaced by RAR.
    # def split_file(self, file_path, max_size=None):
    #     ...
    
    def backup_project(self, project_folder):
        """Backs up a single project."""
        project_name = os.path.basename(project_folder)
        print(f"\n🚀 Backing up: {project_name}")
        
        # 1. Create channel
        channel_id = self.create_channel(project_name)
        if not channel_id:
            print(f"❌ Could not create channel: {project_name}")
            return
        
        time.sleep(2)  # Rate limit prevention
        
        # 2. Create webhook
        webhook_url = self.create_webhook(channel_id, f"{project_name}-backup")
        if not webhook_url:
            print(f"❌ Could not create webhook: {project_name}")
            return
        
        time.sleep(2)
        
        # 3. ZIP the folder
        zip_name = f"{project_name}.zip"
        zip_name = self.zip_folder(project_folder, zip_name)
        
        # 4. Convert ZIP to RAR and split into parts
        # Use 9 MB for safety margin (Discord allows up to 10 MB)
        rar_parts = self.rar_file(zip_name, os.path.join("temp", project_name), max_size_mb=9)
        
        if not rar_parts:
            print(f"❌ Could not create RAR file for {project_name}.")
            # Cleanup
            if os.path.exists(zip_name):
                os.remove(zip_name)
            return
        
        # 5. Send RAR parts
        total_parts = len(rar_parts)
        print(f"📤 Total {total_parts} RAR parts to send")
        
        for i, part in enumerate(rar_parts):
            description = f"📦 Part {i+1}/{total_parts}" if total_parts > 1 else "📦 Backup file (RAR)"
            success = self.send_file(part, webhook_url, description)
            if not success:
                print(f"❌ {part} could not be sent, continuing...")
            time.sleep(3)  # Rate limit prevention (3 seconds)
        
        # 6. Clean up temporary files
        # Delete the ZIP file
        if os.path.exists(zip_name):
            os.remove(zip_name)
            print(f"🗑️  ZIP file deleted: {zip_name}")
        
        # Delete RAR parts
        for part in rar_parts:
             if os.path.exists(part):
                try:
                    os.remove(part)
                except Exception as e:
                    print(f"⚠️  Could not delete part: {part} - {e}")
        
        print(f"✅ {project_name} backed up and sent as RAR!")
    
    def backup_all_projects(self):
        """Backs up all projects."""
        print("🚀 Backing up all projects...")
        
        if not os.path.exists('projects'): # 'projeler' -> 'projects'
            print("❌ 'projects' folder not found!")
            return
        
        projects = [f for f in os.listdir('projects') 
                   if os.path.isdir(os.path.join('projects', f))]
        
        if not projects:
            print("❌ No projects found in 'projects' folder!")
            return
        
        print(f"📁 Found {len(projects)} projects")
        
        for project in projects:
            project_path = os.path.join('projects', project)
            try:
                self.backup_project(project_path)
                time.sleep(3)  # Rate limit prevention
            except Exception as e:
                print(f"❌ Error backing up {project}: {e}")
                import traceback
                traceback.print_exc()
        
        # Clean up temp folder (if empty)
        if os.path.exists("temp") and not os.listdir("temp"): # 'gecici' -> 'temp'
            try:
                shutil.rmtree("temp")
                print("🗑️  Temp folder cleaned up")
            except Exception as e:
                print(f"⚠️  Could not clean up temp folder: {e}")
        elif os.path.exists("temp"):
             print("⚠️  Temp folder is not empty, not deleted.")
        
        print("\n🎉 All projects backed up!")

def main():
    try:
        backup = DiscordBackup()
        backup.backup_all_projects()
    except Exception as e:
        print(f"❌ General error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()