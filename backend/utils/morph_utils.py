import cv2
import numpy as np

def resize_image_to_match(source_img, target_img):
    """
    Resize source image to match target image dimensions.
    
    Args:
        source_img: Source image (numpy array)
        target_img: Target image (numpy array)
    
    Returns:
        Resized source image
    """
    h, w = target_img.shape[:2]
    return cv2.resize(source_img, (w, h))

def normalize_image(img):
    """
    Normalize image pixel values to [0, 1].
    
    Args:
        img: Input image (numpy array)
    
    Returns:
        Normalized image
    """
    return img.astype(np.float32) / 255.0

def denormalize_image(img):
    """
    Denormalize image pixel values back to [0, 255].
    
    Args:
        img: Normalized image (numpy array)
    
    Returns:
        Denormalized image
    """
    return (img * 255.0).astype(np.uint8)

def validate_image(img):
    """
    Validate if image is valid for processing.
    
    Args:
        img: Input image (numpy array)
    
    Returns:
        Boolean indicating if image is valid
    """
    if img is None:
        return False
    if len(img.shape) != 3 or img.shape[2] != 3:
        return False
    if img.size == 0:
        return False
    return True