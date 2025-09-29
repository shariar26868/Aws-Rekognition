from fastapi import APIRouter, HTTPException, Query
from backend.services.aws_service import AWSService
from backend.services.morph_service import MorphService
from backend.config import CELEBRITY_BUCKET
import uuid

router = APIRouter()
aws_service = AWSService()
morph_service = MorphService()

@router.get("/video")
async def morph_video(
    user_image_key: str = Query(..., description="S3 key of the stored user image from search response"),
    celebrity_image_key: str = Query(..., description="S3 key of the stored celebrity image from search response")
):
    try:
        # Retrieve stored images from S3 using the provided keys
        user_bytes = aws_service.get_s3_image(CELEBRITY_BUCKET, user_image_key)
        celebrity_bytes = aws_service.get_s3_image(CELEBRITY_BUCKET, celebrity_image_key)
        
        # Generate morphing video with 5-10 seconds duration
        num_frames = 180
        frames = morph_service.morph_images(user_bytes, celebrity_bytes, num_frames)
        video_io = morph_service.create_video(frames, fps=30)

        # ✅ Upload the video to S3
        video_key = f"morph_videos/{uuid.uuid4()}.mp4"
        aws_service.upload_to_s3(video_io.getvalue(), CELEBRITY_BUCKET, video_key, {"Type": "morph_video"})

        # ✅ Generate a presigned URL for the video
        video_url = aws_service.generate_presigned_url(CELEBRITY_BUCKET, video_key, expiration=3600)

        return {
            "message": "Morph video created successfully",
            "video_key": video_key,
            "video_url": video_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
