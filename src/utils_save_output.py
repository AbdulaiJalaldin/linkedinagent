import os
import requests
import re
from fpdf import FPDF

def clean_text_for_pdf(text: str) -> str:
    """
    Clean text to remove emoji and other characters that might cause encoding issues in PDF.
    """
    # Remove emoji and other Unicode characters that might cause issues
    # Keep basic punctuation and letters
    cleaned = re.sub(r'[^\x00-\x7F\u00A0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF]+', '', text)
    return cleaned

def save_content_and_image_to_pdf(content: str, image_url: str, output_path: str):
    """
    Save the generated content and an image to a PDF file.
    Args:
        content: The text content to include in the PDF.
        image_url: The URL or local path of the image to embed in the PDF.
        output_path: The path where the PDF will be saved.
    """
    # Clean the content to remove problematic characters
    cleaned_content = clean_text_for_pdf(content)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Determine if image_url is a local file or a URL
    is_url = bool(re.match(r'^https?://', image_url, re.IGNORECASE))
    if is_url:
        # Download the image
        image_response = requests.get(image_url)
        image_filename = os.path.join(os.path.dirname(output_path), "_temp_image.png")
        with open(image_filename, "wb") as f:
            f.write(image_response.content)
        image_to_use = image_filename
    else:
        # Use the local file directly
        image_to_use = image_url

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, cleaned_content)
    pdf.ln(10)
    # Insert image (fit width, keep aspect ratio)
    pdf.image(image_to_use, x=10, w=pdf.w - 20)

    # Save PDF
    pdf.output(output_path)

    # Clean up temp image if downloaded
    if is_url and os.path.exists(image_to_use):
        os.remove(image_to_use) 