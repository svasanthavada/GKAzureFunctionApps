import azure.functions as func
import logging
from PIL import Image
import base64
import io
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing image compression request.')

    try:
        req_body = req.get_json()
        base64_string = req_body.get('imageBase64')
        quality = req_body.get('quality', 80)

        if not base64_string:
            return func.HttpResponse(
                "Please provide a base64-encoded image in the request body.",
                status_code=400
            )

        # Convert base64 to bytes
        image_data = base64.b64decode(base64_string)
        original_size = len(image_data)  # ✅ track original size early

        # Load the image
        image = Image.open(io.BytesIO(image_data))

        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background

        # Resize to fixed 400x600
        image = image.resize((400, 600), Image.Resampling.LANCZOS)

        # Compress to JPEG
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=quality, optimize=True)
        compressed_image = output_buffer.getvalue()
        compressed_size = len(compressed_image)  # ✅ get compressed size

        # Encode compressed image to base64
        compressed_base64 = base64.b64encode(compressed_image).decode("utf-8")

        return func.HttpResponse(
            json.dumps({
                "compressedImageBase64": compressed_base64,
                "originalSize": original_size,
                "compressedSize": compressed_size
            }),
            mimetype="application/json"
        )

    except Exception as e:
        logging.exception("Error in image processing")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
