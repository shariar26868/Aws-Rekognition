# import io
# import os
# import uuid
# from typing import List
# from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
# from PIL import Image, UnidentifiedImageError

# from backend.services.aws_service import AWSService
# from backend.utils.image_utils import convert_image_to_bytes, validate_face_visibility, preprocess_image_bytes
# from backend.config import CELEBRITY_BUCKET

# router = APIRouter()
# aws_service = AWSService()

# # Allowed image extensions
# ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"}

# def allowed_file(filename: str) -> bool:
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def get_suggestion_message() -> str:
#     return (
#         "Please upload a valid image with one of the following formats: JPG, JPEG, PNG, or WEBP. "
#         "Ensure the image is clear, not corrupted, and smaller than 5MB."
#     )

# @router.post("/add", status_code=status.HTTP_200_OK)
# async def add_celebrity(
#     files: List[UploadFile] = File(...),
#     folder: str = Form("celebritybucket")
# ):
#     """
#     Upload multiple celebrity images to S3 and DynamoDB with face validation.
#     Returns 200 OK on success or if validation fails with a suggestion message.
#     """
#     try:
#         files_data = {
#             'bytes': [],
#             'filenames': []
#         }
#         errors = []

#         for file in files:
#             filename = file.filename
#             # Check file extension
#             if not allowed_file(filename):
#                 errors.append({"filename": filename, "message": f"Invalid extension. {get_suggestion_message()}"})
#                 continue

#             contents = await file.read()
#             if not contents:
#                 errors.append({"filename": filename, "message": f"File is empty. {get_suggestion_message()}"})
#                 continue

#             # Check file size before processing
#             if len(contents) > 5 * 1024 * 1024:
#                 errors.append({"filename": filename, "message": f"Exceeds 5MB limit. {get_suggestion_message()}"})
#                 continue

#             # Basic image validation
#             try:
#                 image = Image.open(io.BytesIO(contents))
#                 image.load()
#             except UnidentifiedImageError:
#                 errors.append({"filename": filename, "message": f"Not a valid image. {get_suggestion_message()}"})
#                 continue

#             # Preprocess to JPEG for AWS Rekognition
#             try:
#                 processed_bytes = preprocess_image_bytes(contents)
#             except ValueError as ve:
#                 errors.append({"filename": filename, "message": str(ve)})
#                 continue

#             # Face validation
#             is_valid, validation_message = validate_face_visibility(processed_bytes)
#             if not is_valid:
#                 errors.append({"filename": filename, "message": validation_message})
#                 continue

#             files_data['bytes'].append(processed_bytes)
#             files_data['filenames'].append(filename)

#         # If we have valid files, upload them
#         results = []
#         if files_data['bytes']:
#             metadata_list = [
#                 {'FullName': os.path.splitext(filename)[0]} for filename in files_data['filenames']
#             ]
            
#             results = aws_service.upload_multiple_to_s3(
#                 files_data, CELEBRITY_BUCKET, folder, metadata_list
#             )

#             # Validate AWS response
#             if not results:
#                 return {
#                     "status": "error",
#                     "message": "Failed to upload images to S3.",
#                     "results": [],
#                     "errors": [{"filename": "upload", "message": "AWS upload failed"} ] + errors
#                 }

#         num_success = len(results)
#         num_errors = len(errors)
#         if num_success > 0:
#             status = "success"
#             message = f"{num_success} image(s) successfully uploaded and indexed."
#             if num_errors > 0:
#                 message += f" {num_errors} image(s) failed."
#         else:
#             status = "error"
#             message = f"All {num_errors} image(s) failed to upload."
        
#         return {
#             "status": status,
#             "message": message,
#             "results": results,
#             "errors": errors
#         }

#     except Exception as e:
#         return {
#             "status": "error",
#             "message": f"Error processing images: {str(e)}",
#             "results": [],
#             "errors": [{"filename": "general", "message": str(e)}]
#         }

# @router.post("/search", status_code=status.HTTP_200_OK)
# async def search_celebrity(file: UploadFile = File(...)):
#     """
#     Search for celebrity lookalikes for the uploaded image.
#     Returns 200 OK with results or error message if validation fails.
#     """
#     try:
#         if not allowed_file(file.filename):
#             return {
#                 "status": "error",
#                 "message": f"File {file.filename} has an invalid extension. {get_suggestion_message()}",
#                 "matches": [],
#                 "best_match": None,
#                 "morph_credentials": None
#             }

#         contents = await file.read()
#         if not contents:
#             return {
#                 "status": "error",
#                 "message": f"File {file.filename} is empty. {get_suggestion_message()}",
#                 "matches": [],
#                 "best_match": None,
#                 "morph_credentials": None
#             }

#         # Check file size
#         if len(contents) > 5 * 1024 * 1024:
#             return {
#                 "status": "error",
#                 "message": f"File exceeds 5MB limit. {get_suggestion_message()}",
#                 "matches": [],
#                 "best_match": None,
#                 "morph_credentials": None
#             }

#         # Basic image validation
#         try:
#             image = Image.open(io.BytesIO(contents))
#             image.load()
#         except UnidentifiedImageError:
#             return {
#                 "status": "error",
#                 "message": f"The uploaded file is not a valid image. {get_suggestion_message()}",
#                 "matches": [],
#                 "best_match": None,
#                 "morph_credentials": None
#             }

#         # Preprocess to JPEG
#         try:
#             processed_bytes = preprocess_image_bytes(contents)
#         except ValueError as ve:
#             return {
#                 "status": "error",
#                 "message": str(ve),
#                 "matches": [],
#                 "best_match": None,
#                 "morph_credentials": None
#             }

#         # Face validation
#         is_valid, validation_message = validate_face_visibility(processed_bytes)
#         if not is_valid:
#             return {
#                 "status": "error",
#                 "message": validation_message,
#                 "matches": [],
#                 "best_match": None,
#                 "morph_credentials": None
#             }

#         # Search faces in AWS collection
#         matches = aws_service.search_faces("celebrity_images_collections", processed_bytes)
#         results = []
#         best_match = None
#         max_similarity = 0

#         for match in matches:
#             face_id = match['Face']['FaceId']
#             similarity = match['Similarity']
#             item = aws_service.get_dynamodb_item("celebrity-dynamo-table", face_id)

#             if not item or "ImageKey" not in item:
#                 continue

#             result = {
#                 "full_name": item.get('FullName', 'Unknown'),
#                 "similarity": similarity,
#                 "image_key": item.get("ImageKey")
#             }
#             results.append(result)

#             if similarity > max_similarity:
#                 max_similarity = similarity
#                 best_match = item

#         if not results:
#             return {
#                 "status": "success",
#                 "message": "Sorry, we couldn't find any celebrity lookalike in our system.",
#                 "matches": [],
#                 "best_match": None,
#                 "morph_credentials": None
#             }

#         # Upload user image temporarily to S3
#         user_image_key = f"temp/{uuid.uuid4()}_user.jpg"
#         aws_service.upload_to_s3(processed_bytes, CELEBRITY_BUCKET, user_image_key, {'Type': 'user'})

#         morph_credentials = None
#         if best_match:
#             try:
#                 celebrity_image_bytes = aws_service.get_s3_image(CELEBRITY_BUCKET, best_match['ImageKey'])
#                 celebrity_image_key = f"temp/{uuid.uuid4()}_celebrity.jpg"
#                 aws_service.upload_to_s3(celebrity_image_bytes, CELEBRITY_BUCKET, celebrity_image_key, {'Type': 'celebrity'})

#                 morph_credentials = {
#                     "user_image_key": user_image_key,
#                     "celebrity_image_key": celebrity_image_key,
#                     "celebrity_name": best_match.get('FullName', 'Unknown')
#                 }
#             except Exception as img_error:
#                 print(f"Warning: Could not retrieve celebrity image for morphing: {str(img_error)}")
#                 best_match_name = best_match.get('FullName', 'Unknown') if best_match else None
#                 return {
#                     "status": "success",
#                     "message": "Search completed successfully. (Note: Best match image could not be retrieved for morphing)",
#                     "matches": results,
#                     "best_match": best_match_name,
#                     "morph_credentials": None
#                 }

#         best_match_name = best_match.get('FullName') if best_match else None

#         return {
#             "status": "success",
#             "message": "Search completed successfully.",
#             "matches": results,
#             "best_match": best_match_name,
#             "morph_credentials": morph_credentials
#         }

#     except Exception as e:
#         return {
#             "status": "error",
#             "message": f"Error searching for lookalikes: {str(e)}",
#             "matches": [],
#             "best_match": None,
#             "morph_credentials": None
#         }


# # #############################8/11


import io
import os
import uuid
from typing import List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from PIL import Image, UnidentifiedImageError

from backend.services.aws_service import AWSService
from backend.utils.image_utils import convert_image_to_bytes, validate_face_visibility, preprocess_image_bytes
from backend.config import CELEBRITY_BUCKET, CELEBRITY_COLLECTION, CELEBRITY_DDB_TABLE

router = APIRouter()
aws_service = AWSService()

# Allowed image extensions
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_suggestion_message() -> str:
    return (
        "Please upload a valid image with one of the following formats: JPG, JPEG, PNG, or WEBP. "
        "Ensure the image is clear, not corrupted, and smaller than 5MB."
    )

@router.post("/add", status_code=status.HTTP_200_OK)
async def add_celebrity(
    files: List[UploadFile] = File(...),
    folder: str = Form("celebritybucket")
):
    """
    Upload multiple celebrity images to S3 and DynamoDB with face validation.
    Returns 200 OK on success or if validation fails with a suggestion message.
    """
    try:
        files_data = {
            'bytes': [],
            'filenames': []
        }
        errors = []

        for file in files:
            filename = file.filename
            # Check file extension
            if not allowed_file(filename):
                errors.append({"filename": filename, "message": f"Invalid extension. {get_suggestion_message()}"})
                continue

            contents = await file.read()
            if not contents:
                errors.append({"filename": filename, "message": f"File is empty. {get_suggestion_message()}"})
                continue

            # Check file size before processing
            if len(contents) > 5 * 1024 * 1024:
                errors.append({"filename": filename, "message": f"Exceeds 5MB limit. {get_suggestion_message()}"})
                continue

            # Basic image validation
            try:
                image = Image.open(io.BytesIO(contents))
                image.load()
            except UnidentifiedImageError:
                errors.append({"filename": filename, "message": f"Not a valid image. {get_suggestion_message()}"})
                continue

            # Preprocess to JPEG for AWS Rekognition
            try:
                processed_bytes = preprocess_image_bytes(contents)
            except ValueError as ve:
                errors.append({"filename": filename, "message": str(ve)})
                continue

            # Face validation
            is_valid, validation_message = validate_face_visibility(processed_bytes)
            if not is_valid:
                errors.append({"filename": filename, "message": validation_message})
                continue

            files_data['bytes'].append(processed_bytes)
            files_data['filenames'].append(filename)

        # If we have valid files, upload them
        results = []
        if files_data['bytes']:
            metadata_list = [
                {'FullName': os.path.splitext(filename)[0]} for filename in files_data['filenames']
            ]
            
            results = aws_service.upload_multiple_to_s3(
                files_data, CELEBRITY_BUCKET, folder, metadata_list
            )

            # Validate AWS response
            if not results:
                return {
                    "status": "error",
                    "message": "Failed to upload images to S3.",
                    "results": [],
                    "errors": [{"filename": "upload", "message": "AWS upload failed"} ] + errors
                }

        num_success = len(results)
        num_errors = len(errors)
        if num_success > 0:
            status = "success"
            message = f"{num_success} image(s) successfully uploaded and indexed."
            if num_errors > 0:
                message += f" {num_errors} image(s) failed."
        else:
            status = "error"
            message = f"All {num_errors} image(s) failed to upload."
        
        return {
            "status": status,
            "message": message,
            "results": results,
            "errors": errors
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing images: {str(e)}",
            "results": [],
            "errors": [{"filename": "general", "message": str(e)}]
        }

@router.post("/search", status_code=status.HTTP_200_OK)
async def search_celebrity(file: UploadFile = File(...)):
    """
    Search for celebrity lookalikes for the uploaded image.
    Returns 200 OK with results or error message if validation fails.
    """
    try:
        if not allowed_file(file.filename):
            return {
                "status": "error",
                "message": f"File {file.filename} has an invalid extension. {get_suggestion_message()}",
                "matches": [],
                "best_match": None,
                "morph_credentials": None
            }

        contents = await file.read()
        if not contents:
            return {
                "status": "error",
                "message": f"File {file.filename} is empty. {get_suggestion_message()}",
                "matches": [],
                "best_match": None,
                "morph_credentials": None
            }

        # Check file size
        if len(contents) > 5 * 1024 * 1024:
            return {
                "status": "error",
                "message": f"File exceeds 5MB limit. {get_suggestion_message()}",
                "matches": [],
                "best_match": None,
                "morph_credentials": None
            }

        # Basic image validation
        try:
            image = Image.open(io.BytesIO(contents))
            image.load()
        except UnidentifiedImageError:
            return {
                "status": "error",
                "message": f"The uploaded file is not a valid image. {get_suggestion_message()}",
                "matches": [],
                "best_match": None,
                "morph_credentials": None
            }

        # Preprocess to JPEG
        try:
            processed_bytes = preprocess_image_bytes(contents)
        except ValueError as ve:
            return {
                "status": "error",
                "message": str(ve),
                "matches": [],
                "best_match": None,
                "morph_credentials": None
            }

        # Face validation
        is_valid, validation_message = validate_face_visibility(processed_bytes)
        if not is_valid:
            return {
                "status": "error",
                "message": validation_message,
                "matches": [],
                "best_match": None,
                "morph_credentials": None
            }

        # ✅ FIX: Use config constants
        print(f"\n🔍 Searching in collection: {CELEBRITY_COLLECTION}")
        matches = aws_service.search_faces(CELEBRITY_COLLECTION, processed_bytes,threshold=1.0)
        print(f"📊 Raw matches found: {len(matches)}")
        
        results = []
        best_match = None
        max_similarity = 0

        for match in matches:
            face_id = match['Face']['FaceId']
            similarity = match['Similarity']
            
            print(f"\n🆔 Processing Face ID: {face_id}")
            print(f"   Similarity: {similarity}%")
            
            # ✅ FIX: Use config constant
            item = aws_service.get_dynamodb_item(CELEBRITY_DDB_TABLE, face_id)
            
            # ✅ FIX: Better debugging
            print(f"   DynamoDB Item: {item}")
            
            if not item:
                print(f"   ⚠️  No DynamoDB item found for FaceID: {face_id}")
                continue
                
            if "ImageKey" not in item:
                print(f"   ⚠️  ImageKey missing for: {item.get('FullName', 'Unknown')}")
                continue

            result = {
                "full_name": item.get('FullName', 'Unknown'),
                "similarity": similarity,
                "image_key": item.get("ImageKey")
            }
            results.append(result)
            print(f"   ✅ Added to results: {result['full_name']}")

            if similarity > max_similarity:
                max_similarity = similarity
                best_match = item

        print(f"\n📋 Total results: {len(results)}")

        if not results:
            return {
                "status": "success",
                "message": "Sorry, we couldn't find any celebrity lookalike in our system.",
                "matches": [],
                "best_match": None,
                "morph_credentials": None
            }

        # Upload user image temporarily to S3
        user_image_key = f"temp/{uuid.uuid4()}_user.jpg"
        aws_service.upload_to_s3(processed_bytes, CELEBRITY_BUCKET, user_image_key, {'Type': 'user'})

        morph_credentials = None
        if best_match:
            try:
                celebrity_image_bytes = aws_service.get_s3_image(CELEBRITY_BUCKET, best_match['ImageKey'])
                celebrity_image_key = f"temp/{uuid.uuid4()}_celebrity.jpg"
                aws_service.upload_to_s3(celebrity_image_bytes, CELEBRITY_BUCKET, celebrity_image_key, {'Type': 'celebrity'})

                morph_credentials = {
                    "user_image_key": user_image_key,
                    "celebrity_image_key": celebrity_image_key,
                    "celebrity_name": best_match.get('FullName', 'Unknown')
                }
            except Exception as img_error:
                print(f"Warning: Could not retrieve celebrity image for morphing: {str(img_error)}")
                best_match_name = best_match.get('FullName', 'Unknown') if best_match else None
                return {
                    "status": "success",
                    "message": "Search completed successfully. (Note: Best match image could not be retrieved for morphing)",
                    "matches": results,
                    "best_match": best_match_name,
                    "morph_credentials": None
                }

        best_match_name = best_match.get('FullName') if best_match else None

        return {
            "status": "success",
            "message": "Search completed successfully.",
            "matches": results,
            "best_match": best_match_name,
            "morph_credentials": morph_credentials
        }

    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Error searching for lookalikes: {str(e)}",
            "matches": [],
            "best_match": None,
            "morph_credentials": None
        }