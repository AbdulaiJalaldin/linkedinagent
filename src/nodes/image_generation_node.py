"""
Image Generation node for LinkedIn Content Automation Agent
Uses KIE AI 4o Image API to generate relevant images for LinkedIn posts
"""
import os
import requests
import time
import uuid
from typing import Dict, Any
from PIL import Image
from datetime import datetime
from src.state import State, GeneratedImage


def image_generation_node(state: State) -> Dict[str, Any]:
    """
    Image Generation node that creates relevant images for LinkedIn posts using KIE AI.
    
    Args:
        state: Current workflow state with LinkedIn post
        
    Returns:
        Updated state with generated image
    """
    # Get LinkedIn post
    linkedin_post = state.get("linkedin_post")
    selected_idea = state.get("selected_idea")
    topic = state.get("topic", "")
    
    if not linkedin_post:
        return {
            "workflow_status": "failed",
            "error_message": "No LinkedIn post available for image generation",
            "messages": [
                {
                    "role": "system",
                    "content": "No LinkedIn post available for image generation"
                }
            ]
        }
    
    try:
        # Update status to in progress
        state["workflow_status"] = "imaging"
        
        # Generate image prompt from post content
        image_prompt = generate_image_prompt(linkedin_post, selected_idea, topic)
        
        # Generate image using KIE AI 4o Image API
        generated_image = generate_image_with_kie_ai(image_prompt)
        
        # Update state
        return {
            "generated_image": generated_image,
            "image_status": "completed",
            "workflow_status": "imaging_completed",
            "messages": [
                {
                    "role": "system",
                    "content": f"Successfully generated image: {generated_image.image_description}"
                }
            ]
        }
        
    except Exception as e:
        error_msg = f"Error during image generation: {str(e)}"
        return {
            "generated_image": None,
            "image_status": "failed",
            "workflow_status": "failed",
            "error_message": error_msg,
            "messages": [
                {
                    "role": "system",
                    "content": f"Image generation failed: {error_msg}"
                }
            ]
        }


def generate_image_prompt(linkedin_post, selected_idea, topic: str) -> str:
    """
    Generate an image prompt from LinkedIn post content.
    
    Args:
        linkedin_post: LinkedInPost object
        selected_idea: Selected ContentIdea object
        topic: Original topic
        
    Returns:
        Formatted image prompt for KIE AI 4o Image API
    """
    # Extract key elements for image generation
    title = linkedin_post.title
    content = linkedin_post.content
    hashtags = linkedin_post.hashtags
    
    # Create a professional, business-focused image prompt
    base_prompt = f"Professional business illustration, {topic}, modern design, clean composition, corporate style, high quality, detailed, professional color palette"
    
    # Add specific elements based on content and topic
    if any(word in topic.lower() for word in ["technology", "ai", "digital", "software", "tech"]):
        base_prompt += ", technology elements, digital transformation, innovation, futuristic design"
    elif any(word in topic.lower() for word in ["business", "strategy", "management", "leadership"]):
        base_prompt += ", business growth, strategy, success, professional environment, corporate setting"
    elif any(word in topic.lower() for word in ["marketing", "social media", "branding"]):
        base_prompt += ", marketing, social media, engagement, growth, brand elements"
    elif any(word in topic.lower() for word in ["finance", "investment", "money"]):
        base_prompt += ", financial growth, investment, success, professional finance"
    else:
        base_prompt += ", professional development, success, growth, modern business"
    
    # Add LinkedIn-specific styling
    base_prompt += ", minimalist design, modern typography, professional layout, suitable for LinkedIn, business presentation style, clean background"
    
    # Add quality modifiers
    base_prompt += ", high resolution, professional photography style, corporate aesthetic, business professional"
    
    return base_prompt


def generate_image_with_kie_ai(prompt: str) -> GeneratedImage:
    """
    Generate image using KIE AI 4o Image API.
    
    Args:
        prompt: Image generation prompt
        
    Returns:
        GeneratedImage object with image details
    """
    # Get KIE AI API key from environment
    kie_api_key = os.getenv("KIE_API_KEY")
    if not kie_api_key:
        raise ValueError("KIE_API_KEY environment variable not set")
    
    # KIE AI API endpoint
    api_url = "https://kieai.erweima.ai/api/v1/gpt4o-image/generate"
    
    # Prepare request headers
    headers = {
        "Authorization": f"Bearer {kie_api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare request payload
    payload = {
        "prompt": prompt,
        "aspect_ratio": "1:1",  # Square format for LinkedIn
        "reference_images": [],  # No reference images for now
        "callback_url": None  # No callback for simplicity
    }
    
    try:
        # Make API request to generate image
        print(f"Generating image with prompt: {prompt[:100]}...")
        print(f"Payload being sent: {payload}")  # Log payload for debugging
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"KIE AI API error response: {response.text}")  # Log full error response
            raise Exception(f"KIE AI API error: {response.status_code} - {response.text}")
        
        # Parse response
        result = response.json()
        print(f"Initial KIE AI response: {result}")  # Log the initial response
        
        task_id = result.get("data", {}).get("taskId")
        if not task_id:
            print(f"No task ID in response: {result}")  # Log missing task ID
            raise Exception("No task ID received from KIE AI API")
        
        # 1. Poll the status endpoint to get the original image URL when ready
        status_url = f"https://kieai.erweima.ai/api/v1/gpt4o-image/record-info?taskId={task_id}"
        max_wait_time = 120  # seconds
        poll_interval = 5    # seconds
        start_time = time.time()
        original_image_url = None
        while time.time() - start_time < max_wait_time:
            status_response = requests.get(status_url, headers=headers, timeout=30)
            if status_response.status_code != 200:
                print(f"Status check failed: {status_response.status_code}")
                raise Exception(f"Status check failed: {status_response.status_code}")
            status_result = status_response.json()
            print(f"Status check response: {status_result}")
            if status_result.get("code") != 200:
                print(f"Status check error, full response: {status_result}")
                raise Exception(f"Status check error: {status_result.get('msg', 'Unknown error')}")
            data = status_result.get("data", {})
            status = data.get("status")
            # Wait for status == 'SUCCESS' and extract image URL from resultUrls
            if status == "SUCCESS" and data.get("response") and data["response"].get("resultUrls"):
                original_image_url = data["response"]["resultUrls"][0]
                break
            elif status == "FAILED":
                raise Exception(f"Image generation failed: {data.get('errorMessage', 'Unknown error')}")
            else:
                print(f"Image not ready yet (status: {status}), waiting {poll_interval} seconds...")
                time.sleep(poll_interval)
        if not original_image_url:
            raise Exception("Image generation timed out or imageUrl not found.")
        
        # 2. Call the /download-url endpoint to get the direct download URL
        download_url_api = "https://api.kie.ai/api/v1/gpt4o-image/download-url"
        download_url_headers = {
            "Authorization": f"Bearer {kie_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        download_url_payload = {"taskId": task_id, "url": original_image_url}
        download_url_response = requests.post(download_url_api, headers=download_url_headers, json=download_url_payload, timeout=30)
        if download_url_response.status_code != 200:
            print(f"Download URL API error: {download_url_response.text}")
            raise Exception(f"Download URL API error: {download_url_response.status_code} - {download_url_response.text}")
        download_url_result = download_url_response.json()
        print(f"Download URL API response: {download_url_result}")
        if download_url_result.get("code") != 200:
            raise Exception(f"Download URL API error: {download_url_result.get('msg', 'Unknown error')}")
        direct_download_url = download_url_result.get("data")
        if not direct_download_url:
            raise Exception("No direct download URL returned from API")
        
        # 3. Download the image from the direct download URL
        print(f"Downloading image from: {direct_download_url}")
        image_path = download_and_save_image(direct_download_url, task_id)
        
        generated_image = GeneratedImage(
            image_path=image_path,
            image_description=f"Professional business image for LinkedIn post: {prompt[:100]}...",
            prompt_used=prompt
        )
        
        return generated_image
        
    except requests.exceptions.RequestException as e:
        print(f"Network error during image generation: {str(e)}")
        raise Exception(f"Network error during image generation: {str(e)}")
    except Exception as e:
        print(f"Image generation failed with exception: {str(e)}")
        raise Exception(f"Image generation failed: {str(e)}")


def wait_for_image_completion(task_id: str, api_key: str, prompt: str, max_wait_time: int = 300) -> GeneratedImage:
    """
    Wait for image generation to complete and retrieve the result.
    """
    api_url = "https://kieai.erweima.ai/api/v1/gpt4o-image/record-info"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            # Check task status
            response = requests.post(api_url, headers=headers, json={"taskId": task_id}, timeout=30)
            print(f"Status check response: {response.text}")  # Log full response
            
            if response.status_code != 200:
                print(f"Status check failed: {response.status_code}")
                raise Exception(f"Status check failed: {response.status_code}")
            
            result = response.json()
            
            if result.get("code") != 0:
                print(f"Status check error, full response: {result}")
                raise Exception(f"Status check error: {result.get('message', 'Unknown error')}")
            
            data = result.get("data", {})
            status = data.get("status")
            print(f"Image generation status: {status}")
            
            if status == "completed":
                # Image generation completed successfully
                image_url = data.get("imageUrl")
                if not image_url:
                    print(f"No image URL in completed response: {data}")
                    raise Exception("No image URL in completed response")
                
                # Download and save the image
                image_path = download_and_save_image(image_url, task_id)
                
                # Create GeneratedImage object
                generated_image = GeneratedImage(
                    image_path=image_path,
                    image_description=f"Professional business image for LinkedIn post: {prompt[:100]}...",
                    prompt_used=prompt
                )
                
                return generated_image
                
            elif status in ["failed", "error"]:
                error_msg = data.get("errorMessage", "Unknown error")
                print(f"Image generation failed status, full data: {data}")
                raise Exception(f"Image generation failed: {error_msg}")
            
            # Wait before checking again
            time.sleep(10)
            
        except requests.exceptions.RequestException as e:
            print(f"Network error during status check: {e}")
            time.sleep(10)
            continue
    
    print(f"Image generation timed out after {max_wait_time} seconds")
    raise Exception(f"Image generation timed out after {max_wait_time} seconds")


def download_and_save_image(image_url: str, task_id: str) -> str:
    """
    Download image from KIE AI and save it locally.
    
    Args:
        image_url: URL of the generated image
        task_id: Task ID for filename
        
    Returns:
        Path to saved image file
    """
    try:
        # Create images directory if it doesn't exist
        images_dir = "generated_images"
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_image_{task_id}_{timestamp}.png"
        filepath = os.path.join(images_dir, filename)
        
        # Download image
        print(f"Downloading image from: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Save image
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        print(f"Image saved to: {filepath}")
        return filepath
        
    except Exception as e:
        raise Exception(f"Failed to download and save image: {str(e)}")


def create_fallback_image(prompt: str) -> GeneratedImage:
    """
    Create a fallback image when KIE AI generation fails.
    
    Args:
        prompt: Original prompt used
        
    Returns:
        GeneratedImage object with fallback information
    """
    # Create a placeholder image or return error information
    fallback_path = "generated_images/fallback_image.png"
    
    # Create a simple placeholder image if needed
    try:
        os.makedirs("generated_images", exist_ok=True)
        # Create a simple colored rectangle as placeholder
        img = Image.new('RGB', (800, 800), color='#f0f0f0')
        img.save(fallback_path)
    except Exception:
        fallback_path = "No image generated"
    
    return GeneratedImage(
        image_path=fallback_path,
        image_description="Fallback image - KIE AI generation failed",
        prompt_used=prompt
    ) 
