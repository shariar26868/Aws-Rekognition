# ============ reindex_celebrities.py ============
# S3-তে থাকা celebrities গুলো Rekognition-এ re-index করবে

from backend.services.aws_service import AWSService
from backend.config import (
    CELEBRITY_BUCKET, CELEBRITY_COLLECTION, CELEBRITY_DDB_TABLE
)
import os

class CelebrityReindexer:
    def __init__(self):
        self.aws_service = AWSService()
    
    def get_s3_celebrities(self) -> list:
        """S3-তে থাকা সব celebrity images পাবে"""
        try:
            paginator = self.aws_service.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=CELEBRITY_BUCKET, Prefix="celebritybucket/")
            
            celebrities = []
            for page in pages:
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    # Skip folder itself
                    if key != "celebritybucket/" and not key.endswith('/'):
                        celebrities.append(key)
            
            return celebrities
        except Exception as e:
            print(f"❌ Error listing S3: {str(e)}")
            return []
    
    def reindex_celebrities(self):
        """সব celebrities re-index করবে"""
        print("\n" + "="*60)
        print("🎬 CELEBRITY RE-INDEXER")
        print("="*60)
        
        # Get S3 celebrities
        celebrities = self.get_s3_celebrities()
        print(f"\n📊 Found {len(celebrities)} celebrities in S3:")
        for celeb in celebrities:
            print(f"   - {celeb}")
        
        if not celebrities:
            print("\n❌ No celebrities found in S3!")
            return
        
        # Confirm
        response = input(f"\n🚀 Re-index these {len(celebrities)} celebrities? (yes/no): ").lower()
        if response != 'yes':
            print("Cancelled.")
            return
        
        print(f"\n🔄 Starting re-indexing...\n")
        
        # Check DynamoDB table first
        table = self.aws_service.dynamodb.Table(CELEBRITY_DDB_TABLE)
        
        success_count = 0
        error_count = 0
        
        for i, key in enumerate(celebrities, 1):
            filename = os.path.basename(key)
            full_name = os.path.splitext(filename)[0]
            
            print(f"[{i}/{len(celebrities)}] Processing: {filename}")
            
            try:
                # Index face in Rekognition
                face_id = self.aws_service.index_face(
                    CELEBRITY_BUCKET, 
                    key, 
                    CELEBRITY_COLLECTION
                )
                
                # Save to DynamoDB
                self.aws_service.save_to_dynamodb(
                    CELEBRITY_DDB_TABLE,
                    face_id,
                    full_name,
                    key
                )
                
                print(f"   ✓ Indexed successfully")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                error_count += 1
        
        print(f"\n" + "="*60)
        print(f"✅ Re-indexing Complete!")
        print(f"   - Success: {success_count}")
        print(f"   - Failed: {error_count}")
        print(f"="*60)

def main():
    reindexer = CelebrityReindexer()
    reindexer.reindex_celebrities()

if __name__ == "__main__":
    main()