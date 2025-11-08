# cleanup_celebrity_db.py
# DynamoDB থেকে invalid entries remove করুন এবং re-index করুন

import boto3
from backend.services.aws_service import AWSService

aws = AWSService()

print("\n" + "="*70)
print("🧹 CLEANING UP CELEBRITY DATABASE")
print("="*70)

# 1. Check current state
print("\n1️⃣ Current DynamoDB State:")
table = aws.dynamodb.Table("celebrity-dynamo-table")
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
        print(f"   ❌ INVALID: {full_name[:50]} (No ImageKey)")
        invalid_entries.append(face_id)
    else:
        print(f"   ✅ VALID: {full_name[:50]}")
        valid_entries.append(item)

# 2. Delete invalid entries
if invalid_entries:
    print(f"\n2️⃣ Deleting {len(invalid_entries)} invalid entries...")
    for face_id in invalid_entries:
        try:
            table.delete_item(Key={'RekognitionId': face_id})
            print(f"   🗑️  Deleted: {face_id}")
        except Exception as e:
            print(f"   ❌ Failed to delete {face_id}: {str(e)}")
else:
    print("\n2️⃣ No invalid entries to delete")

# 3. Check S3 images
print("\n3️⃣ Checking S3 images...")
s3_keys = aws.debug_s3_keys("celebrity-lookalike-celebrity-lookalike", "celebritybucket")

# 4. Check if S3 images are in DynamoDB
print("\n4️⃣ Cross-checking S3 ↔ DynamoDB:")
valid_image_keys = [item['ImageKey'] for item in valid_entries]

for s3_key in s3_keys:
    if s3_key in valid_image_keys:
        print(f"   ✅ {s3_key} → IN DATABASE")
    else:
        print(f"   ⚠️  {s3_key} → NOT IN DATABASE (needs re-indexing)")

# 5. Summary
print("\n" + "="*70)
print("📊 CLEANUP SUMMARY")
print("="*70)
print(f"   • Valid entries: {len(valid_entries)}")
print(f"   • Deleted entries: {len(invalid_entries)}")
print(f"   • S3 images: {len(s3_keys)}")
print("="*70)

if len(valid_entries) < len(s3_keys):
    print("\n⚠️  WARNING: Some S3 images are not indexed!")
    print("💡 Solution: Re-upload those images using /celebrity/add endpoint")
    print("\nMissing images:")
    for s3_key in s3_keys:
        if s3_key not in valid_image_keys:
            print(f"   • {s3_key}")

print("\n✅ Cleanup complete! Now try searching again.")
print("="*70 + "\n")