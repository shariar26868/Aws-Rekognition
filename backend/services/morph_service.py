from io import BytesIO
import cv2
import numpy as np
from backend.video_face_transition import VideoFaceTransition

class MorphService:
    def __init__(self):
        self.face_transition = VideoFaceTransition()

    def morph_images(self, user_image_bytes, celebrity_image_bytes, num_frames=300):
        """
        Morph between two images using face-focused blending.
        
        Args:
            user_image_bytes: Bytes of the user image
            celebrity_image_bytes: Bytes of the celebrity image
            num_frames: Number of frames for the morphing sequence (300 for 10 seconds at 30 FPS)
        
        Returns:
            List of numpy arrays representing the morphed frames
        """
        # Convert image bytes to numpy arrays
        user_array = np.frombuffer(user_image_bytes, np.uint8)
        celebrity_array = np.frombuffer(celebrity_image_bytes, np.uint8)
        user_img = cv2.imdecode(user_array, cv2.IMREAD_COLOR)
        celebrity_img = cv2.imdecode(celebrity_array, cv2.IMREAD_COLOR)
        h, w = user_img.shape[:2]
        celebrity_img = cv2.resize(celebrity_img, (w, h))
        morph_frames = []
        for i in range(num_frames):
            progress = i / (num_frames - 1)
            if progress < 0.5:
                alpha = 2 * progress * progress
            else:
                alpha = 1 - 2 * (1 - progress) * (1 - progress)
            morphed_frame = self.face_transition.blend_frames_with_face_focus(
                user_img, celebrity_img, alpha, focus_face=True
            )
            morph_frames.append(morphed_frame)
        
        return morph_frames

    def create_video(self, frames, fps=30):
        """
        Create a video from a list of frames.
        
        Args:
            frames: List of numpy arrays (frames)
            fps: Frames per second for the output video
        
        Returns:
            BytesIO object containing the video
        """
        if not frames:
            raise ValueError("No frames provided for video creation")
        height, width = frames[0].shape[:2]
        video_io = BytesIO()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('temp.mp4', fourcc, fps, (width, height))
        for frame in frames:
            out.write(frame)        
        out.release()
        with open('temp.mp4', 'rb') as f:
            video_io.write(f.read())
        
        video_io.seek(0)
        return video_io