# fresh_normal_start.py
# Complete fresh start for normal lookalike system

import boto3
from backend.services.aws_service import AWSService

aws = AWSService()

print("\n" + "="*70)
print("🗑️  FRESH START - CLEANING ALL NORMAL DATA")
print("="*70)
print("\n⚠️  WARNING: This will delete all normal lookalike data!")
print("    - Rekognition faces")
print("    - DynamoDB entries")
print("    - S3 images")

response = input("\nAre you sure? Type 'YES' to continue: ")

if response != "YES":
    print("❌ Cancelled")
    exit()

bucket = "celebrity-lookalike-face-rekognition"
collection = "image_collections"
table_name = "facelookalike"

# 1. Delete all faces from Rekognition collection
print("\n1️⃣ Cleaning Rekognition Collection...")
try:
    response = aws.rekognition.list_faces(CollectionId=collection, MaxResults=100)
    face_ids = [face['FaceId'] for face in response.get('Faces', [])]
    
    if face_ids:
        print(f"   Found {len(face_ids)} faces to delete")
        aws.rekognition.delete_faces(CollectionId=collection, FaceIds=face_ids)
        print(f"   ✅ Deleted {len(face_ids)} faces")
    else:
        print("   ✅ Collection already empty")
except Exception as e:
    print(f"   ⚠️  Error: {str(e)}")

# 2. Delete all DynamoDB entries
print("\n2️⃣ Cleaning DynamoDB Table...")
try:
    table = aws.dynamodb.Table(table_name)
    response = table.scan()
    items = response.get('Items', [])
    
    if items:
        print(f"   Found {len(items)} entries to delete")
        for item in items:
            table.delete_item(Key={'RekognitionId': item['RekognitionId']})
        print(f"   ✅ Deleted {len(items)} entries")
    else:
        print("   ✅ Table already empty")
except Exception as e:
    print(f"   ⚠️  Error: {str(e)}")

# 3. Delete all S3 images in index folder
print("\n3️⃣ Cleaning S3 Bucket...")
try:
    paginator = aws.s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix="index/")
    
    delete_count = 0
    for page in pages:
        objects = page.get('Contents', [])
        if objects:
            delete_keys = [{'Key': obj['Key']} for obj in objects]
            aws.s3_client.delete_objects(
                Bucket=bucket,
                Delete={'Objects': delete_keys}
            )
            delete_count += len(delete_keys)
    
    if delete_count > 0:
        print(f"   ✅ Deleted {delete_count} images")
    else:
        print("   ✅ Folder already empty")
except Exception as e:
    print(f"   ⚠️  Error: {str(e)}")

# 4. Verify cleanup
print("\n4️⃣ Verifying Cleanup...")
collection_info = aws.debug_collection_status(collection)
ddb_items = aws.debug_dynamodb_table(table_name)
s3_keys = aws.debug_s3_keys(bucket, "index")

print("\n" + "="*70)
print("✅ CLEANUP COMPLETE - FRESH START READY")
print("="*70)
print("\n📋 Current Status:")
print(f"   • Rekognition Faces: {collection_info.get('FaceCount', 0)}")
print(f"   • DynamoDB Entries: {len(ddb_items)}")
print(f"   • S3 Images: {len(s3_keys)}")

print("\n💡 Next Steps:")
print("   1. Upload normal person images using /normal/add endpoint")
print("   2. Test search functionality")
print("="*70 + "\n")