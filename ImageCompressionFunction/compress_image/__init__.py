import azure.functions as func
import logging
from PIL import Image
import base64
import io
import json

app = func.FunctionApp()

@app.route(route="compress_image", auth_level=func.AuthLevel.ANONYMOUS)
def compress_image(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing image compression request.')

    try:
        req_body = req.get_json()
        base64_string = req_body.get('imageBase64')
        quality = req_body.get('quality', 80)
        max_width = req_body.get('maxWidth', 1024)

        if not base64_string:
            return func.HttpResponse(
                "Please provide a base64-encoded image in the request body.",
                status_code=400
            )

        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))

        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.convert('RGBA').split()[-1])
            image = background

        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=quality, optimize=True)
        compressed_image = output_buffer.getvalue()

        compressed_base64 = base64.b64encode(compressed_image).decode('utf-8')

        return func.HttpResponse(
            json.dumps({
                'compressedImageBase64': compressed_base64,
                'originalSize': len(image_data),
                'compressedSize': len(compressed_image)
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        return func.HttpResponse(
            f"Error processing image: {str(e)}",
            status_code=500
        )