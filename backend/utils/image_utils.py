from PIL import Image
import io

def convert_image_to_bytes(image: Image.Image) -> bytes:
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    elif image.mode == "L":
        image = image.convert("RGB")

    stream = io.BytesIO()
    image.save(stream, format="JPEG")
    return stream.getvalue()
