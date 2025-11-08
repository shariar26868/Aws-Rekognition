# ============ fix_celebrity_imagekey.py ============
# DynamoDB-তে থাকা celebrities এর ImageKey fill করবে

from backend.services.aws_service import AWSService
from backend.config import (
    CELEBRITY_BUCKET, CELEBRITY_COLLECTION, CELEBRITY_DDB_TABLE
)
import os

class CelebrityFixer:
    def __init__(self):
        self.aws_service = AWSService()
    
    def get_s3_celebrities(self) -> dict:
        """S3-তে থাকা celebrities পাবে - full_name -> key mapping"""
        try:
            celebrities = {}
            paginator = self.aws_service.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=CELEBRITY_BUCKET, Prefix="celebritybucket/")
            
            for page in pages:
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if key != "celebritybucket/" and not key.endswith('/'):
                        # Extract full_name from key
                        filename = os.path.basename(key)
                        full_name = os.path.splitext(filename)[0]
                        celebrities[full_name] = key
            
            return celebrities
        except Exception as e:
            print(f"❌ Error listing S3: {str(e)}")
            return {}
    
    def fix_dynamodb_imagekeys(self):
        """DynamoDB-তে থাকা celebrities এর ImageKey fill করবে"""
        print("\n" + "="*60)
        print("🔧 FIX CELEBRITY IMAGEKEY")
        print("="*60)
        
        # Get S3 celebrities
        s3_celebrities = self.get_s3_celebrities()
        print(f"\n📊 Found {len(s3_celebrities)} celebrities in S3")
        
        # Get DynamoDB items
        table = self.aws_service.dynamodb.Table(CELEBRITY_DDB_TABLE)
        response = table.scan()
        ddb_items = response.get('Items', [])
        
        print(f"   Found {len(ddb_items)} items in DynamoDB")
        
        # Count items with missing ImageKey
        missing_count = 0
        for item in ddb_items:
            if not item.get('ImageKey'):
                missing_count += 1
        
        print(f"   Items with missing ImageKey: {missing_count}")
        
        if missing_count == 0:
            print("\n✅ All items already have ImageKey!")
            return
        
        # Show sample items
        print(f"\n   Sample items to fix:")
        for item in ddb_items[:3]:
            full_name = item.get('FullName', 'Unknown')
            image_key = item.get('ImageKey')
            print(f"   - {full_name}: {image_key}")
        
        # Confirm
        response = input(f"\n🚀 Fix {missing_count} items with missing ImageKey? (yes/no): ").lower()
        if response != 'yes':
            print("Cancelled.")
            return
        
        print(f"\n🔄 Fixing items...\n")
        
        fixed_count = 0
        not_found_count = 0
        
        for item in ddb_items:
            full_name = item.get('FullName')
            face_id = item.get('RekognitionId')
            existing_key = item.get('ImageKey')
            
            # Skip if already has ImageKey
            if existing_key:
                continue
            
            # Try to find in S3
            if full_name in s3_celebrities:
                key = s3_celebrities[full_name]
                print(f"✓ Found: {full_name}")
                print(f"  Key: {key}")
                
                # Update DynamoDB
                try:
                    table.update_item(
                        Key={'RekognitionId': face_id},
                        UpdateExpression='SET ImageKey = :key',
                        ExpressionAttributeValues={':key': key}
                    )
                    print(f"  ✓ Updated in DynamoDB")
                    fixed_count += 1
                except Exception as e:
                    print(f"  ❌ Error updating: {str(e)}")
            else:
                # Try fuzzy matching - look for partial match
                partial_matches = [name for name in s3_celebrities.keys() 
                                 if name.lower() in full_name.lower() 
                                 or full_name.lower() in name.lower()]
                
                if partial_matches:
                    key = s3_celebrities[partial_matches[0]]
                    print(f"⚠️  Partial match: {full_name} -> {partial_matches[0]}")
                    print(f"  Key: {key}")
                    
                    try:
                        table.update_item(
                            Key={'RekognitionId': face_id},
                            UpdateExpression='SET ImageKey = :key',
                            ExpressionAttributeValues={':key': key}
                        )
                        print(f"  ✓ Updated in DynamoDB")
                        fixed_count += 1
                    except Exception as e:
                        print(f"  ❌ Error updating: {str(e)}")
                else:
                    print(f"❌ Not found in S3: {full_name}")
                    not_found_count += 1
        
        print(f"\n" + "="*60)
        print(f"✅ Fix Complete!")
        print(f"   - Fixed: {fixed_count}")
        print(f"   - Not found: {not_found_count}")
        print(f"="*60)

def main():
    fixer = CelebrityFixer()
    fixer.fix_dynamodb_imagekeys()

if __name__ == "__main__":
    main()