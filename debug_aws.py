# ============ debug_aws.py ============
# এটা একটা separate file হিসেবে run করুন
# Command: python debug_aws.py

from backend.services.aws_service import AWSService
from backend.config import (
    NORMAL_BUCKET, CELEBRITY_BUCKET,
    NORMAL_COLLECTION, CELEBRITY_COLLECTION,
    NORMAL_DDB_TABLE, CELEBRITY_DDB_TABLE
)

def main():
    service = AWSService()
    
    print("=" * 60)
    print("AWS DEBUGGING SCRIPT")
    print("=" * 60)
    
    # Check Normal collection
    print("\n### NORMAL BUCKET ###")
    service.debug_collection_status(NORMAL_COLLECTION)
    service.debug_dynamodb_table(NORMAL_DDB_TABLE)
    service.debug_s3_keys(NORMAL_BUCKET, "index")
    
    # Check Celebrity collection
    print("\n\n### CELEBRITY BUCKET ###")
    service.debug_collection_status(CELEBRITY_COLLECTION)
    service.debug_dynamodb_table(CELEBRITY_DDB_TABLE)
    service.debug_s3_keys(CELEBRITY_BUCKET, "celebritybucket")
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()