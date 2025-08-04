"""
LinkedIn Posting node for LinkedIn Content Automation Agent
Posts generated content to LinkedIn using the LinkedIn API
"""
import os
import requests
import json
from typing import Dict, Any
from src.state import State, LinkedInPost, GeneratedImage
import mimetypes


def linkedin_posting_node(state: State) -> Dict[str, Any]:
    """
    Node to post content to LinkedIn using the LinkedIn API.
    
    Args:
        state: Current workflow state with LinkedIn post and generated image
        
    Returns:
        Updated state with posting results
    """
    linkedin_post: LinkedInPost = state.get("linkedin_post")
    generated_image: GeneratedImage = state.get("generated_image")
    topic = state.get("topic", "")

    if not linkedin_post:
        return {
            "workflow_status": "failed",
            "posting_status": "failed",
            "error_message": "No LinkedIn post available for posting",
            "messages": [
                {"role": "system", "content": "No LinkedIn post found in state."}
            ]
        }

    # Get LinkedIn credentials from environment
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    
    if not all([access_token, client_id, client_secret]):
        return {
            "workflow_status": "failed",
            "posting_status": "failed",
            "error_message": "LinkedIn credentials not found in environment variables",
            "messages": [
                {"role": "system", "content": "LinkedIn credentials (LINKEDIN_ACCESS_TOKEN, LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET) not found in environment."}
            ]
        }

    try:
        # Update status to in progress
        state["workflow_status"] = "posting"
        state["posting_status"] = "in_progress"
        
        # Compose the post content
        post_text = compose_linkedin_post_text(linkedin_post)
        
        print(f"\n--- LinkedIn POST Preview ---")
        print(post_text)
        if generated_image:
            print(f"Image to be posted: {generated_image.image_path}")
        print("--- END POST Preview ---\n")

        # Post to LinkedIn using REST API
        # Print the payload for debugging
        print("\n--- DEBUG: Payload to be sent to LinkedIn (see below if error occurs) ---")
        # We'll print the payload inside post_to_linkedin_rest_api
        post_result = post_to_linkedin_rest_api(post_text, generated_image)
        print("--- END DEBUG PAYLOAD ---\n")

        # Always return the full post_result for debugging
        return post_result
        
    except Exception as e:
        error_msg = f"Error during LinkedIn posting: {str(e)}"
        print(f"LinkedIn posting error: {error_msg}")
        return {
            "workflow_status": "failed",
            "posting_status": "failed",
            "error_message": error_msg,
            "messages": [
                {"role": "system", "content": f"LinkedIn posting failed: {error_msg}"}
            ]
        }


def compose_linkedin_post_text(linkedin_post: LinkedInPost) -> str:
    """
    Compose the LinkedIn post text from the LinkedInPost object.
    
    Args:
        linkedin_post: LinkedInPost object with content
        
    Returns:
        Formatted text for LinkedIn post
    """
    # Start with the title as a hook
    post_parts = [linkedin_post.title]
    
    # Add the main content
    if linkedin_post.content:
        post_parts.append("")  # Empty line for spacing
        post_parts.append(linkedin_post.content)
    
    # Add call to action
    if linkedin_post.call_to_action:
        post_parts.append("")  # Empty line for spacing
        post_parts.append(linkedin_post.call_to_action)
    
    # Add hashtags at the end
    if linkedin_post.hashtags:
        post_parts.append("")  # Empty line for spacing
        hashtag_text = " ".join(linkedin_post.hashtags)
        post_parts.append(hashtag_text)
    
    return "\n".join(post_parts)


def get_user_urn_from_userinfo(access_token: str) -> str:
    """
    Get user URN from LinkedIn's /userinfo endpoint.
    
    Args:
        access_token: LinkedIn access token
        
    Returns:
        User URN (urn:li:person:{user_id}) or error message
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Try the /v2/userinfo endpoint first
        response = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("sub")
            if user_id:
                return f"urn:li:person:{user_id}"
            else:
                print("No 'sub' field found in userinfo response")
                return "userinfo_error"
        else:
            print(f"Userinfo API Error: {response.status_code} - {response.text}")
            return "userinfo_error"
            
    except Exception as e:
        print(f"Error getting user info: {str(e)}")
        return "userinfo_error"


def upload_image_to_linkedin(access_token: str, image_path: str, user_urn: str) -> str:
    """
    Upload an image to LinkedIn using the new REST API and get the image URN.
    Returns the image URN if successful, or None if failed.
    """
    try:
        # Step 1: Register the image upload
        register_url = "https://api.linkedin.com/rest/images?action=initializeUpload"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202505"
        }
        register_data = {
            "initializeUploadRequest": {
                "owner": user_urn
            }
        }
        register_response = requests.post(register_url, headers=headers, json=register_data)
        if register_response.status_code != 200:
            print(f"Failed to register image upload: {register_response.status_code} - {register_response.text}")
            return None
        register_result = register_response.json()
        upload_url = register_result["value"]["uploadUrl"]
        image_urn = register_result["value"]["image"]

        # Step 2: Upload the image file (PUT, binary)
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"  # Default fallback
        with open(image_path, 'rb') as image_file:
            upload_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": mime_type
            }
            upload_response = requests.put(upload_url, headers=upload_headers, data=image_file)
            if upload_response.status_code not in [200, 201, 202]:
                print(f"Failed to upload image: {upload_response.status_code} - {upload_response.text}")
                return None
        print(f"✅ Image uploaded successfully. Image URN: {image_urn}")
        return image_urn
    except Exception as e:
        print(f"Error uploading image to LinkedIn: {str(e)}")
        return None

def post_to_linkedin_rest_api(post_text: str, generated_image: GeneratedImage = None) -> dict:
    """
    Post to LinkedIn using REST API with user URN from /userinfo endpoint.
    Only post if image upload succeeds (if image is provided).
    """
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not access_token:
        return {
            "id": "no_token",
            "url": None,
            "response": {"status": "error", "message": "No access token"},
            "note": "No LinkedIn access token available"
        }
    try:
        # Get user URN from /userinfo endpoint
        user_urn = get_user_urn_from_userinfo(access_token)
        if user_urn.startswith("userinfo_error"):
            return {
                "id": "userinfo_error",
                "url": None,
                "response": {"status": "error", "message": "Failed to get user URN"},
                "note": "Could not retrieve user URN from /userinfo endpoint"
            }
        # If we have an image, upload it and only proceed if successful
        image_urn = None
        if generated_image and os.path.exists(generated_image.image_path):
            print(f"Uploading image: {generated_image.image_path}")
            image_urn = upload_image_to_linkedin(access_token, generated_image.image_path, user_urn)
            if not image_urn:
                print("❌ Image upload failed, aborting post.")
                return {
                    "id": "image_upload_failed",
                    "url": None,
                    "response": {"status": "error", "message": "Image upload failed, post not created."},
                    "note": "Image upload failed, post not created."
                }
        # Compose the post data for /rest/posts endpoint
        api_url = "https://api.linkedin.com/rest/posts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202505"
        }
        post_data = {
            "author": user_urn,
            "commentary": post_text,
            "lifecycleState": "PUBLISHED",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            }
        }
        if image_urn:
            post_data["content"] = {
                "media": {"id": image_urn}
            }
        print("\n--- DEBUG: Payload to be sent to LinkedIn ---")
        print(json.dumps(post_data, indent=4))
        print("--- END DEBUG PAYLOAD ---\n")
        response = requests.post(api_url, headers=headers, json=post_data)
        if response.status_code in [200, 201]:
            response_data = response.json()
            post_id = response_data.get("id")
            post_url = f"https://www.linkedin.com/feed/update/{post_id}/" if post_id else None
            return {
                "id": post_id,
                "url": post_url,
                "response": response_data,
                "note": "Successfully posted to LinkedIn with image" if image_urn else "Successfully posted to LinkedIn (text-only)"
            }
        else:
            # Try to get JSON error, otherwise use raw text
            try:
                error_json = response.json()
            except Exception:
                error_json = None
            return {
                "id": "api_error",
                "url": None,
                "response": {
                    "status": "error",
                    "status_code": response.status_code,
                    "message": response.text,
                    "json": error_json
                },
                "note": f"LinkedIn API returned status {response.status_code}"
            }
    except Exception as e:
        print(f"Error in LinkedIn REST API posting: {str(e)}")
        return {
            "id": "exception",
            "url": None,
            "response": {"status": "error", "message": str(e)},
            "note": "Exception occurred during API call"
        }