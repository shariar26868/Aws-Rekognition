import io
import uuid
from typing import List
import os
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from PIL import Image

from backend.services.aws_service import AWSService
from backend.utils.image_utils import convert_image_to_bytes
from backend.config import NORMAL_BUCKET

router = APIRouter()
aws_service = AWSService()


@router.post("/add")
async def add_normal(
    files: List[UploadFile] = File(...),
    folder: str = Form("index")
):
    """
    Upload multiple normal person images to S3 and DynamoDB.
    """
    try:
        files_data = {
            'bytes': [await file.read() for file in files],
            'filenames': [file.filename for file in files]
        }
        metadata_list = [
            {'FullName': os.path.splitext(file.filename)[0]} for file in files
        ]
        results = aws_service.upload_multiple_to_s3(
            files_data, NORMAL_BUCKET, folder, metadata_list
        )
        return {"status": "added", "results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search")
async def search_normal(file: UploadFile = File(...)):
    """
    Search for normal person lookalikes for the uploaded image.
    Returns all matches with similarity, image_key, best match, and user_image_key.
    """
    try:
        # Read and convert uploaded image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_bytes = convert_image_to_bytes(image)

        # Upload user image temporarily to S3
        user_image_key = f"temp/{uuid.uuid4()}_user.jpg"
        aws_service.upload_to_s3(image_bytes, NORMAL_BUCKET, user_image_key, {'Type': 'user'})

        # Search faces in AWS collection
        matches = aws_service.search_faces("image_collections", image_bytes)
        results = []
        best_match = None
        max_similarity = 0

        for match in matches:
            face_id = match['Face']['FaceId']
            similarity = match['Similarity']
            item = aws_service.get_dynamodb_item("facelookalike", face_id)

            if item and "ImageKey" in item:
                # Include image_key for each match
                result = {
                    "full_name": item['FullName'],
                    "similarity": similarity,
                    "image_key": item['ImageKey']
                }
                results.append(result)

                # Track best match
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = {
                        'full_name': item['FullName'],
                        'image_key': item['ImageKey']
                    }

        # Handle no matches found
        if not results:
            return {
                "message": "Sorry, we couldn't find any lookalike in our system.",
                "matches": [],
                "best_match": None,
                "user_image_key": user_image_key
            }

        # Upload best match image temporarily to S3
        if best_match:
            normal_image_bytes = aws_service.get_s3_image(NORMAL_BUCKET, best_match['image_key'])
            best_match['image_key_stored'] = f"temp/{uuid.uuid4()}_normal.jpg"
            aws_service.upload_to_s3(normal_image_bytes, NORMAL_BUCKET, best_match['image_key_stored'], {'Type': 'normal'})

        return {
            "matches": results,
            "best_match": best_match,
            "user_image_key": user_image_key
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
