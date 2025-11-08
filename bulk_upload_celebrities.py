# ============ bulk_upload_celebrities.py ============
# Run this script to upload all celebrities from a folder

import os
import requests
from pathlib import Path

# Config - এখানে আপনার celebrity folder path set করুন
CELEBRITY_FOLDER = "./celebrities"  # এটা আপনার path অনুযায়ী change করুন
API_URL = "http://localhost:8000/celebrity/add"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

def get_celebrity_images(folder_path: str) -> list:
    """Celebrity folder থেকে সব image files পাবে"""
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return []
    
    images = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            ext = Path(filename).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                images.append(file_path)
    
    return images

def upload_celebrities(images: list, batch_size: int = 5):
    """AWS-এ celebrities upload করবে batch এ"""
    if not images:
        print("❌ No valid images found!")
        return
    
    print(f"\n🎬 Found {len(images)} celebrity images")
    print(f"📤 Starting upload in batches of {batch_size}...\n")
    
    total_uploaded = 0
    total_failed = 0
    
    # Batch করে upload করুন
    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(images) + batch_size - 1) // batch_size
        
        print(f"📦 Batch {batch_num}/{total_batches} ({len(batch)} images)")
        
        # Prepare files for upload
        files = []
        for image_path in batch:
            try:
                with open(image_path, 'rb') as f:
                    files.append(('files', (os.path.basename(image_path), f.read())))
            except Exception as e:
                print(f"   ❌ Error reading {os.path.basename(image_path)}: {str(e)}")
                total_failed += 1
                continue
        
        # Upload batch
        try:
            response = requests.post(
                API_URL,
                files=files,
                data={'folder': 'celebritybucket'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                success = len(result.get('results', []))
                errors = len(result.get('errors', []))
                
                print(f"   ✓ Uploaded: {success} | Failed: {errors}")
                total_uploaded += success
                total_failed += errors
                
                # Show errors if any
                if errors > 0:
                    for error in result.get('errors', []):
                        print(f"      - {error.get('filename')}: {error.get('message')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                total_failed += len(batch)
        
        except Exception as e:
            print(f"   ❌ Request error: {str(e)}")
            total_failed += len(batch)
    
    print(f"\n" + "="*60)
    print(f"✅ Upload Complete!")
    print(f"   - Total Uploaded: {total_uploaded}")
    print(f"   - Total Failed: {total_failed}")
    print(f"="*60)

def main():
    print("="*60)
    print("🎬 CELEBRITY BULK UPLOAD TOOL")
    print("="*60)
    print(f"\n📁 Celebrity folder: {CELEBRITY_FOLDER}")
    print(f"🌐 API URL: {API_URL}")
    
    # Get images
    images = get_celebrity_images(CELEBRITY_FOLDER)
    
    if not images:
        print("\n❌ No images found in celebrity folder!")
        return
    
    # Confirm
    print(f"\n📊 Found {len(images)} images:")
    for img in images[:5]:
        print(f"   - {os.path.basename(img)}")
    if len(images) > 5:
        print(f"   ... and {len(images) - 5} more")
    
    response = input(f"\n🚀 Upload these {len(images)} images? (yes/no): ").lower()
    if response != 'yes':
        print("Cancelled.")
        return
    
    # Upload
    upload_celebrities(images, batch_size=5)

if __name__ == "__main__":
    main()