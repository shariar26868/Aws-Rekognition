# ============ debug_celebrity_detailed.py ============

from backend.services.aws_service import AWSService
from backend.config import (
    CELEBRITY_BUCKET, CELEBRITY_COLLECTION, CELEBRITY_DDB_TABLE
)
import boto3

def debug_celebrity():
    aws_service = AWSService()
    
    print("="*60)
    print("DETAILED CELEBRITY DEBUG")
    print("="*60)
    
    # 1. Check collection status
    print("\n1️⃣  COLLECTION STATUS")
    try:
        response = aws_service.rekognition.describe_collection(
            CollectionId=CELEBRITY_COLLECTION
        )
        print(f"   Collection: {CELEBRITY_COLLECTION}")
        print(f"   Faces indexed: {response.get('FaceCount', 0)}")
        print(f"   Created: {response.get('CreationTimestamp', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # 2. Check S3 files
    print("\n2️⃣  S3 FILES")
    try:
        s3_keys = []
        paginator = aws_service.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=CELEBRITY_BUCKET, Prefix="celebritybucket/")
        
        for page in pages:
            for obj in page.get('Contents', []):
                key = obj['Key']
                if key != "celebritybucket/" and not key.endswith('/'):
                    s3_keys.append(key)
        
        print(f"   Total files: {len(s3_keys)}")
        for key in s3_keys[:5]:
            print(f"   - {key}")
        if len(s3_keys) > 5:
            print(f"   ... and {len(s3_keys) - 5} more")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # 3. Check DynamoDB items
    print("\n3️⃣  DYNAMODB ITEMS")
    try:
        table = aws_service.dynamodb.Table(CELEBRITY_DDB_TABLE)
        response = table.scan()
        items = response.get('Items', [])
        
        print(f"   Total items: {len(items)}")
        if items:
            print(f"   Sample items:")
            for item in items[:3]:
                print(f"   - {item.get('FullName')} | Key: {item.get('ImageKey')}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # 4. Try a test search
    print("\n4️⃣  TEST SEARCH")
    try:
        # Get first S3 image
        if s3_keys:
            test_key = s3_keys[0]
            print(f"   Testing with: {test_key}")
            
            # Download the image
            image_bytes = aws_service.get_s3_image(CELEBRITY_BUCKET, test_key)
            print(f"   Image downloaded: {len(image_bytes)} bytes")
            
            # Try to search
            matches = aws_service.search_faces(CELEBRITY_COLLECTION, image_bytes)
            print(f"   Search results: {len(matches)} matches found")
            
            if matches:
                for match in matches[:3]:
                    face_id = match['Face']['FaceId']
                    similarity = match['Similarity']
                    print(f"   - FaceID: {face_id}, Similarity: {similarity}%")
            else:
                print(f"   ⚠️  No matches found! This might indicate:")
                print(f"      - Collection is empty")
                print(f"      - Images weren't indexed properly")
                print(f"      - Search threshold is too high")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    debug_celebrity()