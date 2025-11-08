from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from backend.services.aws_service import AWSService
from backend.services.windows_morph_service import WindowsMorphService
from backend.config import CELEBRITY_BUCKET, NORMAL_BUCKET
from io import BytesIO
import uuid

router = APIRouter()
aws_service = AWSService()
morph_service = WindowsMorphService()  # Windows-compatible local morphing


@router.get("/video")
async def morph_video(
    request: Request,
    user_image_key: str = Query(..., description="S3 key of the stored user image"),
    celebrity_image_key: str = Query(..., description="S3 key of the stored celebrity/normal image"),
    bucket: str = Query("celebrity", description="Bucket type: 'celebrity' or 'normal'")
):
    """
    Create a morph video between user and celebrity/normal person images.
    Returns JSON with video URLs (not streaming).
    """
    try:
        # Determine bucket
        source_bucket = NORMAL_BUCKET if bucket.lower() == "normal" else CELEBRITY_BUCKET
        print(f"✓ Using bucket: {source_bucket}")
        
        # Get images from S3
        print("📥 Downloading images from S3...")
        user_bytes = aws_service.get_s3_image(source_bucket, user_image_key)
        celebrity_bytes = aws_service.get_s3_image(source_bucket, celebrity_image_key)
        
        # Generate morph video using Windows-compatible service
        print("🎬 Starting local morphing (Windows compatible)...")
        video_io = morph_service.create_morph_video(user_bytes, celebrity_bytes)
        
        # Get video bytes
        video_bytes = video_io.getvalue()
        
        # Upload to S3
        print("☁️ Uploading video to S3...")
        video_id = str(uuid.uuid4())
        video_key = f"morph_videos/{video_id}.mp4"
        aws_service.upload_video_to_s3(video_bytes, source_bucket, video_key)
        
        # Generate presigned URL (1 year expiry)
        video_url = aws_service.generate_presigned_url(source_bucket, video_key, expiration=31536000)
        
        # Get base URL dynamically from request
        base_url = str(request.base_url).rstrip('/')
        
        print(f"✅ Video created successfully: {video_id}")
        
        # Return JSON response
        return {
            "message": "Morph video created successfully",
            "video_id": video_id,
            "video_key": video_key,
            "video_url": video_url,  # Direct S3 URL - Use this!
            "download_url": video_url,  # Same as video_url for clarity
            "play_url": f"{base_url}morph/video/play/{video_id}?bucket={bucket}",
            "stream_url": f"{base_url}morph/video/stream/{video_id}?bucket={bucket}",
            "bucket_used": source_bucket,
            "expires_in": "1 year",
            "generation_method": "Local Windows-compatible morphing",
            "note": "Use 'video_url' to access the video directly. The URL expires in 1 year."
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error: {error_message}")
        raise HTTPException(
            status_code=400, 
            detail=f"Video generation failed: {error_message}"
        )


@router.get("/video/play/{video_id}")
async def play_video(
    video_id: str,
    bucket: str = Query("celebrity", description="Bucket type: 'celebrity' or 'normal'")
):
    """
    Stream video for direct browser playback.
    """
    try:
        source_bucket = NORMAL_BUCKET if bucket.lower() == "normal" else CELEBRITY_BUCKET
        video_key = f"morph_videos/{video_id}.mp4"
        
        # Get video from S3
        video_bytes = aws_service.get_s3_image(source_bucket, video_key)
        
        # Stream to browser
        video_io = BytesIO(video_bytes)
        
        return StreamingResponse(
            video_io,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"inline; filename=morph_{video_id}.mp4",
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")


@router.get("/video/stream/{video_id}")
async def stream_video(
    video_id: str,
    bucket: str = Query("celebrity", description="Bucket type: 'celebrity' or 'normal'")
):
    """
    Alternative streaming endpoint (same as play).
    """
    return await play_video(video_id, bucket)


@router.get("/video/info/{video_id}")
async def get_video_info(
    video_id: str,
    bucket: str = Query("celebrity", description="Bucket type: 'celebrity' or 'normal'")
):
    """
    Get video information and download URL for a previously generated video.
    """
    try:
        source_bucket = NORMAL_BUCKET if bucket.lower() == "normal" else CELEBRITY_BUCKET
        video_key = f"morph_videos/{video_id}.mp4"
        
        # Generate presigned URL
        video_url = aws_service.generate_presigned_url(source_bucket, video_key, expiration=3600)
        
        return {
            "video_id": video_id,
            "video_key": video_key,
            "video_url": video_url,
            "download_url": video_url,
            "bucket": source_bucket,
            "expires_in": "1 hour"
        }
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")


@router.get("/video/download/{video_id}")
async def download_video(
    video_id: str,
    bucket: str = Query("celebrity", description="Bucket type: 'celebrity' or 'normal'")
):
    """
    Download previously generated video from S3.
    """
    try:
        source_bucket = NORMAL_BUCKET if bucket.lower() == "normal" else CELEBRITY_BUCKET
        video_key = f"morph_videos/{video_id}.mp4"
        
        # Get video from S3
        video_bytes = aws_service.get_s3_image(source_bucket, video_key)
        
        # Stream to browser for download
        video_io = BytesIO(video_bytes)
        
        return StreamingResponse(
            video_io,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename=morph_{video_id}.mp4"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")