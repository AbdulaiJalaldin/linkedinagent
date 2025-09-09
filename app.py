from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_bolt import App as SlackApp
from slack_sdk import WebClient
from src.graph import run_linkedin_agent, run_linkedin_agent_interactive
from src.slack_product_promotion import run_product_promotion_slack, create_uploaded_image_from_slack, get_pdf_for_slack, cleanup_temp_files
from src.slack_enhanced_functions import handle_product_promotion_image_upload, show_enhanced_final_result
from src.interactive_product_collection import start_product_info_collection, process_product_info_answer
import os
import requests
import logging
import json
import time
from typing import Optional
from fastapi.responses import JSONResponse


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Environment variables for Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SIGNING_SECRET")
print(SLACK_BOT_TOKEN)
print(SLACK_SIGNING_SECRET)

# Initialize Slack Bolt app
slack_app = SlackApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# FastAPI setup
app = FastAPI(title="LinkedIn Agent API", version="1.0.0")
handler = SlackRequestHandler(slack_app)

# Session management for interactive conversations
user_sessions = {}  # Store user session state

@app.get("/")
async def root():
    """Root endpoint to check if the API is running"""
    return {"message": "LinkedIn Agent API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "linkedin-agent"}

@app.get("/slack/events")
async def slack_events_get():
    return JSONResponse({"message": "This endpoint accepts POST requests from Slack."})

@app.post("/slack/events")
async def endpoint(req: Request):
    """Handle all Slack events"""
    return await handler.handle(req)

@slack_app.event("app_mention")
def handle_mention(event, say):
    """Handle when the bot is mentioned in a channel"""
    try:
        user_message = event["text"]
        user_id = event["user"]
        channel = event["channel"]
        
        # Remove the bot mention from the message
        # The message format is usually "<@BOT_ID> your message here"
        bot_mention = f"<@{slack_app.client.auth_test()['user_id']}>"
        clean_message = user_message.replace(bot_mention, "").strip()
        
        logger.info(f"Bot mentioned by {user_id} in {channel}: {clean_message}")
        
        if not clean_message:
            show_start_message(say)
            return
        
        # Process the message
        if clean_message.lower() == "start":
            show_start_message(say)
        elif clean_message.lower() == "help":
            show_help(say)
        elif clean_message.lower().startswith("create post about"):
            topic = clean_message.replace("create post about", "").strip()
            if topic:
                process_linkedin_request(say, topic, user_id, channel)
            else:
                say("Please provide a topic. Example: `create post about AI trends`")
        elif clean_message.lower().startswith("interactive"):
            topic = clean_message.replace("interactive", "").strip()
            if topic:
                start_interactive_session(say, topic, user_id, channel)
            else:
                say("Please provide a topic for interactive mode. Example: `interactive AI trends`")
        else:
            # Treat as a general topic
            process_linkedin_request(say, clean_message, user_id, channel)
            
    except Exception as e:
        logger.error(f"Error handling mention: {str(e)}")
        say("Sorry, I encountered an error processing your request. Please try again.")

@slack_app.event("message")
def handle_message(event, say):
    """Handle regular messages (including DMs and file uploads)"""
    try:
        user_message = event.get("text", "").strip()
        user_id = event.get("user", "")
        channel = event.get("channel", "")
        channel_type = event.get("channel_type", "")
        
        logger.info(f"Message from {user_id} in {channel} ({channel_type}): {user_message}")
        
        # Handle file uploads
        if "files" in event:
            for file_desc in event["files"]:
                if file_desc["filetype"].startswith("image"):
                    # Download the image
                    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
                    image_url = file_desc["url_private"]
                    image_response = requests.get(image_url, headers=headers)
                    
                    if image_response.status_code == 200:
                        image_bytes = image_response.content
                        file_name = file_desc["name"]
                        
                        # Check if user is in product promotion image upload phase
                        if user_id in user_sessions:
                            session = user_sessions[user_id]
                            if session.get("type") == "image_upload" and session.get("mode") == "product_promotion":
                                # Handle image upload for product promotion
                                handle_product_promotion_image_upload(say, session, image_bytes, file_name, user_id, channel)
                            else:
                                # Process the image with the regular agent
                                process_image_with_agent(say, image_bytes, user_id, channel)
                        else:
                            # Process the image with the regular agent
                            process_image_with_agent(say, image_bytes, user_id, channel)
                    else:
                        say("Sorry, I couldn't download the image. Please try again.")
            return
        
        # Handle text messages (including DMs)
        if user_message:
             user_message_lower = user_message.lower()
             
             # Check if user is in an active session
             if user_id in user_sessions:
                 handle_session_message(say, user_message, user_id, channel)
                 return
             
             # Handle help command
             if user_message_lower == "help":
                 show_help(say)
                 return
             
             # Handle start command
             elif user_message_lower == "start":
                 show_start_message(say)
                 return
             
             # Handle LinkedIn content creation commands
             elif user_message_lower.startswith("create post about"):
                 topic = user_message.replace("create post about", "").strip()
                 if topic:
                     process_linkedin_request(say, topic, user_id, channel)
                 else:
                     say("Please provide a topic. Example: `create post about AI trends`")
                 return
             
             elif user_message_lower.startswith("interactive"):
                 topic = user_message.replace("interactive", "").strip()
                 if topic:
                     start_interactive_session(say, topic, user_id, channel)
                 else:
                     say("Please provide a topic for interactive mode. Example: `interactive AI trends`")
                 return
             
             # If it's a DM and not a recognized command, check if it's a choice (1 or 2)
             elif channel_type == "im":
                 if user_message.strip() in ["1", "2"]:
                     # Start interactive session
                     user_sessions[user_id] = {
                         "type": "choice_selection",
                         "mode": None
                     }
                     handle_session_message(say, user_message, user_id, channel)
                 else:
                     # Treat as a general topic
                     process_linkedin_request(say, user_message, user_id, channel)
                 return
             
             # For channel messages that aren't mentions, ignore them
             else:
                 # Only respond if it's a DM
                 if channel_type == "im":
                     say("I didn't understand that command. Type `help` to see available commands or `start` to begin.")
        
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        say("Sorry, I encountered an error processing your request. Please try again.")

@slack_app.event("file_shared")
def handle_file_shared(event, say):
    """Handle file shared events (when users upload files) using Slack SDK"""
    try:
        # Extract file ID from event
        file_id = event.get("file", {}).get("id")
        if not file_id:
            logger.error("No file ID found in file_shared event")
            say("Sorry, I couldn't identify the uploaded file. Please try again.")
            return
        
        user_id = event.get("user_id", "")
        channel = event.get("channel_id", "")
        
        logger.info(f"File shared by {user_id} in {channel}, file ID: {file_id}")
        
        # Fetch complete file information using Slack SDK
        try:
            file_info_response = slack_client.files_info(file=file_id)
            if not file_info_response["ok"]:
                logger.error(f"Failed to get file info: {file_info_response}")
                say("Sorry, I couldn't retrieve the file information. Please try again.")
                return
            
            file_info = file_info_response["file"]
            logger.info(f"Retrieved file info: {file_info}")
            
        except Exception as e:
            logger.error(f"Error fetching file info: {str(e)}")
            say("Sorry, I couldn't retrieve the file information. Please try again.")
            return
        
        # Check if it's an image file
        mimetype = file_info.get("mimetype", "").lower()
        filetype = file_info.get("filetype", "").lower()
        name = file_info.get("name", "").lower()
        
        logger.info(f"Checking file: mimetype='{mimetype}', filetype='{filetype}', name='{name}'")
        
        # Check if it's an image file using multiple criteria
        is_image = (
            mimetype.startswith("image/") or
            filetype in ["jpg", "jpeg", "png", "gif", "webp"] or
            any(name.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"])
        )
        
        logger.info(f"Is image: {is_image}")
        
        if is_image:
            # Download the image using the private URL
            try:
                image_url = file_info["url_private"]
                image_response = requests.get(image_url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"})
                
                if image_response.status_code == 200:
                    image_bytes = image_response.content
                    file_name = file_info["name"]
                    
                    # Check if user is in product promotion image upload phase
                    if user_id in user_sessions:
                        session = user_sessions[user_id]
                        if session.get("type") == "image_upload" and session.get("mode") == "product_promotion":
                            # Handle image upload for product promotion
                            handle_product_promotion_image_upload(say, session, image_bytes, file_name, user_id, channel)
                        else:
                            # Process the image with the regular agent
                            process_image_with_agent(say, image_bytes, user_id, channel)
                    else:
                        # Process the image with the regular agent
                        process_image_with_agent(say, image_bytes, user_id, channel)
                else:
                    logger.error(f"Failed to download image: {image_response.status_code}")
                    say("Sorry, I couldn't download the image. Please try again.")
            except Exception as e:
                logger.error(f"Error downloading image: {str(e)}")
                say("Sorry, I couldn't download the image. Please try again.")
        else:
            say("I can only process image files. Please upload a JPG, PNG, or GIF file.")
            logger.info(f"File rejected: mimetype='{mimetype}', filetype='{filetype}', name='{name}'")
            
    except Exception as e:
        logger.error(f"Error handling file shared: {str(e)}")
        say("Sorry, I encountered an error processing your file upload. Please try again.")

def show_start_message(say):
    """Show the start menu with content creation options"""
    start_text = """
============================================================
🎯 LINKEDIN CONTENT AUTOMATION AGENT
============================================================
Choose your content creation mode:

1. 📝 Write about a topic
   - Scrape YouTube videos for inspiration
   - Generate unique content ideas
   - Create engaging LinkedIn posts
   - Generate matching images
   - Post directly to LinkedIn

2. 🚀 Promote a work/product
   - Create promotional content for your work
   - Upload promotional images
   - Generate professional LinkedIn posts
   - Save to PDF with images
   - Auto-post to LinkedIn
============================================================

*Reply with 1 or 2 to start the interactive process*

*Quick Commands:*
• Type any topic to start content creation (e.g., "AI trends")
• `create post about [topic]` - Direct content creation
• `interactive [topic]` - Interactive mode with idea selection
• `help` - Show all commands
• `start` - Show this menu again

*Ready to create amazing LinkedIn content!* 🚀
    """
    say(start_text)

def show_help(say):
    """Show help information"""
    help_text = """
🤖 *LinkedIn Agent Commands*

*Basic Commands:*
• `start` - Show the main menu
• `create post about [topic]` - Create LinkedIn content about a topic
• `interactive [topic]` - Start interactive content creation with idea selection
• `help` - Show this help message

*Examples:*
• `create post about AI trends in 2024`
• `interactive digital marketing strategies`
• `create post about remote work productivity`

*Features:*
• Content generation with multiple ideas
• Image generation for posts
• Automatic LinkedIn posting (if configured)
• PDF report generation

*Quick Start:*
Just type any topic to begin content creation!
    """
    say(help_text)

def handle_session_message(say, message: str, user_id: str, channel: str):
    """Handle messages during an active session"""
    session = user_sessions[user_id]
    session_type = session.get("type")
    
    try:
        if session_type == "choice_selection":
            # User is choosing between option 1 or 2
            if message.strip() == "1":
                session["type"] = "topic_input"
                session["mode"] = "content_creation"
                say("📝 *Content Creation Mode Selected*\n\nPlease enter your topic for content creation:")
            elif message.strip() == "2":
                session["type"] = "product_info_collection"
                session["mode"] = "product_promotion"
                session["channel"] = channel  # Store channel for image uploads
                # Start interactive product information collection
                response = start_product_info_collection(session)
                say(response)
            else:
                say("Please reply with 1 or 2 to select your content creation mode.")
        
        elif session_type == "topic_input":
            # User is providing a topic for content creation
            topic = message.strip()
            if topic:
                session["topic"] = topic
                session["type"] = "processing"
                session["channel"] = channel  # Store channel for image uploads
                say(f"🎯 *Topic received: {topic}*\n\n⏳ Starting content creation process...\n\nThis will:\n1. Scrape YouTube videos for inspiration\n2. Generate content ideas\n3. Create engaging LinkedIn posts\n4. Generate matching images\n\nPlease wait...")
                
                # Start the content creation process
                process_content_creation_session(say, session, user_id, channel)
            else:
                say("Please provide a valid topic for content creation.")
        
        elif session_type == "product_info_collection":
            # User is answering product information questions
            answer = message.strip()
            if answer:
                response = process_product_info_answer(session, answer)
                say(response)
            else:
                say("Please provide an answer to continue.")
        
        elif session_type == "product_info":
            # User is providing product information (legacy format)
            product_info = message.strip()
            if product_info:
                session["product_info"] = product_info
                session["type"] = "image_upload"
                session["uploaded_images"] = []
                say(f"📋 *Product information received*\n\n🖼️ *Image Upload Phase*\n\nYou can now upload promotional images for your product. Supported formats: JPG, PNG, GIF\n\nUpload images now, or type 'skip' to continue without images.")
            else:
                say("Please provide product information.")
        
        elif session_type == "idea_selection":
            # User is selecting from generated ideas
            try:
                choice = int(message.strip())
                ideas = session.get("ideas", [])
                if 1 <= choice <= len(ideas):
                    selected_idea = ideas[choice - 1]
                    session["selected_idea"] = selected_idea
                    session["type"] = "processing"
                    say(f"✅ *Idea selected: {selected_idea.title}*\n\n⏳ Generating content based on your selection...")
                    # Continue with content generation
                    # Run the content writer and image generation nodes directly
                    from src.nodes.content_writer_node import content_writer_node
                    from src.nodes.image_generation_node import image_generation_node
                    content_state = {
                        "topic": session.get("topic"),
                        "scraped_content": session["agent_result"].get("scraped_content", []),
                        "selected_idea": selected_idea,
                        "workflow_status": "idea_selected"
                    }
                    content_result = content_writer_node(content_state)
                    image_state = {
                        "topic": session.get("topic"),
                        "linkedin_post": content_result.get("linkedin_post"),
                        "selected_idea": selected_idea,
                        "workflow_status": "writing_completed"
                    }
                    image_result = image_generation_node(image_state)
                    # Merge results
                    final_result = {**session["agent_result"], **content_result, **image_result}
                    show_content_for_approval(say, final_result, session, user_id)
                else:
                    say(f"Please select a number between 1 and {len(ideas)}")
            except ValueError:
                say("Please enter a valid number for your selection.")
        
        elif session_type == "content_approval":
            # User is approving content for posting
            if message.strip().lower() in ["yes", "y", "approve", "post"]:
                session["user_approval"] = True
                session["type"] = "processing"
                say("✅ *Content approved!* Posting to LinkedIn...")
                
                # Continue with LinkedIn posting
                continue_content_creation(say, session, user_id, channel)
            elif message.strip().lower() in ["no", "n", "reject", "skip"]:
                session["user_approval"] = False
                session["type"] = "completed"
                say("❌ *Content rejected.* Content generation completed without posting to LinkedIn.\n\nType `start` to begin a new session.")
                clear_user_session(user_id)
            else:
                say("Please respond with 'yes' to approve and post, or 'no' to reject without posting.")
        
        elif session_type == "image_upload":
            # User is in image upload phase for product promotion
            if message.strip().lower() == "skip":
                session["type"] = "processing"
                say(f"⏳ Starting product promotion process \n\nThis will:\n1. Analyze your product information\n2. Create promotional content\n3. Generate professional LinkedIn posts\nPlease wait...")
                
                # Start the product promotion process
                process_product_promotion_session(say, session, user_id, channel)
            elif message.strip().lower() in ["continue", "done", "finish", "proceed"]:
                # User wants to continue with uploaded images
                session["type"] = "processing"
                say(f"⏳ Starting product promotion process with uploaded images...\n\nThis will:\n1. Analyze your product information\n2. Create promotional content with your images\n3. Generate professional LinkedIn posts\n4. Save to PDF\n\nPlease wait...")
                
                # Start the product promotion process
                process_product_promotion_session(say, session, user_id, channel)
            else:
                say("Please upload more images, type 'skip' to continue without images, or type 'continue' to proceed with uploaded images.")
        
        elif session_type == "processing":
            say("⏳ Still processing your request. Please wait...")
        
    except Exception as e:
        logger.error(f"Error in session handling: {str(e)}")
        say("❌ An error occurred. Please try again or type `start` to restart.")
        clear_user_session(user_id)

def clear_user_session(user_id: str):
    """Clear a user's session"""
    if user_id in user_sessions:
        del user_sessions[user_id]

def upload_generated_image_to_slack(say, generated_image, channel=None):
    """Upload generated image to Slack and display it"""
    try:
        if not generated_image or not os.path.exists(generated_image.image_path):
            return
        
        # Read the image file
        with open(generated_image.image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        # Get file extension
        file_extension = os.path.splitext(generated_image.image_path)[1].lower()
        if file_extension == '.png':
            file_type = 'image/png'
        elif file_extension in ['.jpg', '.jpeg']:
            file_type = 'image/jpeg'
        else:
            file_type = 'image/png'  # Default fallback
        
        # Create a temporary filename for Slack
        filename = f"linkedin_content_{int(time.time())}{file_extension}"
        
        # Upload to Slack using the WebClient
        try:
            # Use the provided channel or try to find one from sessions
            upload_channel = channel
            if not upload_channel:
                # Try to get channel from any active session
                for user_id, user_session in user_sessions.items():
                    if "channel" in user_session:
                        upload_channel = user_session["channel"]
                        break
                if not upload_channel:
                    upload_channel = "general"  # Fallback
            
            logger.info(f"Uploading image to Slack channel: {upload_channel}")
            
            response = slack_client.files_upload_v2(
                channel=upload_channel,
                file=image_data,
                filename=filename,
                title=f"Generated LinkedIn Content Image",
                initial_comment="🖼️ *Generated Image for LinkedIn Post*"
            )
            
            if response["ok"]:
                logger.info(f"Successfully uploaded generated image to Slack: {filename}")
                say("🖼️ *Generated image uploaded to Slack!*")
            else:
                logger.error(f"Failed to upload image to Slack: {response}")
                say(f"🖼️ *Generated Image:* {generated_image.image_path}")
                
        except Exception as e:
            logger.error(f"Error uploading image to Slack: {str(e)}")
            say(f"🖼️ *Generated Image:* {generated_image.image_path}")
            
    except Exception as e:
        logger.error(f"Error in upload_generated_image_to_slack: {str(e)}")
        say(f"🖼️ *Generated Image:* {generated_image.image_path}")

def show_content_for_approval(say, result: dict, session: dict, user_id: str):
    """Show generated content for user approval"""
    try:
        linkedin_post = result.get("linkedin_post")
        generated_image = result.get("generated_image")
        pdf_path = result.get("pdf_path")
        product_data = result.get("product_data")
        
        # Build approval message
        approval_parts = []
        approval_parts.append("📝 *Generated Content for Approval:*\n")
        
        if product_data:
            approval_parts.append(f"🎯 *Product:* {product_data.name}\n")
        
        if linkedin_post:
            approval_parts.append(f"*Title:* {linkedin_post.title}\n")
            approval_parts.append(f"*Content:*\n{linkedin_post.content}\n")
        
        if pdf_path:
            approval_parts.append(f"📄 *PDF Generated:* {pdf_path}\n")
        
        # Send the text content first
        say("\n".join(approval_parts))
        
        # Upload and display the generated image if it exists
        if generated_image and os.path.exists(generated_image.image_path):
            try:
                # Get the channel from the session
                current_channel = session.get("channel", "general")
                upload_generated_image_to_slack(say, generated_image, current_channel)
            except Exception as e:
                logger.error(f"Error uploading generated image: {str(e)}")
                say(f"🖼️ *Generated Image:* {generated_image.image_path}\n")
        elif generated_image:
            say(f"🖼️ *Generated Image:* {generated_image.image_path}\n")
        
        # Send approval question
        say("\n*Do you want to approve and post this content to LinkedIn?*\nReply with 'yes' to approve and post, or 'no' to reject without posting.")
        
        # Set session to approval mode
        session["type"] = "content_approval"
        session["agent_result"] = result
        
    except Exception as e:
        logger.error(f"Error showing content for approval: {str(e)}")
        say(f"❌ *Error:* {str(e)}")
        clear_user_session(user_id)

def process_content_creation_session(say, session: dict, user_id: str, channel: str):
    """Process content creation session with approval"""
    try:
        topic = session.get("topic")
        user_choice = session.get("user_choice")
        
        # Run the LinkedIn agent for content creation
        result = run_linkedin_agent(topic)
        
        if result.get("workflow_status") == "awaiting_choice":
            # Send ideas to user and set session for idea selection
            ideas = result.get("content_ideas", [])
            session["ideas"] = ideas
            session["type"] = "idea_selection"
            session["agent_result"] = result
            ideas_text = "*Generated Content Ideas:*\n\n"
            for i, idea in enumerate(ideas, 1):
                ideas_text += f"{i}. {idea.title}\n{idea.description}\n\n"
            ideas_text += "Please select an idea (1, 2, etc.):"
            say(ideas_text)
            return
        
        if result.get("workflow_status") == "completed":
            # Check if we need to show ideas for selection
            ideas = result.get("content_ideas", [])
            if ideas and len(ideas) > 1 and not user_choice:
                session["ideas"] = ideas
                session["type"] = "idea_selection"
                session["agent_result"] = result
                
                # Show ideas for selection
                ideas_text = "*Generated Content Ideas:*\n\n"
                for i, idea in enumerate(ideas, 1):
                    ideas_text += f"{i}. {idea.title}\n{idea.description}\n\n"
                ideas_text += "Please select an idea (1, 2, etc.):"
                say(ideas_text)
            else:
                # Show content for approval
                show_content_for_approval(say, result, session, user_id)
        else:
            error_msg = result.get("error_message", "Unknown error occurred")
            say(f"❌ *Error creating content:* {error_msg}")
            clear_user_session(user_id)
            
    except Exception as e:
        logger.error(f"Error in content creation session: {str(e)}")
        say(f"❌ *Error:* {str(e)}")
        clear_user_session(user_id)

def handle_product_promotion_image_upload(say, session: dict, image_bytes: bytes, file_name: str, user_id: str, channel: str):
    """Handle image upload during product promotion workflow"""
    try:
        # Create UploadedImage object from Slack upload
        uploaded_image = create_uploaded_image_from_slack(image_bytes, file_name)
        
        # Add to session's uploaded images
        if "uploaded_images" not in session:
            session["uploaded_images"] = []
        session["uploaded_images"].append(uploaded_image)
        
        say(f"✅ *Image uploaded successfully:* {file_name}\n\nYou can upload more images, type 'continue' to proceed with uploaded images, or type 'skip' to continue without images.")
        
    except Exception as e:
        logger.error(f"Error handling product promotion image upload: {str(e)}")
        say(f"❌ *Error uploading image:* {str(e)}")

def process_product_promotion_session(say, session: dict, user_id: str, channel: str):
    """Process product promotion session"""
    try:
        # Check if we have collected product data from interactive collection
        product_data = session.get("product_data")
        uploaded_images = session.get("uploaded_images", [])
        logger.info(f"[DEBUG] product_data type: {type(product_data)}, value: {product_data}")
        logger.info(f"[DEBUG] uploaded_images: {uploaded_images}")
        
        if product_data:
            # Use the collected product data
            logger.info(f"Processing product promotion with collected data: {product_data.name}")
            logger.info(f"Uploaded images: {len(uploaded_images)}")
            
            # Create initial state with the collected product data
            from src.state import State
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
            from src.product_promotion_graph import create_product_promotion_graph
            graph = create_product_promotion_graph()
            result = graph.invoke(initial_state)
            
        else:
            # Fallback to legacy method with product_info string
            product_info = session.get("product_info")
            logger.info(f"Processing product promotion with info: {product_info[:100] if product_info else 'None'}...")
            logger.info(f"Uploaded images: {len(uploaded_images)}")
            
            # Use the specialized product promotion workflow with uploaded images
            result = run_product_promotion_slack(product_info, uploaded_images)
        
        logger.info(f"Product promotion result status: {result.get('workflow_status')}")
        
        if result.get("workflow_status") == "completed":
            show_enhanced_final_result(say, result, user_id)
            # Clean up temporary files
            cleanup_temp_files(uploaded_images)
        elif result.get("promotion_status") == "awaiting_approval":
            # Show content for approval
            show_content_for_approval(say, result, session, user_id)
        else:
            error_msg = result.get("error_message", "Unknown error occurred")
            say(f"❌ *Error creating promotional content:* {error_msg}")
            clear_user_session(user_id)
            # Clean up temporary files even on error
            cleanup_temp_files(uploaded_images)
            
    except Exception as e:
        logger.error(f"Error in product promotion session: {str(e)}")
        say(f"❌ *Error:* {str(e)}")
        clear_user_session(user_id)
        # Clean up temporary files on exception
        cleanup_temp_files(session.get("uploaded_images", []))

def continue_content_creation(say, session: dict, user_id: str, channel: str):
    """Continue content creation after idea selection or approval"""
    try:
        selected_idea = session.get("selected_idea")
        agent_result = session.get("agent_result")
        user_approval = session.get("user_approval")
        session_mode = session.get("mode")  # "content_creation" or "product_promotion"
        
        logger.info(f"[DEBUG] continue_content_creation - user_approval: {user_approval}, mode: {session_mode}")
        
        if user_approval is True:
            # User approved the content, continue with LinkedIn posting
            if agent_result:
                logger.info(f"[DEBUG] Continuing workflow with agent_result: {agent_result.keys()}")
                
                # Import the LinkedIn posting node directly
                from src.nodes.linkedin_posting_node import linkedin_posting_node
                from src.state import State
                
                # Create state with the data needed for LinkedIn posting
                posting_state = State(
                    linkedin_post=agent_result.get("linkedin_post"),
                    generated_image=agent_result.get("generated_image"),
                    uploaded_images=agent_result.get("uploaded_images", []),
                    product_data=agent_result.get("product_data"),
                    user_approval=True,
                    workflow_status="promotion" if session_mode == "product_promotion" else "content_creation",
                    promotion_status="approved"
                )
                
                logger.info(f"[DEBUG] Created posting_state with keys: {posting_state.keys()}")
                
                # Call the LinkedIn posting node directly
                posting_result = linkedin_posting_node(posting_state)
                
                logger.info(f"[DEBUG] LinkedIn posting result: {posting_result}")
                
                # Check the posting result
                posting_status = posting_result.get("posting_status")
                if posting_status == "completed":
                    say("✅ *Content approved and posted to LinkedIn successfully!*\n\nType `start` to begin a new session.")
                else:
                    error_msg = posting_result.get("error_message", "Unknown posting error")
                    say(f"❌ *LinkedIn posting failed:* {error_msg}\n\nType `start` to begin a new session.")
                
                clear_user_session(user_id)
            else:
                logger.error("[DEBUG] No agent_result found for LinkedIn posting")
                say("❌ *Error:* No agent result found to continue posting.\n\nType `start` to begin a new session.")
                clear_user_session(user_id)
        else:
            # Show content for approval or final result
            if agent_result:
                show_content_for_approval(say, agent_result, session, user_id)
            else:
                show_final_result(say, agent_result, user_id)
        
    except Exception as e:
        logger.error(f"Error continuing content creation: {str(e)}")
        say(f"❌ *Error:* {str(e)}")
        clear_user_session(user_id)

def show_final_result(say, result: dict, user_id: str):
    """Show the final result and clear session"""
    try:
        # Extract relevant information
        linkedin_post = result.get("linkedin_post")
        generated_image = result.get("generated_image")
        posting_status = result.get("posting_status", "not_attempted")
        product_data = result.get("product_data")
        promotion_status = result.get("promotion_status")
        
        # Build response message
        response_parts = []
        
        # Show product information if available
        if product_data:
            response_parts.append(f"🎯 *Product Promotion for: {product_data.name}*")
        
        if linkedin_post:
            response_parts.append(f"📝 *Generated LinkedIn Post:*\n{linkedin_post.title}\n\n{linkedin_post.content}")
        
        # Send the text content first
        say("\n\n".join(response_parts))
        
        # Upload and display the generated image if it exists
        if generated_image and os.path.exists(generated_image.image_path):
            try:
                # Try to get channel from session or use a default
                current_channel = "general"  # Default fallback
                upload_generated_image_to_slack(say, generated_image, current_channel)
            except Exception as e:
                logger.error(f"Error uploading generated image: {str(e)}")
                say(f"🖼️ *Promotional Image Generated:* {generated_image.image_path}")
        elif generated_image:
            say(f"🖼️ *Promotional Image Generated:* {generated_image.image_path}")
        
        # Send status messages
        if posting_status == "success":
            say("✅ *Posted to LinkedIn successfully!*")
        elif posting_status == "failed":
            say("❌ *LinkedIn posting failed* (content generated but not posted)")
        else:
            say("📋 *Promotional content ready* (not posted to LinkedIn)")
        
        # Add session completion message
        if promotion_status == "success":
            say("\n🎉 *Product promotion completed successfully!* Type `start` to begin a new session.")
        else:
            say("\n🎉 *Session completed!* Type `start` to begin a new session.")
        
        # Clear the session
        clear_user_session(user_id)
        
    except Exception as e:
        logger.error(f"Error showing final result: {str(e)}")
        say(f"❌ *Error:* {str(e)}")
        clear_user_session(user_id)

def process_linkedin_request(say, topic: str, user_id: str, channel: str):
    """Process LinkedIn content creation request"""
    try:
        # Send initial response
        say(f"🎯 Creating LinkedIn content about: *{topic}*\n\n⏳ This may take a few moments...")
        
        # Run the LinkedIn agent
        result = run_linkedin_agent(topic)
        
        # Process the result
        if result.get("workflow_status") == "completed":
            # Extract relevant information
            linkedin_post = result.get("linkedin_post")
            generated_image = result.get("generated_image")
            posting_status = result.get("posting_status", "not_attempted")
            
            # Build response message
            response_parts = []
            
            if linkedin_post:
                response_parts.append(f"📝 *Generated Content:*\n{linkedin_post.title}\n\n{linkedin_post.content}")
            
            # Send the text content first
            say("\n\n".join(response_parts))
            
            # Upload and display the generated image if it exists
            if generated_image and os.path.exists(generated_image.image_path):
                try:
                    upload_generated_image_to_slack(say, generated_image, channel)
                except Exception as e:
                    logger.error(f"Error uploading generated image: {str(e)}")
                    say(f"🖼️ *Image Generated:* {generated_image.image_path}")
            elif generated_image:
                say(f"🖼️ *Image Generated:* {generated_image.image_path}")
            
            # Send status message
            if posting_status == "success":
                say("✅ *Posted to LinkedIn successfully!*")
            elif posting_status == "failed":
                say("❌ *LinkedIn posting failed* (content generated but not posted)")
            else:
                say("📋 *Content ready* (not posted to LinkedIn)")
            
        else:
            error_msg = result.get("error_message", "Unknown error occurred")
            say(f"❌ *Error creating content:* {error_msg}")
            
    except Exception as e:
        logger.error(f"Error processing LinkedIn request: {str(e)}")
        say(f"❌ *Error:* {str(e)}")

def start_interactive_session(say, topic: str, user_id: str, channel: str):
    """Start interactive content creation session"""
    try:
        say(f"🎯 Starting interactive session for: *{topic}*\n\n⏳ Generating content ideas...")
        
        # Run the interactive agent
        result = run_linkedin_agent_interactive(topic)
        
        # For now, we'll handle the interactive flow in a simplified way
        # In a full implementation, you'd need to maintain session state
        if result.get("workflow_status") == "completed":
            say("✅ Interactive session completed! Check the generated content above.")
        else:
            say("❌ Interactive session failed. Please try again.")
            
    except Exception as e:
        logger.error(f"Error in interactive session: {str(e)}")
        say(f"❌ *Error:* {str(e)}")

def process_image_with_agent(say, image_bytes: bytes, user_id: str, channel: str):
    """Process uploaded image with the agent"""
    try:
        say("🖼️ Processing uploaded image...")
        
        # Save image temporarily
        temp_image_path = f"temp_image_{user_id}.jpg"
        with open(temp_image_path, "wb") as f:
            f.write(image_bytes)
        
        # Process with agent (you'll need to modify your agent to handle images)
        # For now, just acknowledge the upload
        say("✅ Image received! Image processing feature coming soon.")
        
        # Clean up
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        say(f"❌ *Error processing image:* {str(e)}")

@app.get("/pdf/{filename}")
def get_pdf(filename: str):
    """Serve generated PDF files"""
    filepath = f"outputs/{filename}"
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="application/pdf", filename=filename)
    return {"error": "PDF not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 