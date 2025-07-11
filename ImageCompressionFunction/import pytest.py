import test_compress_image.py
import json
import base64
import io
from PIL import Image
from . import compress_image

# test___init__.py


import azure.functions as func

class MockHttpRequest:
    def __init__(self, body_dict):
        self._body = json.dumps(body_dict).encode('utf-8')
    def get_json(self):
        return json.loads(self._body.decode('utf-8'))

def create_base64_image():
    img = Image.new('RGB', (100, 100), color='blue')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def test_compress_image_success():
    image_b64 = create_base64_image()
    req = MockHttpRequest({
        'imageBase64': image_b64,
        'quality': 60,
        'maxWidth': 50
    })
    resp = compress_image(req)
    assert isinstance(resp, func.HttpResponse)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    assert 'compressedImageBase64' in data
    assert data['originalSize'] > data['compressedSize']

def test_compress_image_missing_base64():
    req = MockHttpRequest({})
    resp = compress_image(req)
    assert resp.status_code == 400
    assert b"base64-encoded image" in resp.get_body()

def test_compress_image_invalid_base64():
    req = MockHttpRequest({'imageBase64': 'not_base64!'})
    resp = compress_image(req)
    assert resp.status_code == 500
    assert b"Error processing image" in resp.get_body()
    
