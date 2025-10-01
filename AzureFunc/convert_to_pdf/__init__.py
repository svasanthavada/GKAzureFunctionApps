import logging
import azure.functions as func
import base64
import tempfile
import os
import pdfkit
from docx2pdf import convert as docx2pdf_convert

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing file conversion request...")

    try:
        # Input should contain fileContent (base64) and fileName
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

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, file_name)
            output_path = os.path.join(tmpdir, "output.pdf")

            # Save input file
            with open(input_path, "wb") as f:
                f.write(file_bytes)

            # Conversion logic
            if file_name.lower().endswith(".html"):
                pdfkit.from_file(input_path, output_path)
            elif file_name.lower().endswith(".docx"):
                docx2pdf_convert(input_path, output_path)
            else:
                return func.HttpResponse(
                    "Unsupported file type. Only .html and .docx are allowed.",
                    status_code=400
                )

            # Read back PDF
            with open(output_path, "rb") as f:
                pdf_bytes = f.read()

        # Encode PDF as base64 for Power Automate
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return func.HttpResponse(
            body=pdf_base64,
            status_code=200,
            mimetype="text/plain"
        )

    except Exception as e:
        logging.error(f"Conversion error: {e}", exc_info=True)
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )
