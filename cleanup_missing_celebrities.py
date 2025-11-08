# ============ cleanup_missing_celebrities.py ============
# DynamoDB-তে যেসব celebrities S3-তে নেই, সেগুলো delete করবে

from backend.services.aws_service import AWSService
from backend.config import CELEBRITY_BUCKET, CELEBRITY_COLLECTION, CELEBRITY_DDB_TABLE
import os

class MissingCelebrityCleaner:
    def __init__(self):
        self.aws_service = AWSService()
    
    def get_s3_celebrities(self) -> set:
        """S3-তে থাকা সব celebrities এর full_name return করবে"""
        try:
            celebrities = set()
            paginator = self.aws_service.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=CELEBRITY_BUCKET, Prefix="celebritybucket/")
            
            for page in pages:
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if key != "celebritybucket/" and not key.endswith('/'):
                        filename = os.path.basename(key)
                        full_name = os.path.splitext(filename)[0]
                        celebrities.add(full_name)
            
            return celebrities
        except Exception as e:
            print(f"❌ Error listing S3: {str(e)}")
            return set()
    
    def cleanup_missing(self):
        """Missing celebrities delete করবে"""
        print("\n" + "="*60)
        print("🧹 CLEANUP MISSING CELEBRITIES")
        print("="*60)
        
        # Get S3 celebrities
        s3_celebrities = self.get_s3_celebrities()
        print(f"\n📊 S3 celebrities: {len(s3_celebrities)}")
        
        # Get DynamoDB items
        table = self.aws_service.dynamodb.Table(CELEBRITY_DDB_TABLE)
        response = table.scan()
        ddb_items = response.get('Items', [])
        
        print(f"   DynamoDB items: {len(ddb_items)}")
        
        # Find missing items
        missing_items = []
        for item in ddb_items:
            full_name = item.get('FullName')
            if full_name not in s3_celebrities:
                missing_items.append(item)
        
        print(f"   Missing in S3: {len(missing_items)}")
        
        if not missing_items:
            print("\n✅ No missing celebrities found!")
            return
        
        # Show missing items
        print(f"\n   Items to delete:")
        for item in missing_items:
            full_name = item.get('FullName', 'Unknown')
            face_id = item.get('RekognitionId')
            print(f"   - {full_name} ({face_id})")
        
        # Confirm
        response = input(f"\n🚀 Delete these {len(missing_items)} items? (yes/no): ").lower()
        if response != 'yes':
            print("Cancelled.")
            return
        
        print(f"\n🔄 Deleting items...\n")
        
        deleted_count = 0
        error_count = 0
        
        for item in missing_items:
            full_name = item.get('FullName', 'Unknown')
            face_id = item.get('RekognitionId')
            
            try:
                # Delete from Rekognition collection
                self.aws_service.rekognition.delete_faces(
                    CollectionId=CELEBRITY_COLLECTION,
                    FaceIds=[face_id]
                )
                print(f"✓ Removed from Rekognition: {full_name}")
                
                # Delete from DynamoDB
                table.delete_item(Key={'RekognitionId': face_id})
                print(f"  ✓ Deleted from DynamoDB")
                deleted_count += 1
                
            except Exception as e:
                print(f"❌ Error deleting {full_name}: {str(e)}")
                error_count += 1
        
        print(f"\n" + "="*60)
        print(f"✅ Cleanup Complete!")
        print(f"   - Deleted: {deleted_count}")
        print(f"   - Errors: {error_count}")
        print(f"="*60)

def main():
    cleaner = MissingCelebrityCleaner()
    cleaner.cleanup_missing()

if __name__ == "__main__":
    main()