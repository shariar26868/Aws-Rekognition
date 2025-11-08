# celebrity_debug.py
# এই script টি চালিয়ে দেখুন আপনার AWS setup সঠিক আছে কিনা

from backend.services.aws_service import AWSService

aws = AWSService()

print("\n" + "="*70)
print("🔍 CELEBRITY SYSTEM DEBUGGING")
print("="*70)

# 1. Check Celebrity Collection Status
print("\n1️⃣ CHECKING CELEBRITY COLLECTION...")
collection_info = aws.debug_collection_status("celebrity_image_collections")
if collection_info:
    face_count = collection_info.get('FaceCount', 0)
    if face_count == 0:
        print("   ⚠️  WARNING: Collection exists but has 0 faces indexed!")
        print("   💡 Solution: Upload celebrity images first using /celebrity/add endpoint")
else:
    print("   ❌ ERROR: Collection not found or error occurred")
    print("   💡 Solution: Create collection using AWS CLI:")
    print("      aws rekognition create-collection --collection-id celebrity_image_collections --region eu-west-1")

# 2. Check DynamoDB Table
print("\n2️⃣ CHECKING CELEBRITY DYNAMODB TABLE...")
items = aws.debug_dynamodb_table("celebrity-dynamo-table")
if len(items) == 0:
    print("   ⚠️  WARNING: DynamoDB table is empty!")
    print("   💡 Solution: Upload celebrity images first")
else:
    print(f"   ✅ Found {len(items)} celebrities in database")
    print("\n   📋 Celebrity Names:")
    for item in items[:10]:
        print(f"      • {item.get('FullName', 'Unknown')} - {item.get('ImageKey', 'N/A')}")

# 3. Check S3 Bucket
print("\n3️⃣ CHECKING CELEBRITY S3 BUCKET...")
keys = aws.debug_s3_keys("celebrity-lookalike-celebrity-lookalike", "celebritybucket")
if len(keys) == 0:
    print("   ⚠️  WARNING: No images found in S3 bucket!")
    print("   💡 Solution: Upload celebrity images using /celebrity/add endpoint")
else:
    print(f"   ✅ Found {len(keys)} images in S3")

# 4. Test Search with Sample Image (if available)
print("\n4️⃣ TESTING SEARCH FUNCTIONALITY...")
if len(keys) > 0:
    try:
        # Get first celebrity image from S3
        test_image_key = keys[0]
        print(f"   📸 Testing with: {test_image_key}")
        
        test_image_bytes = aws.get_s3_image("celebrity-lookalike-celebrity-lookalike", test_image_key)
        
        # Search using the same image (should return 100% match)
        matches = aws.search_faces("celebrity_image_collections", test_image_bytes, threshold=1.0)
        
        if matches:
            print(f"   ✅ Search works! Found {len(matches)} match(es)")
            print(f"   📊 Top match similarity: {matches[0]['Similarity']:.2f}%")
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

# 5. Cross-check Configuration
print("\n5️⃣ CONFIGURATION CHECK...")
print("   From your config file:")
print("   • Collection: celebrity_image_collections")
print("   • Bucket: celebrity-lookalike-celebrity-lookalike")
print("   • DynamoDB: celebrity-dynamo-table")
print("   • Folder: celebritybucket")

print("\n" + "="*70)
print("✅ DEBUGGING COMPLETE")
print("="*70)
print("\n💡 Next Steps:")
print("   1. If collections/tables don't exist, create them")
print("   2. Upload at least one celebrity image using /celebrity/add")
print("   3. Then try searching again")
print("="*70 + "\n")