# create_dynamodb_tables.py
# একবার চালালেই দুটো DynamoDB টেবিল তৈরি হয়ে যাবে

import boto3
from botocore.exceptions import ClientError
from backend.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION,
    NORMAL_DDB_TABLE, CELEBRITY_DDB_TABLE
)

def create_table(table_name):
    client = boto3.client(
        'dynamodb',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    
    print(f"Creating DynamoDB table: {table_name} ...")
    try:
        client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'RekognitionId', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'RekognitionId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'  # ফ্রি টিয়ারে চলবে
        )
        print(f"Creating {table_name}... (waiting 10s)")
        time.sleep(10)
        print(f"SUCCESS: {table_name} created!")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Already exists: {table_name}")
        else:
            print(f"Error: {e}")
            return False
    return True

import time

if __name__ == "__main__":
    print("="*70)
    print("CREATING DYNAMODB TABLES FOR FACELOOKALIKE")
    print("="*70)
    
    create_table(NORMAL_DDB_TABLE)
    create_table(CELEBRITY_DDB_TABLE)
    
    print("\n" + "="*70)
    print("ALL TABLES READY!")
    print("Now you can upload images:")
    print("   python bulk_upload_normal.py")
    print("   curl -X POST http://localhost:8000/normal/add ...")
    print("="*70)