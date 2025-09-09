from src.product_promotion_graph import create_product_promotion_graph
from src.state import State, ProductPromotionData, UploadedImage
import re
import os
import tempfile
from pathlib import Path

def parse_product_info(product_info_str):
    # Enhanced parser for Slack input - handles both structured and sentence form
    data = {}
    
    # First try structured format
    patterns = {
        'name': r'Product Name:\s*(.*)',
        'description': r'Description:\s*(.*)',
        'target_audience': r'Target Audience:\s*(.*)',
        'features': r'Key Features:\s*((?:- .*(?:\n|$))+)',
        'benefits': r'Benefits:\s*((?:- .*(?:\n|$))+)',
        'call_to_action': r'Call to Action:\s*(.*)',
        'website': r'Website:\s*(.*)',
        'contact': r'Contact:\s*(.*)',
    }
    
    # Check if input is structured format
    has_structured_format = any(re.search(pat, product_info_str, re.IGNORECASE) for pat in patterns.values())
    
    if has_structured_format:
        # Parse structured format
        for key, pat in patterns.items():
            match = re.search(pat, product_info_str, re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()
        
        # Features as list
        if 'features' in data:
            data['features'] = [f.strip('- ').strip() for f in data['features'].split('\n') if f.strip()]
        
        # Benefits as list
        if 'benefits' in data:
            data['benefits'] = [f.strip('- ').strip() for f in data['benefits'].split('\n') if f.strip()]
    else:
        # Handle sentence form - extract key information from natural language
        description = product_info_str.strip()
        
        # Try to extract product name from the beginning
        name_match = re.search(r'(?:my product is|i have a|the name of my product is)\s+([^,\.]+)', description, re.IGNORECASE)
        if name_match:
            data['name'] = name_match.group(1).strip()
        
        # Try to extract target audience
        audience_match = re.search(r'(?:target audience|audience|for)\s+(?:are|is)\s+([^,\.]+)', description, re.IGNORECASE)
        if audience_match:
            data['target_audience'] = audience_match.group(1).strip()
        
        # Try to extract features
        features_match = re.search(r'(?:features include|features|includes?)\s+([^,\.]+)', description, re.IGNORECASE)
        if features_match:
            features_text = features_match.group(1)
            # Split by common separators
            features = [f.strip() for f in re.split(r'[,;]', features_text) if f.strip()]
            data['features'] = features
        
        # Set description
        data['description'] = description
    
    return data

def save_slack_image_to_temp(image_bytes: bytes, filename: str) -> str:
    """Save uploaded image from Slack to temporary file"""
    # Create temp directory if it doesn't exist
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    # Save image to temp file
    temp_path = temp_dir / filename
    with open(temp_path, "wb") as f:
        f.write(image_bytes)
    
    return str(temp_path)

def create_uploaded_image_from_slack(image_bytes: bytes, filename: str) -> UploadedImage:
    """Create UploadedImage object from Slack upload"""
    file_path = save_slack_image_to_temp(image_bytes, filename)
    file_size = len(image_bytes)
    
    return UploadedImage(
        file_path=file_path,
        file_name=filename,
        file_size=file_size,
        description=None
    )

def run_product_promotion_slack(product_info_str, uploaded_images=None):
    """
    Run product promotion workflow for Slack integration
    
    Args:
        product_info_str: Product information from Slack
        uploaded_images: List of UploadedImage objects from Slack uploads
    """
    # Parse product info
    parsed = parse_product_info(product_info_str)
    # Fallbacks for missing fields
    name = parsed.get('name', 'Your Product')
    description = parsed.get('description', product_info_str)
    target_audience = parsed.get('target_audience', 'LinkedIn audience')
    features = parsed.get('features', [])
    benefits = parsed.get('benefits', [])
    call_to_action = parsed.get('call_to_action', 'Learn more!')
    website = parsed.get('website', '')
    contact = parsed.get('contact', '')

    # Build ProductPromotionData
    product_data = ProductPromotionData(
        name=name,
        description=description,
        target_audience=target_audience,
        features=features,
        benefits=benefits,
        call_to_action=call_to_action,
        website=website,
        contact=contact
    )

    # Prepare initial state with uploaded images if provided
    initial_state = State(
        product_data=product_data,
        workflow_status="promotion",
        promotion_status="pending",
        messages=[{"role": "user", "content": "Create promotional LinkedIn content for a product or work"}]
    )
    
    # Add uploaded images if provided
    if uploaded_images:
        initial_state["uploaded_images"] = uploaded_images

    # Run the workflow
    graph = create_product_promotion_graph()
    result = graph.invoke(initial_state)
    return result

def get_pdf_for_slack(result):
    """Extract PDF path from result for Slack file upload"""
    pdf_path = result.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        return pdf_path
    return None

def cleanup_temp_files(uploaded_images):
    """Clean up temporary uploaded files"""
    if uploaded_images:
        for img in uploaded_images:
            try:
                if os.path.exists(img.file_path):
                    os.remove(img.file_path)
            except Exception as e:
                print(f"Error cleaning up {img.file_path}: {e}") 