import boto3
from botocore.exceptions import ClientError
from backend.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION,
    NORMAL_BUCKET, CELEBRITY_BUCKET,
    NORMAL_COLLECTION, CELEBRITY_COLLECTION,
    NORMAL_DDB_TABLE, CELEBRITY_DDB_TABLE
)
import uuid

class AWSService:
    def __init__(self):
        boto3.setup_default_session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        self.s3 = boto3.resource("s3")
        self.s3_client = boto3.client("s3")   # ✅ add client for presigned URL
        self.rekognition = boto3.client("rekognition")
        self.dynamodb = boto3.resource("dynamodb")

    def upload_to_s3(self, file_bytes: bytes, bucket: str, key: str, metadata: dict) -> None:
        try:
            self.s3.Bucket(bucket).put_object(Key=key, Body=file_bytes, Metadata=metadata)
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    def index_face(self, bucket: str, key: str, collection_id: str) -> str:
        response = self.rekognition.index_faces(
            CollectionId=collection_id,
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            DetectionAttributes=['ALL']
        )
        face_records = response.get('FaceRecords', [])
        if not face_records:
            raise Exception("No face detected")
        return face_records[0]['Face']['FaceId']

    def save_to_dynamodb(self, table_name: str, face_id: str, full_name: str, image_key: str) -> None:
        table = self.dynamodb.Table(table_name)
        table.put_item(Item={'RekognitionId': face_id, 'FullName': full_name, 'ImageKey': image_key})

    def search_faces(self, collection_id: str, image_bytes: bytes) -> list:
        response = self.rekognition.search_faces_by_image(
            CollectionId=collection_id,
            Image={'Bytes': image_bytes},
            MaxFaces=10,
            FaceMatchThreshold=1
        )
        return response.get('FaceMatches', [])

    def get_dynamodb_item(self, table_name: str, face_id: str) -> dict:
        table = self.dynamodb.Table(table_name)
        response = table.get_item(Key={'RekognitionId': face_id})
        return response.get('Item', {})

    def get_s3_image(self, bucket: str, key: str) -> bytes:
        obj = self.s3.Object(bucket, key)
        return obj.get()['Body'].read()

    def upload_multiple_to_s3(self, files: dict, bucket: str, folder: str, metadata_list: list) -> list:
        results = []
        for file_bytes, metadata, filename in zip(files['bytes'], metadata_list, files['filenames']):
            key = f"{folder}/{uuid.uuid4()}_{filename}"
            self.upload_to_s3(file_bytes, bucket, key, metadata)
            face_id = self.index_face(bucket, key, NORMAL_COLLECTION if bucket == NORMAL_BUCKET else CELEBRITY_COLLECTION)
            table_name = NORMAL_DDB_TABLE if bucket == NORMAL_BUCKET else CELEBRITY_DDB_TABLE
            self.save_to_dynamodb(table_name, face_id, metadata['FullName'], key)
            results.append({"filename": filename, "face_id": face_id, "key": key})
        return results

    # ✅ NEW: generate presigned URL for secure temporary access
    def generate_presigned_url(self, bucket: str, key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL to share an S3 object
        :param bucket: S3 bucket name
        :param key: S3 object key
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")
