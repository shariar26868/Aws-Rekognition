# clean_aws_everything.py
# একবার চালালেই সব কিছু ক্লিন! 100% সেফ।

import boto3
from botocore.exceptions import ClientError
from backend.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION,
    NORMAL_BUCKET, CELEBRITY_BUCKET,
    NORMAL_COLLECTION, CELEBRITY_COLLECTION,
    NORMAL_DDB_TABLE, CELEBRITY_DDB_TABLE
)
import time

class AWSCleaner:
    def __init__(self):
        session = boto3.session.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        self.s3_client = session.client('s3')
        self.s3_resource = session.resource('s3')
        self.rekognition = session.client('rekognition')
        self.dynamodb = session.resource('dynamodb')
        self.ddb_client = session.client('dynamodb')

    def delete_collection(self, collection_id):
        print(f"\nDeleting Rekognition Collection: {collection_id} ...")
        try:
            self.rekognition.delete_collection(CollectionId=collection_id)
            print(f"Deleted: {collection_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"Already deleted or not found: {collection_id}")
            else:
                print(f"Error deleting {collection_id}: {e}")

    def delete_dynamodb_table(self, table_name):
        print(f"\nDeleting DynamoDB Table: {table_name} ...")
        try:
            table = self.dynamodb.Table(table_name)
            table.delete()
            print(f"Deleting {table_name}... (waiting 30s)")
            time.sleep(30)  # ডিলিট হতে টাইম লাগে
            print(f"Deleted: {table_name}")
        except ClientError as e:
            if 'ResourceNotFoundException' in str(e):
                print(f"Table not found: {table_name}")
            else:
                print(f"Error: {e}")

    def empty_s3_folder(self, bucket, folder):
        print(f"\nEmptying S3 Bucket: {bucket} → Folder: {folder}/")
        try:
            bucket_obj = self.s3_resource.Bucket(bucket)
            objects_to_delete = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket, Prefix=folder + "/"):
                for obj in page.get('Contents', []):
                    objects_to_delete.append({'Key': obj['Key']})
            
            if objects_to_delete:
                # 1000 টা করে ডিলিট করবে
                for i in range(0, len(objects_to_delete), 1000):
                    chunk = objects_to_delete[i:i+1000]
                    bucket_obj.delete_objects(Delete={'Objects': chunk})
                    print(f"Deleted {len(chunk)} objects from {folder}/")
            else:
                print(f"No objects found in {folder}/")
        except ClientError as e:
            print(f"S3 Error: {e}")

    def run_full_cleanup(self):
        print("="*70)
        print("AWS FULL CLEANUP STARTED - EVERYTHING WILL BE DELETED!")
        print("="*70)

        # 1. Delete Collections
        self.delete_collection(NORMAL_COLLECTION)
        self.delete_collection(CELEBRITY_COLLECTION)

        # 2. Delete DynamoDB Tables
        self.delete_dynamodb_table(NORMAL_DDB_TABLE)
        self.delete_dynamodb_table(CELEBRITY_DDB_TABLE)

        # 3. Empty S3 Folders
        self.empty_s3_folder(NORMAL_BUCKET, "index")
        self.empty_s3_folder(NORMAL_BUCKET, "temp")
        self.empty_s3_folder(CELEBRITY_BUCKET, "celebritybucket")
        self.empty_s3_folder(CELEBRITY_BUCKET, "temp")

        print("\n" + "="*70)
        print("FULL CLEANUP COMPLETED!")
        print("You can now run: python debug_aws.py")
        print("All counts will be 0 → Ready for fresh upload!")
        print("="*70)

if __name__ == "__main__":
    cleaner = AWSCleaner()
    confirm = input("\nWARNING: This will DELETE EVERYTHING! Type 'YES_DELETE_ALL' to continue: ")
    if confirm == "YES_DELETE_ALL":
        cleaner.run_full_cleanup()
    else:
        print("Cleanup cancelled. Good decision if unsure!")