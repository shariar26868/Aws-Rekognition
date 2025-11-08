import cv2
import numpy as np
from io import BytesIO
import imageio
import tempfile
import os

class WindowsMorphService:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def bytes_to_image(self, image_bytes):
        """Convert bytes to OpenCV image"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    
    def make_dimensions_even(self, width, height):
        """Ensure dimensions are even numbers for H.264 encoding"""
        if width % 2 != 0:
            width = width - 1
        if height % 2 != 0:
            height = height - 1
        return width, height
    
    def resize_to_match(self, img1, img2, max_size=720):
        """Resize both images to same EVEN dimensions"""
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        target_h = max(h1, h2)
        target_w = max(w1, w2)
        
        # Limit max dimension
        if target_h > max_size or target_w > max_size:
            scale = max_size / max(target_h, target_w)
            target_h = int(target_h * scale)
            target_w = int(target_w * scale)
        
        # Make dimensions even
        target_w, target_h = self.make_dimensions_even(target_w, target_h)
        
        img1_resized = cv2.resize(img1, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        img2_resized = cv2.resize(img2, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        
        return img1_resized, img2_resized
    
    def detect_face_bbox(self, img):
        """Detect face bounding box"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            return max(faces, key=lambda f: f[2] * f[3])
        return None
    
    def align_faces(self, img1, img2):
        """Align faces to center position"""
        face1 = self.detect_face_bbox(img1)
        face2 = self.detect_face_bbox(img2)
        
        if face1 is None or face2 is None:
            return img1, img2
        
        h, w = img1.shape[:2]
        center_target = (w//2, h//2)
        
        # Align face1
        x1, y1, w1, h1 = face1
        center1 = (x1 + w1//2, y1 + h1//2)
        dx1 = center_target[0] - center1[0]
        dy1 = center_target[1] - center1[1]
        M1 = np.float32([[1, 0, dx1], [0, 1, dy1]])
        img1_aligned = cv2.warpAffine(img1, M1, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        # Align face2
        x2, y2, w2, h2 = face2
        center2 = (x2 + w2//2, y2 + h2//2)
        dx2 = center_target[0] - center2[0]
        dy2 = center_target[1] - center2[1]
        M2 = np.float32([[1, 0, dx2], [0, 1, dy2]])
        img2_aligned = cv2.warpAffine(img2, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        return img1_aligned, img2_aligned
    
    def create_smooth_blend(self, img1, img2, alpha):
        """Create smooth blend with easing"""
        # Ease-in-out curve
        if alpha < 0.5:
            eased_alpha = 2 * alpha * alpha
        else:
            eased_alpha = 1 - 2 * (1 - alpha) * (1 - alpha)
        
        blended = cv2.addWeighted(
            img1.astype(np.float32), 1 - eased_alpha,
            img2.astype(np.float32), eased_alpha,
            0
        )
        
        return blended.astype(np.uint8)
    
    def create_morph_frames(self, user_image_bytes, celebrity_image_bytes):
        """
        Create morphing frames: User → Transition → Celebrity
        Total: 150 frames (5 seconds at 30fps)
        """
        print(f"🎬 Creating morph frames...")
        
        user_img = self.bytes_to_image(user_image_bytes)
        celebrity_img = self.bytes_to_image(celebrity_image_bytes)
        
        if user_img is None or celebrity_img is None:
            raise ValueError("Failed to decode images")
        
        # Resize and align
        user_img, celebrity_img = self.resize_to_match(user_img, celebrity_img)
        user_img_aligned, celebrity_img_aligned = self.align_faces(user_img, celebrity_img)
        
        # Verify dimensions are even
        h, w = user_img_aligned.shape[:2]
        print(f"   Frame dimensions: {w}x{h} (even: {w%2==0 and h%2==0})")
        
        # Convert BGR to RGB for imageio
        user_img_rgb = cv2.cvtColor(user_img_aligned, cv2.COLOR_BGR2RGB)
        celebrity_img_rgb = cv2.cvtColor(celebrity_img_aligned, cv2.COLOR_BGR2RGB)
        
        frames = []
        
        # Hold user image (1 second = 30 frames)
        print("   Creating user hold frames (1s)...")
        for _ in range(30):
            frames.append(user_img_rgb.copy())
        
        # Morphing transition (3 seconds = 90 frames)
        print("   Creating morph transition frames (3s)...")
        morph_frames = 90
        for i in range(morph_frames):
            alpha = i / (morph_frames - 1)
            # Blend in RGB
            morphed_bgr = self.create_smooth_blend(user_img_aligned, celebrity_img_aligned, alpha)
            morphed_rgb = cv2.cvtColor(morphed_bgr, cv2.COLOR_BGR2RGB)
            frames.append(morphed_rgb)
        
        # Hold celebrity image (1 second = 30 frames)
        print("   Creating celebrity hold frames (1s)...")
        for _ in range(30):
            frames.append(celebrity_img_rgb.copy())
        
        print(f"✓ Created {len(frames)} frames")
        return frames
    
    def create_video_with_imageio(self, frames, fps=30):
        """
        Create video using imageio-ffmpeg (works on Windows without FFmpeg install!)
        """
        if not frames:
            raise ValueError("No frames to create video")
        
        print(f"🎥 Encoding video with imageio (Windows compatible)...")
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Use imageio to create video with proper settings
            writer = imageio.get_writer(
                temp_path,
                fps=fps,
                codec='libx264',
                quality=8,  # 0-10, higher is better
                pixelformat='yuv420p',
                macro_block_size=None,  # Let FFmpeg handle this
                ffmpeg_params=[
                    '-preset', 'medium',
                    '-crf', '23'
                ]
            )
            
            # Write all frames
            for i, frame in enumerate(frames):
                writer.append_data(frame)
                
                if (i + 1) % 30 == 0:
                    print(f"   Encoded {i+1}/{len(frames)} frames")
            
            writer.close()
            
            # Check if file was created
            if not os.path.exists(temp_path):
                raise RuntimeError("Video file was not created")
            
            file_size = os.path.getsize(temp_path)
            if file_size == 0:
                raise RuntimeError("Video file is empty")
            
            # Read video bytes
            with open(temp_path, 'rb') as f:
                video_bytes = f.read()
            
            video_size_mb = len(video_bytes) / (1024 * 1024)
            print(f"✓ Video created: {len(frames)} frames, {fps}fps, {video_size_mb:.2f}MB")
            
            return BytesIO(video_bytes)
        
        except Exception as e:
            raise RuntimeError(f"Video creation failed: {str(e)}")
        
        finally:
            # Cleanup
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
    
    def create_morph_video(self, user_image_bytes, celebrity_image_bytes):
        """
        Main function: Create complete morph video
        Windows-compatible - no FFmpeg installation needed!
        """
        # Create frames
        frames = self.create_morph_frames(user_image_bytes, celebrity_image_bytes)
        
        # Create video with imageio (includes embedded FFmpeg)
        video_io = self.create_video_with_imageio(frames, fps=30)
        
        return video_io