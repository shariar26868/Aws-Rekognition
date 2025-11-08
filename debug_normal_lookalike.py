# debug_normal_lookalike.py
# Normal lookalike system debug করুন

from backend.services.aws_service import AWSService

aws = AWSService()

print("\n" + "="*70)
print("🔍 NORMAL LOOKALIKE SYSTEM DEBUGGING")
print("="*70)

# 1. Check Normal Collection Status
print("\n1️⃣ CHECKING NORMAL COLLECTION...")
collection_info = aws.debug_collection_status("image_collections")
if collection_info:
    face_count = collection_info.get('FaceCount', 0)
    if face_count == 0:
        print("   ⚠️  WARNING: Collection exists but has 0 faces indexed!")
        print("   💡 Solution: Upload normal images first using /normal/add endpoint")
    else:
        print(f"   ✅ Collection has {face_count} faces indexed")
else:
    print("   ❌ ERROR: Collection not found")
    print("   💡 Solution: Create collection using AWS CLI:")
    print("      aws rekognition create-collection --collection-id image_collections --region eu-west-1")

# 2. Check DynamoDB Table
print("\n2️⃣ CHECKING NORMAL DYNAMODB TABLE...")
items = aws.debug_dynamodb_table("facelookalike")
if len(items) == 0:
    print("   ⚠️  WARNING: DynamoDB table is empty!")
    print("   💡 Solution: Upload normal images first")
else:
    print(f"   ✅ Found {len(items)} entries in database")
    print("\n   📋 Normal Person Names:")
    valid_count = 0
    invalid_count = 0
    for item in items[:10]:
        full_name = item.get('FullName', 'Unknown')
        image_key = item.get('ImageKey', None)
        if image_key:
            print(f"      ✅ {full_name[:60]} - {image_key}")
            valid_count += 1
        else:
            print(f"      ❌ {full_name[:60]} - NO ImageKey!")
            invalid_count += 1
    
    if invalid_count > 0:
        print(f"\n   ⚠️  Found {invalid_count} entries without ImageKey!")
        print("   💡 Run cleanup script to fix this")

# 3. Check S3 Bucket
print("\n3️⃣ CHECKING NORMAL S3 BUCKET...")
keys = aws.debug_s3_keys("celebrity-lookalike-face-rekognition", "index")
if len(keys) == 0:
    print("   ⚠️  WARNING: No images found in S3 bucket!")
    print("   💡 Solution: Upload normal images using /normal/add endpoint")
else:
    print(f"   ✅ Found {len(keys)} images in S3")

# 4. Cross-check: Are there any faces in collection but not in DynamoDB?
print("\n4️⃣ CROSS-CHECKING COLLECTION ↔ DYNAMODB...")
if collection_info and items:
    collection_face_count = collection_info.get('FaceCount', 0)
    ddb_count = len(items)
    
    if collection_face_count == ddb_count:
        print(f"   ✅ Match! {collection_face_count} faces in both")
    elif collection_face_count > ddb_count:
        print(f"   ⚠️  Mismatch: {collection_face_count} in collection, {ddb_count} in DynamoDB")
        print("   💡 Some faces are indexed but not saved in database")
    else:
        print(f"   ⚠️  Mismatch: {ddb_count} in DynamoDB, {collection_face_count} in collection")

# 5. Test Search with Sample Image (if available)
print("\n5️⃣ TESTING SEARCH FUNCTIONALITY...")
if len(keys) > 0:
    try:
        # Get first normal image from S3
        test_image_key = keys[0]
        print(f"   📸 Testing with: {test_image_key}")
        
        test_image_bytes = aws.get_s3_image("celebrity-lookalike-face-rekognition", test_image_key)
        
        # Search using the same image (should return 100% match)
        print(f"   🔍 Searching in collection: image_collections")
        matches = aws.search_faces("image_collections", test_image_bytes, threshold=1.0)
        
        if matches:
            print(f"   ✅ Search works! Found {len(matches)} match(es)")
            print(f"   📊 Top match similarity: {matches[0]['Similarity']:.2f}%")
            
            # Check if match has DynamoDB entry
            face_id = matches[0]['Face']['FaceId']
            item = aws.get_dynamodb_item("facelookalike", face_id)
            
            if item and "ImageKey" in item:
                print(f"   ✅ DynamoDB entry found with ImageKey")
            elif item:
                print(f"   ⚠️  DynamoDB entry found but NO ImageKey!")
            else:
                print(f"   ❌ No DynamoDB entry for this face!")
        else:
            print("   ❌ Search returned no matches")
            print("   🔍 Possible causes:")
            print("      1. Face not properly indexed in collection")
            print("      2. Collection ID mismatch")
            print("      3. Image quality issue")
    except Exception as e:
        print(f"   ❌ Search test failed: {str(e)}")
else:
    print("   ⏭️  Skipped: No images available for testing")

# 6. Configuration Check
print("\n6️⃣ CONFIGURATION CHECK...")
print("   From your config file:")
print("   • Collection: image_collections")
print("   • Bucket: celebrity-lookalike-face-rekognition")
print("   • DynamoDB: facelookalike")
print("   • Folder: index")

print("\n" + "="*70)
print("✅ DEBUGGING COMPLETE")
print("="*70)
print("\n💡 Summary:")
if collection_info and collection_info.get('FaceCount', 0) > 0:
    print("   ✅ Collection has faces")
else:
    print("   ❌ Collection is empty or doesn't exist")

if len(items) > 0:
    print(f"   ✅ DynamoDB has {len(items)} entries")
else:
    print("   ❌ DynamoDB is empty")

if len(keys) > 0:
    print(f"   ✅ S3 has {len(keys)} images")
else:
    print("   ❌ S3 is empty")

print("\n💡 Next Steps:")
if collection_info and collection_info.get('FaceCount', 0) == 0:
    print("   1. Upload normal images using /normal/add endpoint")
    print("   2. Then try searching again")
elif len(items) == 0:
    print("   1. Check if upload process completed successfully")
    print("   2. Re-upload images if needed")
else:
    print("   1. If everything looks good but search still fails:")
    print("      - Check server console logs during search")
    print("      - Verify the image you're searching with is clear")
    print("      - Try with threshold=50 instead of 68")
print("="*70 + "\n")