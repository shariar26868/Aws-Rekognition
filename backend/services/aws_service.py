# import boto3
# from botocore.exceptions import ClientError
# from backend.config import (
#     AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION,
#     NORMAL_BUCKET, CELEBRITY_BUCKET,
#     NORMAL_COLLECTION, CELEBRITY_COLLECTION,
#     NORMAL_DDB_TABLE, CELEBRITY_DDB_TABLE
# )
# import uuid
# import time

# class AWSService:
#     def __init__(self):
#         boto3.setup_default_session(
#             aws_access_key_id=AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
#             region_name=AWS_REGION
#         )
#         self.s3 = boto3.resource("s3")
#         self.s3_client = boto3.client("s3")
#         self.rekognition = boto3.client("rekognition")
#         self.dynamodb = boto3.resource("dynamodb")

#     def upload_to_s3(self, file_bytes: bytes, bucket: str, key: str, metadata: dict) -> None:
#         try:
#             self.s3.Bucket(bucket).put_object(
#                 Key=key,
#                 Body=file_bytes,
#                 Metadata=metadata,
#                 ContentType='image/jpeg'  # Explicitly set ContentType to JPEG
#             )
#             print(f"✓ S3 Upload successful: s3://{bucket}/{key}")
#         except ClientError as e:
#             raise Exception(f"S3 upload failed: {str(e)}")

#     def upload_video_to_s3(self, file_bytes: bytes, bucket: str, key: str) -> None:
#         """Upload video file to S3 with proper content type"""
#         try:
#             self.s3.Bucket(bucket).put_object(
#                 Key=key,
#                 Body=file_bytes,
#                 ContentType='video/mp4',  # ✅ Correct content type for MP4
#                 ContentDisposition='inline'  # ✅ Allow viewing in browser
#             )
#             print(f"✓ S3 Video Upload successful: s3://{bucket}/{key}")
#         except ClientError as e:
#             raise Exception(f"S3 video upload failed: {str(e)}")

#     def index_face(self, bucket: str, key: str, collection_id: str, retries=3, delay=1) -> str:
#         for attempt in range(retries):
#             try:
#                 response = self.rekognition.index_faces(
#                     CollectionId=collection_id,
#                     Image={'S3Object': {'Bucket': bucket, 'Name': key}},
#                     DetectionAttributes=['ALL']
#                 )
#                 face_records = response.get('FaceRecords', [])
#                 if not face_records:
#                     raise Exception("No face detected")
#                 face_id = face_records[0]['Face']['FaceId']
#                 print(f"✓ Face indexed: {face_id} in collection {collection_id}")
                
#                 return face_id
#             except ClientError as e:
#                 if attempt == retries - 1:
#                     raise Exception(f"IndexFaces failed: {str(e)}")
#                 time.sleep(delay)

#     def save_to_dynamodb(self, table_name: str, face_id: str, full_name: str, image_key: str) -> None:
#         try:
#             table = self.dynamodb.Table(table_name)
#             table.put_item(Item={
#                 'RekognitionId': face_id, 
#                 'FullName': full_name, 
#                 'ImageKey': image_key
#             })
#             print(f"✓ Saved to DynamoDB: {table_name} | FaceID: {face_id} | ImageKey: {image_key}")
#         except ClientError as e:
#             raise Exception(f"DynamoDB save failed: {str(e)}")

#     def search_faces(self, collection_id: str, image_bytes: bytes, retries=3, delay=1) -> list:
#         for attempt in range(retries):
#             try:
#                 response = self.rekognition.search_faces_by_image(
#                     CollectionId=collection_id,
#                     Image={'Bytes': image_bytes},
#                     MaxFaces=10,
#                     FaceMatchThreshold=1
#                 )
#                 matches = response.get('FaceMatches', [])
#                 print(f"✓ Search completed: Found {len(matches)} faces in collection {collection_id}")
#                 return matches
#             except ClientError as e:
#                 if attempt == retries - 1:
#                     raise Exception(f"SearchFaces failed: {str(e)}")
#                 time.sleep(delay)

#     def get_dynamodb_item(self, table_name: str, face_id: str) -> dict:
#         try:
#             table = self.dynamodb.Table(table_name)
#             response = table.get_item(Key={'RekognitionId': face_id})
#             item = response.get('Item', {})
#             if item:
#                 print(f"✓ DynamoDB retrieved: {item}")
#             else:
#                 print(f"⚠ DynamoDB item not found for FaceID: {face_id}")
#             return item
#         except ClientError as e:
#             raise Exception(f"DynamoDB get failed: {str(e)}")

#     def get_s3_image(self, bucket: str, key: str) -> bytes:
#         try:
#             print(f"→ Attempting to retrieve: s3://{bucket}/{key}")
#             obj = self.s3.Object(bucket, key)
#             data = obj.get()['Body'].read()
#             print(f"✓ S3 image retrieved successfully")
#             return data
#         except ClientError as e:
#             print(f"✗ S3 retrieval failed: {str(e)}")
#             raise Exception(f"Failed to retrieve S3 image: {str(e)}")

#     # def upload_multiple_to_s3(self, files: dict, bucket: str, folder: str, metadata_list: list) -> list:
#     #     results = []
#     #     for file_bytes, metadata, filename in zip(files['bytes'], metadata_list, files['filenames']):
#     #         try:
#     #             key = f"{folder}/{uuid.uuid4()}_{filename}"
#     #             print(f"\n→ Processing: {filename}")
                
#     #             self.upload_to_s3(file_bytes, bucket, key, metadata)
                
#     #             collection_id = NORMAL_COLLECTION if bucket == NORMAL_BUCKET else CELEBRITY_COLLECTION
#     #             face_id = self.index_face(bucket, key, collection_id)
                
#     #             table_name = NORMAL_DDB_TABLE if bucket == NORMAL_BUCKET else CELEBRITY_DDB_TABLE
#     #             self.save_to_dynamodb(table_name, face_id, metadata['FullName'], key)
                
#     #             results.append({"filename": filename, "face_id": face_id, "key": key})
#     #         except Exception as e:
#     #             print(f"✗ Error processing {filename}: {str(e)}")
#     #             # Don't stop on error, continue with next file
#     #             continue
        
#     #     return results
#     def upload_multiple_to_s3(self, files: dict, bucket: str, folder: str, metadata_list: list) -> list:
#         results = []
#         for file_bytes, metadata, filename in zip(files['bytes'], metadata_list, files['filenames']):
#             try:
#                 key = f"{folder}/{uuid.uuid4()}_{filename}"
#                 print(f"\n→ Processing: {filename}")
                
#                 self.upload_to_s3(file_bytes, bucket, key, metadata)
                
#                 collection_id = NORMAL_COLLECTION if bucket == NORMAL_BUCKET else CELEBRITY_COLLECTION
#                 face_id = self.index_face(bucket, key, collection_id)
                
#                 table_name = NORMAL_DDB_TABLE if bucket == NORMAL_BUCKET else CELEBRITY_DDB_TABLE
#                 self.save_to_dynamodb(table_name, face_id, metadata['FullName'], key)
                
#                 results.append({"filename": filename, "face_id": face_id, "key": key})
#             except Exception as e:
#                 print(f"✗ Error processing {filename}: {str(e)}")
#                 # Don't stop on error, continue with next file
#                 continue
        
#         # ✅ এই section যোগ করুন (return এর আগে)
#         print("\n" + "="*70)
#         print("📦 UPLOAD_MULTIPLE_TO_S3 - FINAL RESULTS:")
#         print("="*70)
#         print(f"Total files processed: {len(results)}")
#         if results:
#             import json
#             print(json.dumps(results, indent=2, default=str))
#         else:
#             print("⚠️  No results to return (all files may have failed)")
#         print("="*70 + "\n")
        
#         return results

#     def generate_presigned_url(self, bucket: str, key: str, expiration: int = 3600) -> str:
#         try:
#             url = self.s3_client.generate_presigned_url(
#                 'get_object',
#                 Params={'Bucket': bucket, 'Key': key},
#                 ExpiresIn=expiration
#             )
#             return url
#         except ClientError as e:
#             raise Exception(f"Error generating presigned URL: {str(e)}")

#     # ===================== DEBUGGING FUNCTIONS =====================
#     def debug_collection_status(self, collection_id: str) -> dict:
#         """Check how many faces are indexed in a collection"""
#         try:
#             response = self.rekognition.describe_collection(CollectionId=collection_id)
#             print(f"\n📊 Collection Status: {collection_id}")
#             print(f"   - Indexed Faces: {response.get('FaceCount', 0)}")
#             print(f"   - Created: {response.get('CreationTimestamp', 'N/A')}")
#             return response
#         except ClientError as e:
#             print(f"✗ Error checking collection: {str(e)}")
#             return {}

#     def debug_dynamodb_table(self, table_name: str) -> dict:
#         """Check all items in DynamoDB table"""
#         try:
#             table = self.dynamodb.Table(table_name)
#             response = table.scan()
#             items = response.get('Items', [])
#             print(f"\n📊 DynamoDB Table: {table_name}")
#             print(f"   - Total Items: {len(items)}")
#             if items:
#                 print(f"   - Sample item: {items[0]}")
#             return items
#         except ClientError as e:
#             print(f"✗ Error scanning DynamoDB: {str(e)}")
#             return []

#     def debug_s3_keys(self, bucket: str, folder: str = "") -> list:
#         """List all S3 keys in bucket/folder"""
#         try:
#             print(f"\n📊 S3 Bucket: {bucket}")
#             if folder:
#                 print(f"   - Folder: {folder}/")
            
#             paginator = self.s3_client.get_paginator('list_objects_v2')
#             pages = paginator.paginate(Bucket=bucket, Prefix=folder)
            
#             keys = []
#             for page in pages:
#                 for obj in page.get('Contents', []):
#                     keys.append(obj['Key'])
            
#             print(f"   - Total keys: {len(keys)}")
#             if keys:
#                 print(f"   - Sample keys:")
#                 for key in keys[:5]:
#                     print(f"      • {key}")
#             return keys
#         except ClientError as e:
#             print(f"✗ Error listing S3: {str(e)}")
#             return []




################################################################7/11############
# backend/services/aws_service.py
# backend/services/aws_service.py
# import boto3
# from botocore.exceptions import ClientError
# from backend.config import (
#     AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION,
#     NORMAL_BUCKET, CELEBRITY_BUCKET,
#     NORMAL_COLLECTION, CELEBRITY_COLLECTION,
#     NORMAL_DDB_TABLE, CELEBRITY_DDB_TABLE
# )
# import uuid
# import time
# import json

# class AWSService:
#     def __init__(self):
#         boto3.setup_default_session(
#             aws_access_key_id=AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
#             region_name=AWS_REGION
#         )
#         self.s3 = boto3.resource("s3")
#         self.s3_client = boto3.client("s3")
#         self.rekognition = boto3.client("rekognition")
#         self.dynamodb = boto3.resource("dynamodb")

#     def upload_to_s3(self, file_bytes: bytes, bucket: str, key: str, metadata: dict) -> None:
#         try:
#             self.s3.Bucket(bucket).put_object(
#                 Key=key,
#                 Body=file_bytes,
#                 Metadata=metadata,
#                 ContentType='image/jpeg'
#             )
#             print(f"Uploaded: s3://{bucket}/{key}")
#         except ClientError as e:
#             raise Exception(f"S3 upload failed: {str(e)}")

#     def upload_video_to_s3(self, file_bytes: bytes, bucket: str, key: str) -> None:
#         try:
#             self.s3.Bucket(bucket).put_object(
#                 Key=key,
#                 Body=file_bytes,
#                 ContentType='video/mp4',
#                 ContentDisposition='inline'
#             )
#             print(f"Video uploaded: s3://{bucket}/{key}")
#         except ClientError as e:
#             raise Exception(f"S3 video upload failed: {str(e)}")

#     def index_face(self, bucket: str, key: str, collection_id: str, retries=3, delay=2) -> str:
#         for attempt in range(retries):
#             try:
#                 response = self.rekognition.index_faces(
#                     CollectionId=collection_id,
#                     Image={'S3Object': {'Bucket': bucket, 'Name': key}},
#                     DetectionAttributes=['ALL'],
#                     MaxFaces=1,
#                     QualityFilter='AUTO'
#                 )
#                 face_records = response.get('FaceRecords', [])
#                 if not face_records:
#                     raise Exception("No face detected")
#                 face_id = face_records[0]['Face']['FaceId']
#                 print(f"Indexed: {face_id}")
#                 return face_id
#             except ClientError as e:
#                 if attempt == retries - 1:
#                     raise Exception(f"Index failed: {str(e)}")
#                 time.sleep(delay)

#     def save_to_dynamodb(self, table_name: str, face_id: str, full_name: str, image_key: str) -> None:
#         try:
#             table = self.dynamodb.Table(table_name)
#             table.put_item(Item={
#                 'RekognitionId': face_id,
#                 'FullName': full_name,
#                 'ImageKey': image_key
#             })
#             print(f"DynamoDB saved: {full_name}")
#         except ClientError as e:
#             raise Exception(f"DynamoDB save failed: {str(e)}")

#     def search_faces(self, collection_id: str, image_bytes: bytes, threshold: float = 1.0, max_faces: int = 10) -> list:
#         try:
#             response = self.rekognition.search_faces_by_image(
#                 CollectionId=collection_id,
#                 Image={'Bytes': image_bytes},
#                 MaxFaces=max_faces,
#                 FaceMatchThreshold=threshold
#             )
#             matches = response.get('FaceMatches', [])
#             print(f"Found {len(matches)} matches ≥ {threshold}%")
#             return matches
#         except ClientError as e:
#             if 'ResourceNotFoundException' in str(e):
#                 print(f"Collection {collection_id} not found!")
#                 return []
#             print(f"Search error: {str(e)}")
#             return []

#     def get_dynamodb_item(self, table_name: str, face_id: str) -> dict:
#         try:
#             table = self.dynamodb.Table(table_name)
#             response = table.get_item(Key={'RekognitionId': face_id})
#             return response.get('Item', {})
#         except ClientError as e:
#             print(f"DynamoDB get failed: {str(e)}")
#             return {}

#     def get_s3_image(self, bucket: str, key: str) -> bytes:
#         try:
#             obj = self.s3.Object(bucket, key)
#             return obj.get()['Body'].read()
#         except ClientError as e:
#             raise Exception(f"S3 get failed: {str(e)}")

#     def upload_multiple_to_s3(self, files: dict, bucket: str, folder: str, metadata_list: list) -> list:
#         results = []
#         for file_bytes, metadata, filename in zip(files['bytes'], metadata_list, files['filenames']):
#             try:
#                 key = f"{folder}/{uuid.uuid4()}_{filename}"
#                 self.upload_to_s3(file_bytes, bucket, key, metadata)
#                 collection_id = NORMAL_COLLECTION if bucket == NORMAL_BUCKET else CELEBRITY_COLLECTION
#                 face_id = self.index_face(bucket, key, collection_id)
#                 table_name = NORMAL_DDB_TABLE if bucket == NORMAL_BUCKET else CELEBRITY_DDB_TABLE
#                 self.save_to_dynamodb(table_name, face_id, metadata['FullName'], key)
#                 results.append({"filename": filename, "key": key, "face_id": face_id, "status": "success"})
#             except Exception as e:
#                 results.append({"filename": filename, "error": str(e), "status": "failed"})
#         print("UPLOAD RESULTS:", json.dumps(results, indent=2))
#         return results

#     def generate_presigned_url(self, bucket: str, key: str, expiration: int = 3600) -> str:
#         try:
#             return self.s3_client.generate_presigned_url(
#                 'get_object',
#                 Params={'Bucket': bucket, 'Key': key},
#                 ExpiresIn=expiration
#             )
#         except ClientError as e:
#             raise Exception(f"Presigned URL error: {str(e)}")

#     # ===================== DEBUGGING FUNCTIONS =====================
#     def debug_collection_status(self, collection_id: str) -> dict:
#         try:
#             response = self.rekognition.describe_collection(CollectionId=collection_id)
#             print(f"\nCollection: {collection_id}")
#             print(f"   Status: {response.get('Status', 'Unknown')}")
#             print(f"   Face Count: {response.get('FaceCount', 0)}")
#             print(f"   Created: {response.get('CreationTimestamp', 'N/A')}")
#             return response
#         except ClientError as e:
#             print(f"Collection {collection_id} NOT FOUND or ERROR: {str(e)}")
#             return {}

#     def debug_dynamodb_table(self, table_name: str) -> list:
#         try:
#             table = self.dynamodb.Table(table_name)
#             response = table.scan()
#             items = response.get('Items', [])
#             print(f"\nDynamoDB Table: {table_name}")
#             print(f"   Total Items: {len(items)}")
#             if items:
#                 print(f"   Sample: {items[0]}")
#             return items
#         except ClientError as e:
#             print(f"DynamoDB Table {table_name} ERROR: {str(e)}")
#             return []

#     def debug_s3_keys(self, bucket: str, folder: str = "") -> list:
#         try:
#             print(f"\nS3 Bucket: {bucket} | Folder: {folder or 'root'}")
#             paginator = self.s3_client.get_paginator('list_objects_v2')
#             pages = paginator.paginate(Bucket=bucket, Prefix=folder + "/" if folder else "")
#             keys = []
#             for page in pages:
#                 for obj in page.get('Contents', []):
#                     keys.append(obj['Key'])
#             print(f"   Total Objects: {len(keys)}")
#             for key in keys[:10]:
#                 print(f"   • {key}")
#             if len(keys) > 10:
#                 print(f"   ... and {len(keys) - 10} more")
#             return keys
#         except ClientError as e:
#             print(f"S3 List failed for {bucket}: {str(e)}")
#             return []



#8/11/2025

# backend/services/aws_service.py
# backend/services/aws_service.py

import boto3
from botocore.exceptions import ClientError
from backend.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION,
    NORMAL_BUCKET, CELEBRITY_BUCKET,
    NORMAL_COLLECTION, CELEBRITY_COLLECTION,
    NORMAL_DDB_TABLE, CELEBRITY_DDB_TABLE
)
import uuid
import time
import json

class AWSService:
    def __init__(self):
        boto3.setup_default_session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        self.s3 = boto3.resource("s3")
        self.s3_client = boto3.client("s3")
        self.rekognition = boto3.client("rekognition")
        self.dynamodb = boto3.resource("dynamodb")

    def upload_to_s3(self, file_bytes: bytes, bucket: str, key: str, metadata: dict) -> None:
        try:
            self.s3.Bucket(bucket).put_object(
                Key=key,
                Body=file_bytes,
                Metadata=metadata,
                ContentType='image/jpeg'
            )
            print(f"✅ Uploaded: s3://{bucket}/{key}")
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    # 🔧 নতুন function: S3 এ file আছে কিনা verify করুন
    def verify_s3_object_exists(self, bucket: str, key: str, max_retries: int = 10, delay: float = 1.0) -> bool:
        """
        S3 এ object upload complete হয়েছে কিনা verify করে
        Eventual consistency এর জন্য retry করে
        """
        print(f"🔍 Verifying S3 object: s3://{bucket}/{key}")
        
        for attempt in range(max_retries):
            try:
                # HeadObject API call করে file existence check করা হয়
                self.s3_client.head_object(Bucket=bucket, Key=key)
                print(f"✅ S3 object verified (attempt {attempt + 1}/{max_retries})")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    if attempt < max_retries - 1:
                        print(f"⏳ Object not found yet, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"❌ Object not found after {max_retries} attempts")
                        return False
                else:
                    # অন্য error হলে
                    print(f"❌ S3 verification error: {str(e)}")
                    return False
        
        return False

    # 🔧 Updated: Better retry logic with S3 verification
    def index_face(self, bucket: str, key: str, collection_id: str, retries: int = 5, delay: float = 2.0) -> str:
        """
        S3 থেকে face index করে Rekognition collection এ
        Improved retry mechanism with exponential backoff
        """
        print(f"\n🎯 Indexing face: s3://{bucket}/{key}")
        print(f"   Collection: {collection_id}")
        
        for attempt in range(retries):
            try:
                response = self.rekognition.index_faces(
                    CollectionId=collection_id,
                    Image={'S3Object': {'Bucket': bucket, 'Name': key}},
                    DetectionAttributes=['ALL'],
                    MaxFaces=1,
                    QualityFilter='AUTO'
                )
                
                face_records = response.get('FaceRecords', [])
                
                if not face_records:
                    raise Exception("No face detected in image")
                
                face_id = face_records[0]['Face']['FaceId']
                print(f"✅ Face indexed successfully: {face_id}")
                return face_id
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = str(e)
                
                # S3 object not found - সবচেয়ে common error
                if 'InvalidS3ObjectException' in error_msg or 'NoSuchKey' in error_msg:
                    if attempt < retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        print(f"⚠️  S3 object not ready, waiting {wait_time}s... (attempt {attempt + 1}/{retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"S3 object not found after {retries} attempts: {key}")
                
                # Invalid image parameter
                elif 'InvalidImageFormatException' in error_msg:
                    raise Exception(f"Invalid image format: {error_msg}")
                
                # No face detected
                elif 'InvalidParameterException' in error_msg:
                    raise Exception(f"Face detection failed: {error_msg}")
                
                # Collection not found
                elif 'ResourceNotFoundException' in error_msg:
                    raise Exception(f"Collection '{collection_id}' not found!")
                
                # অন্যান্য errors
                else:
                    if attempt < retries - 1:
                        wait_time = delay * (2 ** attempt)
                        print(f"⚠️  Rekognition error, retrying in {wait_time}s... (attempt {attempt + 1}/{retries})")
                        print(f"   Error: {error_msg}")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Rekognition index failed: {error_msg}")
        
        raise Exception(f"Failed to index face after {retries} attempts")

    def save_to_dynamodb(self, table_name: str, face_id: str, full_name: str, image_key: str) -> None:
        try:
            table = self.dynamodb.Table(table_name)
            table.put_item(Item={
                'RekognitionId': face_id,
                'FullName': full_name,
                'ImageKey': image_key
            })
            print(f"✅ DynamoDB saved: {full_name} → {face_id}")
        except ClientError as e:
            raise Exception(f"DynamoDB save failed: {str(e)}")

    def search_faces(self, collection_id: str, image_bytes: bytes, threshold: float = 1.0, max_faces: int = 10) -> list:
        try:
            response = self.rekognition.search_faces_by_image(
                CollectionId=collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=max_faces,
                FaceMatchThreshold=threshold
            )
            matches = response.get('FaceMatches', [])
            print(f"Found {len(matches)} matches ≥ {threshold}%")
            return matches
        except ClientError as e:
            if 'ResourceNotFoundException' in str(e):
                print(f"❌ Collection {collection_id} not found!")
                return []
            print(f"❌ Search error: {str(e)}")
            return []

    def get_dynamodb_item(self, table_name: str, face_id: str) -> dict:
        try:
            table = self.dynamodb.Table(table_name)
            response = table.get_item(Key={'RekognitionId': face_id})
            return response.get('Item', {})
        except ClientError as e:
            print(f"❌ DynamoDB get failed: {str(e)}")
            return {}

    def get_s3_image(self, bucket: str, key: str) -> bytes:
        try:
            obj = self.s3.Object(bucket, key)
            return obj.get()['Body'].read()
        except ClientError as e:
            raise Exception(f"S3 get failed: {str(e)}")

    # 🔧 UPDATED: Better error handling and S3 verification
    def upload_multiple_to_s3(self, files: dict, bucket: str, folder: str, metadata_list: list) -> list:
        """
        Multiple files upload করে S3 এ, index করে Rekognition এ, এবং save করে DynamoDB তে
        Improved error handling and verification
        """
        results = []
        collection_id = NORMAL_COLLECTION if bucket == NORMAL_BUCKET else CELEBRITY_COLLECTION
        table_name = NORMAL_DDB_TABLE if bucket == NORMAL_BUCKET else CELEBRITY_DDB_TABLE
        
        print(f"\n{'='*60}")
        print(f"📦 BATCH UPLOAD STARTED")
        print(f"{'='*60}")
        print(f"   Bucket: {bucket}")
        print(f"   Folder: {folder}")
        print(f"   Collection: {collection_id}")
        print(f"   DynamoDB Table: {table_name}")
        print(f"   Total Files: {len(files['bytes'])}")
        print(f"{'='*60}\n")
        
        for idx, (file_bytes, metadata, filename) in enumerate(zip(files['bytes'], metadata_list, files['filenames']), 1):
            print(f"\n📁 Processing file {idx}/{len(files['bytes'])}: {filename}")
            print(f"{'─'*60}")
            
            try:
                # Step 1: Generate unique key
                key = f"{folder}/{uuid.uuid4()}_{filename}"
                
                # Step 2: Upload to S3
                print(f"⬆️  Uploading to S3...")
                self.upload_to_s3(file_bytes, bucket, key, metadata)
                
                # Step 3: Verify S3 upload (CRITICAL!)
                print(f"🔍 Verifying S3 upload...")
                if not self.verify_s3_object_exists(bucket, key, max_retries=10, delay=1.0):
                    raise Exception("S3 upload verification failed - object not found")
                
                # Step 4: Wait a bit for S3 consistency (extra safety)
                print(f"⏳ Waiting 2s for S3 consistency...")
                time.sleep(2)
                
                # Step 5: Index face in Rekognition
                print(f"🎯 Indexing face in Rekognition...")
                face_id = self.index_face(bucket, key, collection_id, retries=5, delay=2.0)
                
                # Step 6: Save to DynamoDB
                print(f"💾 Saving to DynamoDB...")
                self.save_to_dynamodb(table_name, face_id, metadata['FullName'], key)
                
                # Success!
                result = {
                    "filename": filename,
                    "key": key,
                    "face_id": face_id,
                    "status": "success",
                    "message": "Successfully uploaded and indexed"
                }
                results.append(result)
                print(f"✅ SUCCESS: {filename}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ FAILED: {filename}")
                print(f"   Error: {error_msg}")
                
                # Cleanup: যদি S3 এ upload হয়ে থাকে কিন্তু index fail হয়
                try:
                    if 'key' in locals():
                        print(f"🧹 Attempting cleanup of S3 object: {key}")
                        self.s3_client.delete_object(Bucket=bucket, Key=key)
                        print(f"✅ Cleaned up S3 object")
                except Exception as cleanup_error:
                    print(f"⚠️  Cleanup failed: {cleanup_error}")
                
                result = {
                    "filename": filename,
                    "error": error_msg,
                    "status": "failed",
                    "message": f"Upload or indexing failed: {error_msg}"
                }
                results.append(result)
        
        # Final summary
        success_count = sum(1 for r in results if r['status'] == 'success')
        fail_count = sum(1 for r in results if r['status'] == 'failed')
        
        print(f"\n{'='*60}")
        print(f"📊 BATCH UPLOAD COMPLETED")
        print(f"{'='*60}")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {fail_count}")
        print(f"   📋 Total: {len(results)}")
        print(f"{'='*60}\n")
        
        return results

    def upload_video_to_s3(self, file_bytes: bytes, bucket: str, key: str) -> None:
        try:
            self.s3.Bucket(bucket).put_object(
                Key=key,
                Body=file_bytes,
                ContentType='video/mp4',
                ContentDisposition='inline'
            )
            print(f"✅ Video uploaded: s3://{bucket}/{key}")
        except ClientError as e:
            raise Exception(f"S3 video upload failed: {str(e)}")

    def generate_presigned_url(self, bucket: str, key: str, expiration: int = 3600) -> str:
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
        except ClientError as e:
            raise Exception(f"Presigned URL error: {str(e)}")

    # ===================== DEBUGGING FUNCTIONS =====================
    def debug_collection_status(self, collection_id: str) -> dict:
        try:
            response = self.rekognition.describe_collection(CollectionId=collection_id)
            print(f"\n📊 Collection: {collection_id}")
            print(f"   Status: {response.get('Status', 'Unknown')}")
            print(f"   Face Count: {response.get('FaceCount', 0)}")
            print(f"   Created: {response.get('CreationTimestamp', 'N/A')}")
            return response
        except ClientError as e:
            print(f"❌ Collection {collection_id} NOT FOUND or ERROR: {str(e)}")
            return {}

    def debug_dynamodb_table(self, table_name: str) -> list:
        try:
            table = self.dynamodb.Table(table_name)
            response = table.scan()
            items = response.get('Items', [])
            print(f"\n📋 DynamoDB Table: {table_name}")
            print(f"   Total Items: {len(items)}")
            if items:
                print(f"   Sample: {items[0]}")
            return items
        except ClientError as e:
            print(f"❌ DynamoDB Table {table_name} ERROR: {str(e)}")
            return []

    def debug_s3_keys(self, bucket: str, folder: str = "") -> list:
        try:
            print(f"\n📦 S3 Bucket: {bucket} | Folder: {folder or 'root'}")
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket, Prefix=folder + "/" if folder else "")
            keys = []
            for page in pages:
                for obj in page.get('Contents', []):
                    keys.append(obj['Key'])
            print(f"   Total Objects: {len(keys)}")
            for key in keys[:10]:
                print(f"   • {key}")
            if len(keys) > 10:
                print(f"   ... and {len(keys) - 10} more")
            return keys
        except ClientError as e:
            print(f"❌ S3 List failed for {bucket}: {str(e)}")
            return []