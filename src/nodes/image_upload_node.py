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
        state: Current workflow state
        
    Returns:
        Updated state with uploaded images
    """
    # Check if images already exist (from Slack session)
    existing_images = state.get("uploaded_images", [])
    if existing_images:
        print("\n" + "="*60)
        print("🖼️  IMAGE UPLOAD")
        print("="*60)
        print(f"Using {len(existing_images)} pre-uploaded images from Slack...")
        print("="*60)
        
        return {
            "uploaded_images": existing_images,
            "promotion_status": "uploading_images",
            "workflow_status": "promotion",
            "messages": [
                {
                    "role": "system",
                    "content": f"Using {len(existing_images)} pre-uploaded images"
                }
            ]
        }
    
    # Normal interactive image upload
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
        
        try:
            # Validate and add image
            if os.path.exists(image_path):
                file_size = os.path.getsize(image_path)
                file_name = os.path.basename(image_path)
                
                uploaded_image = UploadedImage(
                    file_path=image_path,
                    file_name=file_name,
                    file_size=file_size,
                    description=None
                )
                uploaded_images.append(uploaded_image)
                print(f"✅ Added: {file_name}")
            else:
                print(f"❌ File not found: {image_path}")
        except Exception as e:
            print(f"❌ Error adding image: {str(e)}")
    
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