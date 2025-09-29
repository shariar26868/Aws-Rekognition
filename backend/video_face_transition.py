import cv2
import numpy as np
import os

class VideoFaceTransition:
    def __init__(self):
        try:
            self.detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            print("Face detector initialized")
        except:
            print("Using basic blending (face detection not available)")
            self.detector = None
    
    def extract_frames(self, video_path, max_frames=None, skip_frames=1):
        print(f"📽️ Extracting frames from {video_path}...")
        
        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames for faster processing
            if frame_count % skip_frames == 0:
                frames.append(frame)
                extracted_count += 1
                
                if max_frames and extracted_count >= max_frames:
                    break
            
            frame_count += 1
        
        cap.release()
        print(f"Extracted {len(frames)} frames (skipped every {skip_frames} frames)")
        return frames
    
    def get_video_info(self, video_path):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        return {
            'fps': fps,
            'width': width,
            'height': height,
            'frame_count': frame_count,
            'duration': frame_count / fps if fps > 0 else 0
        }
    
    def detect_face_region(self, frame):
        if self.detector is None:
            h, w = frame.shape[:2]
            return (w//4, h//4, w//2, h//2)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            return tuple(largest_face)
        else:
            h, w = frame.shape[:2]
            return (w//4, h//4, w//2, h//2)
    
    def get_face_center(self, face_rect):
        """Get center point of face rectangle"""
        x, y, w, h = face_rect
        return (x + w//2, y + h//2)
    
    def align_face_to_center(self, frame, target_center=None):
        """Align face to center or specific position"""
        face_rect = self.detect_face_region(frame)
        face_center = self.get_face_center(face_rect)
        
        h, w = frame.shape[:2]
        
        # If no target center specified, use image center
        if target_center is None:
            target_center = (w//2, h//2)
        
        # Calculate translation needed
        dx = target_center[0] - face_center[0]
        dy = target_center[1] - face_center[1]
        
        # Create translation matrix
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        
        # Apply translation
        aligned_frame = cv2.warpAffine(frame, M, (w, h))
        
        return aligned_frame, (dx, dy)
    
    def resize_and_align_faces_fast(self, frame1, frame2, target_size=(640, 480)):
        """Fast resize and align with fixed target size for speed"""
        # Resize to fixed smaller size for faster processing
        frame1_resized = cv2.resize(frame1, target_size)
        frame2_resized = cv2.resize(frame2, target_size)
        
        # Get face positions
        face1_rect = self.detect_face_region(frame1_resized)
        face2_rect = self.detect_face_region(frame2_resized)
        
        face1_center = self.get_face_center(face1_rect)
        face2_center = self.get_face_center(face2_rect)
        
        # Calculate average center position
        avg_center = (
            (face1_center[0] + face2_center[0]) // 2,
            (face1_center[1] + face2_center[1]) // 2
        )
        
        # Align both faces to average center
        aligned_frame1, _ = self.align_face_to_center(frame1_resized, avg_center)
        aligned_frame2, _ = self.align_face_to_center(frame2_resized, avg_center)
        
        return aligned_frame1, aligned_frame2
    
    def create_face_mask(self, frame, face_rect, feather_size=20):
        x, y, w, h = face_rect
        mask = np.zeros(frame.shape[:2], dtype=np.float32)
        center_x, center_y = x + w//2, y + h//2
        
        # Create elliptical mask around face
        cv2.ellipse(mask, (center_x, center_y), (w//2 + feather_size, h//2 + feather_size), 
                   0, 0, 360, 1, -1)
        
        # Apply Gaussian blur for smooth edges
        mask = cv2.GaussianBlur(mask, (feather_size*2+1, feather_size*2+1), 0)
        mask = mask / mask.max() if mask.max() > 0 else mask
        
        return mask
    
    def blend_frames_with_face_focus(self, frame1, frame2, alpha, focus_face=True):
        """Blend frames with special focus on face region"""
        if not focus_face or self.detector is None:
            return cv2.addWeighted(frame1, 1-alpha, frame2, alpha, 0)
        
        # Get face regions from aligned frames
        face1 = self.detect_face_region(frame1)
        face2 = self.detect_face_region(frame2)
        
        # Create masks for both faces
        mask1 = self.create_face_mask(frame1, face1, feather_size=30)
        mask2 = self.create_face_mask(frame2, face2, feather_size=30)
        
        # Combine masks
        combined_mask = np.maximum(mask1, mask2)
        
        # Enhanced alpha for face region
        face_alpha = alpha * 1.2
        face_alpha = np.clip(face_alpha, 0, 1)
        
        # Create 3-channel mask
        mask_3ch = np.stack([combined_mask] * 3, axis=-1)
        
        # Blend face and body regions separately
        face_blend = cv2.addWeighted(frame1, 1-face_alpha, frame2, face_alpha, 0)
        body_blend = cv2.addWeighted(frame1, 1-alpha, frame2, alpha, 0)
        
        # Combine using mask
        result = face_blend * mask_3ch + body_blend * (1 - mask_3ch)
        return result.astype(np.uint8)
    
    def create_transition_frames_fast(self, frames1, frames2, transition_length=15):
        print(f"Creating {transition_length} transition frames with fast processing...")
        
        end_frame1 = frames1[-1]
        start_frame2 = frames2[0]
        
        # Use fast alignment with smaller resolution
        aligned_frame1, aligned_frame2 = self.resize_and_align_faces_fast(
            end_frame1, start_frame2, target_size=(640, 480)
        )
        
        transition_frames = []
        
        for i in range(transition_length):
            progress = i / (transition_length - 1)
            
            # Faster transition curve - more aggressive
            alpha = progress ** 1.5  # Exponential curve for faster transition
            
            # Simplified blending for speed
            blended = cv2.addWeighted(aligned_frame1, 1-alpha, aligned_frame2, alpha, 0)
            transition_frames.append(blended)
        
        return transition_frames
    
    def create_full_transition_video_fast(self, video1_path, video2_path, 
                                         output_path="fast_transition.mp4",
                                         transition_duration=1.0):
        print("Creating FAST face transition video...")
        
        # Get video info
        info1 = self.get_video_info(video1_path)
        info2 = self.get_video_info(video2_path)
        
        print(f"Video 1: {info1['frame_count']} frames, {info1['duration']:.2f}s")
        print(f"Video 2: {info2['frame_count']} frames, {info2['duration']:.2f}s")
        
        # Extract frames with skipping for speed
        frames1 = self.extract_frames(video1_path, max_frames=60, skip_frames=2)  # Skip every 2nd frame
        frames2 = self.extract_frames(video2_path, max_frames=60, skip_frames=2)
        
        if not frames1 or not frames2:
            print("Error: Could not extract frames")
            return False
        
        # Use higher FPS for smoother but faster transition
        fps = 30  # Fixed high FPS for speed
        transition_frame_count = max(5, int(transition_duration * fps))  # Minimum 5 frames
        
        # Create fast transition
        transition_frames = self.create_transition_frames_fast(
            frames1, frames2, transition_frame_count
        )
        
        # Keep fewer frames from original videos
        video1_keep = min(len(frames1), int(fps * 1.5))  # Only 1.5 seconds
        video2_keep = min(len(frames2), int(fps * 1.5))
        
        # Resize all frames to transition size for consistency
        if transition_frames:
            target_size = (transition_frames[0].shape[1], transition_frames[0].shape[0])
            
            frames1_resized = [cv2.resize(f, target_size) for f in frames1[-video1_keep:]]
            frames2_resized = [cv2.resize(f, target_size) for f in frames2[:video2_keep]]
            
            final_frames = frames1_resized + transition_frames + frames2_resized
        else:
            final_frames = frames1[-video1_keep:] + frames2[:video2_keep]
        
        print(f"Final video: {len(final_frames)} frames at {fps}fps")
        
        # Write video with faster encoding
        if final_frames:
            height, width = final_frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Faster codec
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            for frame in final_frames:
                out.write(frame)
            
            out.release()
            print(f"FAST transition video saved as {output_path}")
            return True
        
        return False
    
    def create_ultra_fast_morph(self, video1_path, video2_path, 
                               output_path="ultra_fast_morph.mp4"):
        print("Creating ULTRA FAST face morph...")
        cap1 = cv2.VideoCapture(video1_path)
        cap1.set(cv2.CAP_PROP_POS_AVI_RATIO, 0.8)
        ret1, frame1 = cap1.read()
        cap1.release()
        
        cap2 = cv2.VideoCapture(video2_path)
        ret2, frame2 = cap2.read()
        cap2.release()
        
        if not ret1 or not ret2:
            print("Could not extract key frames")
            return False
        
        # Fast resize to smaller resolution
        target_size = (480, 360)  # Smaller for speed
        frame1 = cv2.resize(frame1, target_size)
        frame2 = cv2.resize(frame2, target_size)
        
        # Quick alignment
        aligned_frame1, aligned_frame2 = self.resize_and_align_faces_fast(
            frame1, frame2, target_size
        )
        
        # Create very few morph frames for speed
        morph_frames = []
        num_frames = 20  # Reduced from 45
        
        for i in range(num_frames):
            progress = i / (num_frames - 1)
            alpha = progress ** 2  # Faster transition curve
            
            # Simple blending - no complex masking for speed
            morphed = cv2.addWeighted(aligned_frame1, 1-alpha, aligned_frame2, alpha, 0)
            morph_frames.append(morphed)
        
        # Write with fast codec
        h, w = morph_frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, 24, (w, h))  # Higher FPS
        
        for frame in morph_frames:
            out.write(frame)
        
        out.release()
        print(f"Ultra fast morph saved as {output_path}")
        return True

# Usage example
if __name__ == "__main__":
    # Create instance
    processor = VideoFaceTransition()
    
    # Create full transition video with face alignment
    success = processor.create_full_transition_video(
        "video1.mp4", 
        "video2.mp4",
        "aligned_transition.mp4",
        transition_duration=2.5
    )
    
    if success:
        print("✅ Face-aligned transition video created successfully!")
    else:
        print("❌ Failed to create transition video")
    
    # Or create quick morph with alignment
    success = processor.create_quick_face_morph_aligned(
        "video1.mp4",
        "video2.mp4", 
        "aligned_morph.mp4"
    )
    
    if success:
        print("✅ Face-aligned morph created successfully!")
    else:
        print("❌ Failed to create morph")