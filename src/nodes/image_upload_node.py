"""
Image Upload Node for LinkedIn Content Automation Agent
Handles image upload for product promotion content
"""
import os
from pathlib import Path
from typing import Dict, Any
from PIL import Image
from src.state import State, UploadedImage


def image_upload_node(state: State) -> Dict[str, Any]:
    """
    Image Upload node that handles promotional image uploads.
    
    Args:
        state: Current workflow state with product data
        
    Returns:
        Updated state with uploaded images
    """
    print("\n" + "="*60)
    print("🖼️  IMAGE UPLOAD")
    print("="*60)
    print("You can upload promotional images for your work/product.")
    print("Supported formats: JPG, PNG, GIF")
    print("Press Enter without a path to skip image upload.")
    print("="*60)
    
    uploaded_images = []
    
    while True:
        image_path = input("\nEnter image file path (or press Enter to finish): ").strip()
        
        if not image_path:
            break
            
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"❌ File not found: {image_path}")
            continue
            
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        file_ext = Path(image_path).suffix.lower()
        
        if file_ext not in allowed_extensions:
            print(f"❌ Unsupported file format: {file_ext}")
            print(f"Supported formats: {', '.join(allowed_extensions)}")
            continue
            
        # Validate image file
        try:
            with Image.open(image_path) as img:
                img.verify()
            
            # Get file size
            file_size = os.path.getsize(image_path)
            
            # Create UploadedImage object
            uploaded_image = UploadedImage(
                file_path=image_path,
                file_name=Path(image_path).name,
                file_size=file_size,
                description=None
            )
            
            uploaded_images.append(uploaded_image)
            print(f"✅ Image added: {image_path}")
            
        except Exception as e:
            print(f"❌ Invalid image file: {e}")
            continue
    
    return {
        "uploaded_images": uploaded_images,
        "promotion_status": "uploading_images",
        "workflow_status": "promotion",
        "messages": [
            {
                "role": "system",
                "content": f"Uploaded {len(uploaded_images)} images for promotion"
            }
        ]
    } 