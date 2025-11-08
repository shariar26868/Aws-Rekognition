# cleanup_normal_db.py
# Normal DynamoDB থেকে invalid entries remove করুন

import boto3
from backend.services.aws_service import AWSService

aws = AWSService()

print("\n" + "="*70)
print("🧹 CLEANING UP NORMAL DATABASE")
print("="*70)

# 1. Check current state
print("\n1️⃣ Current DynamoDB State:")
table = aws.dynamodb.Table("facelookalike")
response = table.scan()
items = response.get('Items', [])

print(f"   Total entries: {len(items)}")
print("\n   Checking each entry:")

invalid_entries = []
valid_entries = []

for item in items:
    face_id = item.get('RekognitionId')
    full_name = item.get('FullName', 'Unknown')
    image_key = item.get('ImageKey', None)
    
    if not image_key:
        print(f"   ❌ INVALID: {full_name[:60]} (No ImageKey)")
        invalid_entries.append((face_id, full_name))
    else:
        print(f"   ✅ VALID: {full_name[:60]}")
        valid_entries.append(item)

# 2. Delete invalid entries
if invalid_entries:
    print(f"\n2️⃣ Deleting {len(invalid_entries)} invalid entries...")
    for face_id, name in invalid_entries:
        try:
            table.delete_item(Key={'RekognitionId': face_id})
            print(f"   🗑️  Deleted: {name[:60]}")
            
            # Also delete from Rekognition collection
            try:
                aws.rekognition.delete_faces(
                    CollectionId="image_collections",
                    FaceIds=[face_id]
                )
                print(f"   🗑️  Also deleted from Rekognition collection")
            except Exception as e:
                print(f"   ⚠️  Could not delete from collection: {str(e)}")
                
        except Exception as e:
            print(f"   ❌ Failed to delete {face_id}: {str(e)}")
else:
    print("\n2️⃣ No invalid entries to delete")

# 3. Check S3 images
print("\n3️⃣ Checking S3 images...")
s3_keys = aws.debug_s3_keys("celebrity-lookalike-face-rekognition", "index")

# 4. Check if S3 images are in DynamoDB
print("\n4️⃣ Cross-checking S3 ↔ DynamoDB:")
valid_image_keys = [item['ImageKey'] for item in valid_entries]

missing_images = []
for s3_key in s3_keys:
    if s3_key in valid_image_keys:
        print(f"   ✅ {s3_key} → IN DATABASE")
    else:
        print(f"   ⚠️  {s3_key} → NOT IN DATABASE (needs re-indexing)")
        missing_images.append(s3_key)

# 5. Summary
print("\n" + "="*70)
print("📊 CLEANUP SUMMARY")
print("="*70)
print(f"   • Valid entries: {len(valid_entries)}")
print(f"   • Deleted entries: {len(invalid_entries)}")
print(f"   • S3 images: {len(s3_keys)}")
print(f"   • Missing in DB: {len(missing_images)}")
print("="*70)

if missing_images:
    print("\n⚠️  WARNING: Some S3 images are not indexed!")
    print("💡 Solution Options:")
    print("\n   Option 1: Re-upload missing images using /normal/add")
    print("   Option 2: Delete unindexed S3 images")
    print("\nMissing images:")
    for s3_key in missing_images:
        filename = s3_key.split('/')[-1]
        # Extract original filename (remove UUID prefix)
        parts = filename.split('_', 1)
        original_name = parts[1] if len(parts) > 1 else filename
        print(f"   • {original_name}")

print("\n✅ Cleanup complete!")
print("\n💡 Next Step: Try searching again with a valid image")
print("="*70 + "\n")

# 6. Final verification
print("🔍 FINAL STATUS CHECK:")
collection_info = aws.debug_collection_status("image_collections")
ddb_items = aws.debug_dynamodb_table("facelookalike")

if collection_info.get('FaceCount', 0) == len(ddb_items):
    print("✅ Collection and DynamoDB are now in sync!")
else:
    print("⚠️  Still some mismatch - may need manual intervention")