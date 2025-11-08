# ============ cleanup_orphaned.py ============
# এটা একটা separate file হিসেবে run করুন
# Command: python cleanup_orphaned.py

from backend.services.aws_service import AWSService
from backend.config import (
    NORMAL_BUCKET, CELEBRITY_BUCKET,
    NORMAL_COLLECTION, CELEBRITY_COLLECTION,
    NORMAL_DDB_TABLE, CELEBRITY_DDB_TABLE,
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
)
import boto3
from botocore.exceptions import ClientError

class CleanupService:
    def __init__(self):
        self.aws_service = AWSService()
        boto3.setup_default_session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        self.dynamodb = boto3.resource("dynamodb")
        self.rekognition = boto3.client("rekognition")
    
    def get_all_s3_keys(self, bucket: str, folder: str = "") -> set:
        """S3-তে সব keys এর একটা set return করে"""
        keys = set()
        try:
            paginator = self.aws_service.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket, Prefix=folder)
            
            for page in pages:
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if key != folder and key != f"{folder}/":  # folder name itself exclude করো
                        keys.add(key)
            return keys
        except ClientError as e:
            print(f"✗ Error getting S3 keys: {str(e)}")
            return keys
    
    def get_all_dynamodb_items(self, table_name: str) -> list:
        """DynamoDB-তে সব items return করে"""
        table = self.dynamodb.Table(table_name)
        items = []
        try:
            response = table.scan()
            items.extend(response.get('Items', []))
            
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response.get('Items', []))
            
            return items
        except ClientError as e:
            print(f"✗ Error scanning DynamoDB: {str(e)}")
            return items
    
    def remove_face_from_collection(self, collection_id: str, face_id: str) -> bool:
        """Rekognition collection থেকে face remove করে"""
        try:
            self.rekognition.delete_faces(
                CollectionId=collection_id,
                FaceIds=[face_id]
            )
            print(f"   ✓ Removed face {face_id} from collection")
            return True
        except ClientError as e:
            print(f"   ✗ Error removing face: {str(e)}")
            return False
    
    def cleanup_normal_bucket(self):
        """NORMAL bucket থেকে orphaned records clean করে"""
        print("\n" + "="*60)
        print("CLEANING NORMAL BUCKET")
        print("="*60)
        
        # S3 keys এবং DynamoDB items পাও
        s3_keys = self.get_all_s3_keys(NORMAL_BUCKET, "index")
        ddb_items = self.get_all_dynamodb_items(NORMAL_DDB_TABLE)
        
        print(f"\n📊 Status:")
        print(f"   - S3 keys found: {len(s3_keys)}")
        print(f"   - DynamoDB items: {len(ddb_items)}")
        
        # যেসব DynamoDB items এর S3 file নেই, সেগুলো remove করো
        orphaned = []
        for item in ddb_items:
            image_key = item.get('ImageKey')
            if image_key and image_key not in s3_keys:
                orphaned.append(item)
        
        print(f"   - Orphaned records found: {len(orphaned)}")
        
        if orphaned:
            print(f"\n🧹 Removing {len(orphaned)} orphaned records...")
            
            table = self.dynamodb.Table(NORMAL_DDB_TABLE)
            removed_count = 0
            
            for item in orphaned:
                try:
                    face_id = item['RekognitionId']
                    full_name = item.get('FullName', 'Unknown')
                    
                    # Rekognition collection থেকে remove করো
                    self.remove_face_from_collection(NORMAL_COLLECTION, face_id)
                    
                    # DynamoDB থেকে remove করো
                    table.delete_item(Key={'RekognitionId': face_id})
                    print(f"   ✓ Deleted: {full_name} ({face_id})")
                    removed_count += 1
                    
                except Exception as e:
                    print(f"   ✗ Error deleting {item.get('FullName', 'Unknown')}: {str(e)}")
            
            print(f"\n✅ Cleanup complete! Removed {removed_count} records.")
        else:
            print("\n✅ No orphaned records found!")
    
    def cleanup_celebrity_bucket(self):
        """CELEBRITY bucket থেকে orphaned records clean করে"""
        print("\n" + "="*60)
        print("CLEANING CELEBRITY BUCKET")
        print("="*60)
        
        # S3 keys এবং DynamoDB items পাও
        s3_keys = self.get_all_s3_keys(CELEBRITY_BUCKET, "celebritybucket")
        ddb_items = self.get_all_dynamodb_items(CELEBRITY_DDB_TABLE)
        
        print(f"\n📊 Status:")
        print(f"   - S3 keys found: {len(s3_keys)}")
        print(f"   - DynamoDB items: {len(ddb_items)}")
        
        # যেসব DynamoDB items এর S3 file নেই, সেগুলো remove করো
        orphaned = []
        for item in ddb_items:
            image_key = item.get('ImageKey')
            if image_key and image_key not in s3_keys:
                orphaned.append(item)
        
        print(f"   - Orphaned records found: {len(orphaned)}")
        
        if orphaned:
            print(f"\n🧹 Removing {len(orphaned)} orphaned records...")
            
            table = self.dynamodb.Table(CELEBRITY_DDB_TABLE)
            removed_count = 0
            
            for item in orphaned:
                try:
                    face_id = item['RekognitionId']
                    full_name = item.get('FullName', 'Unknown')
                    
                    # Rekognition collection থেকে remove করো
                    self.remove_face_from_collection(CELEBRITY_COLLECTION, face_id)
                    
                    # DynamoDB থেকে remove করো
                    table.delete_item(Key={'RekognitionId': face_id})
                    print(f"   ✓ Deleted: {full_name} ({face_id})")
                    removed_count += 1
                    
                except Exception as e:
                    print(f"   ✗ Error deleting {item.get('FullName', 'Unknown')}: {str(e)}")
            
            print(f"\n✅ Cleanup complete! Removed {removed_count} records.")
        else:
            print("\n✅ No orphaned records found!")

def main():
    print("🔧 AWS Cleanup Tool")
    print("This will remove orphaned DynamoDB records and Rekognition faces.\n")
    
    cleanup = CleanupService()
    
    # Ask for confirmation
    response = input("Do you want to proceed? (yes/no): ").lower()
    if response != 'yes':
        print("Cancelled.")
        return
    
    cleanup.cleanup_normal_bucket()
    cleanup.cleanup_celebrity_bucket()
    
    print("\n" + "="*60)
    print("All cleanup operations completed!")
    print("="*60)

if __name__ == "__main__":
    main()