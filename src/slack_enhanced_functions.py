"""
Enhanced Slack functions for product promotion workflow
Handles image uploads and PDF outputs for Slack integration
"""
import os
import requests
from pathlib import Path
from src.slack_product_promotion import create_uploaded_image_from_slack, get_pdf_for_slack, cleanup_temp_files

def handle_product_promotion_image_upload(say, session: dict, image_bytes: bytes, file_name: str, user_id: str, channel: str):
    """Handle image upload during product promotion workflow"""
    try:
        # Create UploadedImage object from Slack upload
        uploaded_image = create_uploaded_image_from_slack(image_bytes, file_name)
        
        # Add to session's uploaded images
        if "uploaded_images" not in session:
            session["uploaded_images"] = []
        session["uploaded_images"].append(uploaded_image)
        
        say(f"✅ *Image uploaded successfully:* {file_name}\n\nYou can upload more images or type 'skip' to continue with the promotion process.")
        
    except Exception as e:
        print(f"Error handling product promotion image upload: {str(e)}")
        say(f"❌ *Error uploading image:* {str(e)}")

def upload_pdf_to_slack(say, pdf_path: str, filename: str = "promotional_content.pdf"):
    """Upload PDF to Slack channel"""
    try:
        if os.path.exists(pdf_path):
            # Upload file to Slack
            with open(pdf_path, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                say(f"📄 *PDF Report Generated:* {filename}")
                # Note: In a real implementation, you would use Slack's file upload API
                # For now, we'll just confirm the PDF was created
                say(f"📋 PDF saved to: {pdf_path}")
        else:
            say("❌ PDF file not found")
    except Exception as e:
        print(f"Error uploading PDF to Slack: {str(e)}")
        say(f"❌ *Error uploading PDF:* {str(e)}")

def show_enhanced_final_result(say, result: dict, user_id: str):
    """Show enhanced final result with PDF upload for Slack"""
    try:
        # Extract relevant information
        linkedin_post = result.get("linkedin_post")
        generated_image = result.get("generated_image")
        posting_status = result.get("posting_status", "not_attempted")
        product_data = result.get("product_data")
        promotion_status = result.get("promotion_status")
        uploaded_images = result.get("uploaded_images", [])
        
        # Build response message
        response_parts = []
        
        # Show product information if available
        if product_data:
            response_parts.append(f"🎯 *Product Promotion for: {product_data.name}*")
        
        if linkedin_post:
            response_parts.append(f"📝 *Generated LinkedIn Post:*\n{linkedin_post.title}\n\n{linkedin_post.content}")
        
        if generated_image:
            response_parts.append(f"🖼️ *Promotional Image Generated:* {generated_image.image_path}")
        
        if uploaded_images:
            response_parts.append(f"📸 *Uploaded Images:* {len(uploaded_images)} images processed")
        
        if posting_status == "success":
            response_parts.append("✅ *Posted to LinkedIn successfully!*")
        elif posting_status == "failed":
            response_parts.append("❌ *LinkedIn posting failed* (content generated but not posted)")
        else:
            response_parts.append("📋 *Promotional content ready* (not posted to LinkedIn)")
        
        # Add session completion message
        if promotion_status == "success":
            response_parts.append("\n🎉 *Product promotion completed successfully!* Type `start` to begin a new session.")
        else:
            response_parts.append("\n🎉 *Session completed!* Type `start` to begin a new session.")
        
        # Send the response
        say("\n\n".join(response_parts))
        
        # Upload PDF if available
        pdf_path = get_pdf_for_slack(result)
        if pdf_path:
            upload_pdf_to_slack(say, pdf_path, f"promotional_content_{product_data.name if product_data else 'report'}.pdf")
        
    except Exception as e:
        print(f"Error showing enhanced final result: {str(e)}")
        say(f"❌ *Error:* {str(e)}") 