import io
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from typing import Tuple

def get_suggestion_message() -> str:
    """
    Provide a user-friendly suggestion message for image upload issues.
    """
    return (
        "Please upload a valid image in one of the following formats: JPG, JPEG, PNG, or WEBP. "
        "Ensure the image is clear, not corrupted, and smaller than 5MB. "
        "For best results, use a front-facing photo with good lighting and a single face."
    )

def validate_image_for_rekognition(image_bytes: bytes) -> Tuple[bool, str]:
    """
    Validate image for AWS Rekognition requirements:
    - Format: JPEG or PNG (WEBP allowed before conversion)
    - Integrity: Valid image that can be opened
    - Resolution: At least 80x80 pixels
    """
    try:
        # Check file size (max 5MB)
        if len(image_bytes) > 5 * 1024 * 1024:
            return False, f"Image file size exceeds 5MB. {get_suggestion_message()}"

        # Verify image integrity
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()  # Ensures the image is not corrupted
        img = Image.open(io.BytesIO(image_bytes))  # Re-open for further checks
        img.load()

        # Check resolution (minimum 80x80 for Rekognition)
        width, height = img.size
        if width < 80 or height < 80:
            return False, f"Image resolution ({width}x{height}) is too low. Minimum is 80x80 pixels. {get_suggestion_message()}"

        # Allow WEBP, JPEG, or PNG (WEBP will be converted later)
        if img.format not in {"JPEG", "PNG", "WEBP"}:
            return False, f"Image format ({img.format}) is not supported. {get_suggestion_message()}"

        return True, "Image is valid for processing."

    except UnidentifiedImageError:
        return False, f"Invalid or corrupted image file. {get_suggestion_message()}"
    except Exception as e:
        return False, f"Error validating image: {str(e)}. {get_suggestion_message()}"

def convert_image_to_bytes(image: Image.Image) -> bytes:
    """
    Convert PIL Image to bytes in JPEG format.
    """
    img_byte_arr = io.BytesIO()
    image.convert("RGB").save(img_byte_arr, format='JPEG', quality=85)  # Reduced quality to minimize size
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

def preprocess_image_bytes(image_bytes: bytes) -> bytes:
    """
    Preprocess image bytes:
    - Convert .webp or other formats to JPEG
    - Validate for AWS Rekognition
    - Return clean JPEG bytes for OpenCV face detection and AWS Rekognition
    """
    try:
        # Validate initial image (allow WEBP)
        is_valid, message = validate_image_for_rekognition(image_bytes)
        if not is_valid:
            raise ValueError(message)

        img = Image.open(io.BytesIO(image_bytes))
        img.load()

        # Convert to JPEG with optimized quality
        buffer = io.BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)
        jpeg_bytes = buffer.getvalue()

        # Validate converted image (must be JPEG or PNG)
        try:
            converted_img = Image.open(io.BytesIO(jpeg_bytes))
            converted_img.verify()
            converted_img = Image.open(io.BytesIO(jpeg_bytes))
            if converted_img.format != "JPEG":
                raise ValueError(f"Converted image is not JPEG. {get_suggestion_message()}")
            width, height = converted_img.size
            if width < 80 or height < 80:
                raise ValueError(f"Converted image resolution ({width}x{height}) is too low. {get_suggestion_message()}")
        except Exception as e:
            raise ValueError(f"Invalid converted image: {str(e)}. {get_suggestion_message()}")

        return jpeg_bytes

    except UnidentifiedImageError:
        raise ValueError(f"Invalid or corrupted image file. {get_suggestion_message()}")
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")

def validate_face_visibility(image_bytes: bytes) -> Tuple[bool, str]:
    """
    Validate if a face is visible in the image.
    More lenient validation - allows slightly angled faces and various distances.
    Rejects only: no face, side profiles, multiple faces, very blurry images, or fully hidden faces.
    """
    try:
        # Step 1: Preprocess to JPEG and validate for Rekognition
        image_bytes = preprocess_image_bytes(image_bytes)

        # Step 2: Decode image for OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return False, f"Unable to process the image. {get_suggestion_message()}"

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

        if not face_cascade or not profile_cascade or not eye_cascade:
            return False, f"Failed to load face detection models. Please try again later."

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect frontal faces with STRICT parameters to avoid false positives
        frontal_faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=7, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Detect profile faces (stricter - we want to reject these)
        profile_faces_left = profile_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=7, minSize=(30, 30)
        )

        gray_flipped = cv2.flip(gray, 1)
        profile_faces_right = profile_cascade.detectMultiScale(
            gray_flipped, scaleFactor=1.2, minNeighbors=7, minSize=(30, 30)
        )

        total_profile_faces = len(profile_faces_left) + len(profile_faces_right)

        # REJECT: Side profile detected
        if len(frontal_faces) == 0 and total_profile_faces > 0:
            return False, "Side profile detected! Please upload a FRONT-FACING photo where you are looking directly at the camera."

        # REJECT: No face detected
        if len(frontal_faces) == 0 and total_profile_faces == 0:
            return False, "No face detected! Make sure your face is clear, well-lit, and looking at the camera."

        # Select the largest frontal face to handle multiple detections of the same face
        if len(frontal_faces) > 1:
            areas = [w * h for _, _, w, h in frontal_faces]
            largest_idx = np.argmax(areas)
            frontal_faces = [frontal_faces[largest_idx]]

        x, y, w, h = frontal_faces[0]
        face_roi_gray = gray[y:y+h, x:x+w]
        img_height, img_width = img.shape[:2]
        face_area = w * h
        img_area = img_width * img_height
        face_ratio = face_area / img_area

        # REJECT: Face is extremely small (too far away)
        if face_ratio < 0.002:
            return False, "Face is too small or too far away! Please take a closer photo."

        # REJECT: Face is too close/cropped (more than 80% of image)
        if face_ratio > 0.8:
            return False, "Face is cropped or too close! Please ensure your entire face fits within the frame."

        # Check for eyes (more lenient)
        eyes = eye_cascade.detectMultiScale(face_roi_gray, scaleFactor=1.1, minNeighbors=1, minSize=(5, 5))
        if len(eyes) < 1:
            return False, "Eyes not clearly visible! Please look directly at the camera with both eyes open."

        # REJECT: Face is too blurry (Laplacian variance < 20 is very blurry)
        laplacian_var = cv2.Laplacian(face_roi_gray, cv2.CV_64F).var()
        if laplacian_var < 30:
            return False, "Image is too blurry! Please upload a clearer, sharper photo."

        # Check face aspect ratio (more lenient - allows angled faces)
        face_aspect_ratio = w / h
        if face_aspect_ratio < 0.3 or face_aspect_ratio > 2.0:
            return False, "Face appears distorted or partially cut off!"

        return True, "Face validation successful."

    except ValueError as ve:
        return False, str(ve)
    except Exception as e:
        return False, f"Error validating image: {str(e)}"





