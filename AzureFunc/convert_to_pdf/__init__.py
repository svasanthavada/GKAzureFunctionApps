import logging
import azure.functions as func
import base64
import tempfile
import os

from weasyprint import HTML
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def docx_to_pdf(input_path, output_path):
    """Convert .docx to PDF using python-docx + reportlab (basic text only)."""
    doc = Document(input_path)

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    y = height - 40

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            c.drawString(40, y, text)
            y -= 20
            if y < 40:  # new page if needed
                c.showPage()
                y = height - 40

    c.save()


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing file conversion request...")

    try:
        # Expect JSON: { "fileName": "sample.html", "fileContent": "<base64>" }
        req_body = req.get_json()
        file_content = req_body.get("fileContent")
        file_name = req_body.get("fileName")

        if not file_content or not file_name:
            return func.HttpResponse(
                "Missing 'fileContent' or 'fileName'.",
                status_code=400
            )

        # Decode incoming file
        file_bytes = base64.b64decode(file_content)

        # Temp dir for work
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, file_name)
            output_path = os.path.join(tmpdir, "output.pdf")

            with open(input_path, "wb") as f:
                f.write(file_bytes)

            # Conversion logic
            if file_name.lower().endswith(".html"):
                HTML(input_path).write_pdf(output_path)
            elif file_name.lower().endswith(".docx"):
                docx_to_pdf(input_path, output_path)
            else:
                return func.HttpResponse(
                    "Unsupported file type. Only .html and .docx are allowed.",
                    status_code=400
                )

            with open(output_path, "rb") as f:
                pdf_bytes = f.read()

        # Return PDF as binary (like OneDrive Convert to PDF)
        return func.HttpResponse(
            body=pdf_bytes,
            status_code=200,
            mimetype="application/pdf"
        )

    except Exception as e:
        logging.error(f"Conversion error: {e}", exc_info=True)
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )