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

        if not base64_string:
            return func.HttpResponse("Missing imageBase64", status_code=400)

        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))

        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.convert('RGBA').split()[-1])
            image = background

        image = image.resize((400, 600), Image.Resampling.LANCZOS)

        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=quality, optimize=True)

        compressed_base64 = base64.b64encode(output_buffer.getvalue()).decode("utf-8")

        return func.HttpResponse(
            json.dumps({
                "compressedImageBase64": compressed_base64,
                "originalSize": len(image_data),
                "compressedSize": len(output_buffer.getvalue())
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.exception("Error during image compression")
        return func.HttpResponse(str(e), status_code=500)
