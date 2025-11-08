# create_collections.py
# একবার চালালেই দুটো Rekognition Collection তৈরি হয়ে যাবে

import boto3
from botocore.exceptions import ClientError
from backend.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION,
    NORMAL_COLLECTION, CELEBRITY_COLLECTION
)

def create_collection(collection_id):
    client = boto3.client(
        'rekognition',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    
    print(f"Creating collection: {collection_id} ...")
    try:
        client.create_collection(CollectionId=collection_id)
        print(f"SUCCESS: {collection_id} created!")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            print(f"Already exists: {collection_id}")
        else:
            print(f"Error: {e}")
            return False
    return True

if __name__ == "__main__":
    print("="*60)
    print("CREATING REKOGNITION COLLECTIONS")
    print("="*60)
    
    create_collection(NORMAL_COLLECTION)
    create_collection(CELEBRITY_COLLECTION)
    
    print("\n" + "="*60)
    print("ALL COLLECTIONS READY!")
    print("Now you can upload images:")
    print("   python bulk_upload_normal.py")
    print("   curl -X POST http://localhost:8000/normal/add ...")
    print("="*60)