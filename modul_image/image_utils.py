import io
import cv2
import numpy as np
import logging
from PIL import Image

from modul_image.watermark import add_watermark
from modul_image.watermark_config import WATERMARK_TEXT, WATERMARK_FONT_SCALE, WATERMARK_COLOR, WATERMARK_BG_COLOR, WATERMARK_BG_OPACITY, WATERMARK_POSITION

logger = logging.getLogger("rich")


def is_image_suitable(image_data, min_width=1024):
    try:
        with Image.open(image_data) as img:
            width, height = img.size
            return width >= min_width and width > height
    except Exception as e:
        logger.error(f"Error checking image suitability: {str(e)}")
        return False

# Update the `resize_and_optimize_image` function in `modul_image/image_utils.py`
def resize_and_optimize_image(image_data, target_width=1200, target_height=760, max_size_kb=100, watermark_text=WATERMARK_TEXT, template_path=None, config=None):
    try:
        # Convert image data to numpy array
        image_data.seek(0)
        file_bytes = np.asarray(bytearray(image_data.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # Get original dimensions
        original_height, original_width = img.shape[:2]

        # Calculate the aspect ratio
        aspect_ratio = original_width / original_height

        # Determine new dimensions while maintaining aspect ratio
        if aspect_ratio > 1:  # Landscape orientation
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else:  # Portrait orientation
            new_height = target_height
            new_width = int(target_height * aspect_ratio)

        # Resize the image
        img_resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

        # Convert the resized image to a PIL Image object
        img_resized_pil = Image.fromarray(cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB))

        # Add watermark
        if template_path and config:
            img_with_watermark = add_watermark(img_resized_pil, template_path, config)
        else:
            img_with_watermark = img_resized_pil

         # Convert the PIL Image back to a numpy array
        img_with_watermark_np = cv2.cvtColor(np.array(img_with_watermark), cv2.COLOR_RGB2BGR)

        # Encode the image to WEBP format with quality adjustment
        quality = 85
        encode_param = [int(cv2.IMWRITE_WEBP_QUALITY), quality]
        while True:
            result, encoded_img = cv2.imencode('.webp', img_with_watermark_np, encode_param)
            size_kb = len(encoded_img) / 1024
            if size_kb <= max_size_kb or quality <= 10:
                break
            quality -= 5
            encode_param = [int(cv2.IMWRITE_WEBP_QUALITY), quality]

        # Convert encoded image to BytesIO
        optimized_image_data = io.BytesIO(encoded_img.tobytes())
        optimized_image_data.seek(0)
        return optimized_image_data
    except Exception as e:
        logger.error(f"Error resizing and optimizing image: {str(e)}")
        return None