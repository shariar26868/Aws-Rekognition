from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
MORPH_API_KEY = os.getenv("MORPH_API_KEY")
NORMAL_BUCKET = os.getenv("NORMAL_BUCKET")
CELEBRITY_BUCKET = os.getenv("CELEBRITY_BUCKET")
NORMAL_COLLECTION = os.getenv("NORMAL_COLLECTION")
CELEBRITY_COLLECTION = os.getenv("CELEBRITY_COLLECTION")
NORMAL_DDB_TABLE = os.getenv("NORMAL_DDB_TABLE")
CELEBRITY_DDB_TABLE = os.getenv("CELEBRITY_DDB_TABLE")