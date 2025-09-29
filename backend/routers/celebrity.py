import io
import os
import uuid
from typing import List

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from PIL import Image

from backend.services.aws_service import AWSService
from backend.utils.image_utils import convert_image_to_bytes
from backend.config import CELEBRITY_BUCKET

router = APIRouter()
aws_service = AWSService()


@router.post("/add")
async def add_celebrity(
    files: List[UploadFile] = File(...),
    folder: str = Form("celebritybucket")
):
    """
    Upload multiple celebrity images to S3 and DynamoDB.
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
            files_data, CELEBRITY_BUCKET, folder, metadata_list
        )
        return {"status": "added", "results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search")
async def search_celebrity(file: UploadFile = File(...)):
    """
    Search for celebrity lookalikes for the uploaded image.
    Returns all matches with similarity, image_key, best match, and morph credentials.
    """
    try:
        # Read and convert uploaded image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_bytes = convert_image_to_bytes(image)

        # Search faces in AWS collection
        matches = aws_service.search_faces("celebrity_images_collections", image_bytes)
        results = []
        best_match = None
        max_similarity = 0

        for match in matches:
            face_id = match['Face']['FaceId']
            similarity = match['Similarity']
            item = aws_service.get_dynamodb_item("celebrity-dynamo-table", face_id)

            # Skip if item missing or no ImageKey
            if not item or "ImageKey" not in item:
                continue

            # Add each match with name, similarity, and image_key
            result = {
                "full_name": item.get('FullName', 'Unknown'),
                "similarity": similarity,
                "image_key": item.get("ImageKey")
            }
            results.append(result)

            # Track best match
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = item

        # Handle no matches found
        if not results:
            return {
                "message": "Sorry, we couldn't find any celebrity lookalike in our system.",
                "matches": [],
                "best_match": None,
                "morph_credentials": None
            }

        # Upload user image temporarily to S3
        user_image_key = f"temp/{uuid.uuid4()}_user.jpg"
        aws_service.upload_to_s3(image_bytes, CELEBRITY_BUCKET, user_image_key, {'Type': 'user'})

        morph_credentials = None
        if best_match:
            # Upload best matched celebrity image temporarily to S3
            celebrity_image_bytes = aws_service.get_s3_image(CELEBRITY_BUCKET, best_match['ImageKey'])
            celebrity_image_key = f"temp/{uuid.uuid4()}_celebrity.jpg"
            aws_service.upload_to_s3(celebrity_image_bytes, CELEBRITY_BUCKET, celebrity_image_key, {'Type': 'celebrity'})

            morph_credentials = {
                "user_image_key": user_image_key,
                "celebrity_image_key": celebrity_image_key,
                "celebrity_name": best_match.get('FullName', 'Unknown')
            }

        return {
            "matches": results,
            "best_match": best_match.get('FullName') if best_match else None,
            "morph_credentials": morph_credentials
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
