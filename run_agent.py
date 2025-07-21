#!/usr/bin/env python3
"""
LinkedIn Content Automation Agent - Main Runner
Interactive tool for creating LinkedIn content with user choice
"""
import os
import sys
from dotenv import load_dotenv
from src.graph import run_linkedin_agent_interactive

# Load environment variables from .env file
load_dotenv()


def check_environment_variables():
    """
    Check for required environment variables and provide helpful feedback.
    """
    print("🔍 Checking environment variables...")
    
    # Required variables
    required_vars = {
        "GROQ_API_KEY": "Required for AI content generation",
        "LINKEDIN_ACCESS_TOKEN": "Required for posting to LinkedIn",
        "LINKEDIN_CLIENT_ID": "Required for LinkedIn API access",
        "LINKEDIN_CLIENT_SECRET": "Required for LinkedIn API access"
    }
    
    missing_vars = []
    optional_vars = []
    
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var}: {description}")
        else:
            print(f"✅ {var}: Found")
    
    # Optional variables
    optional_vars_list = ["YOUTUBE_API_KEY", "APIFY_API_TOKEN"]
    for var in optional_vars_list:
        if not os.getenv(var):
            optional_vars.append(var)
        else:
            print(f"✅ {var}: Found (optional)")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file.")
        print("\nExample .env file:")
        print(f"GROQ_API_KEY=your_groq_api_key_here")
        print(f"LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token_here")
        print(f"LINKEDIN_CLIENT_ID=your_linkedin_client_id_here")
        print(f"LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here")
        print(f"YOUTUBE_API_KEY=your_youtube_api_key_here (optional)")
        print(f"APIFY_API_TOKEN=your_apify_token_here (optional)")
        return False  
    if optional_vars:
        print(f"\n⚠️  Optional variables not set: {', '.join(optional_vars)}")
        print("These are not required but may enhance functionality.")
    
    print("\n✅ All required environment variables are set!")
    return True


def main():
    """
    Main function to run the LinkedIn Content Automation Agent interactively.
    """
    print("="*60)
    print("🚀 LINKEDIN CONTENT AUTOMATION AGENT")
    print("="*60)
    print("This tool will help you create engaging LinkedIn content by:")
    print("1. Scraping relevant YouTube content")
    print("2. Generating 2 unique content ideas")
    print("3. Letting you choose your preferred idea")
    print("4. Creating a professional LinkedIn post")
    print("5. Generating a matching image")
    print("6. Optionally posting directly to LinkedIn")
    print("="*60)
    
    # Check environment variables
    if not check_environment_variables():
        return 1
    
    # Get topic from user
    print("\n📝 Enter your content topic:")
    print("(e.g., 'artificial intelligence in business', 'leadership tips', 'startup growth')")
    
    while True:
        topic = input("\nTopic: ").strip()
        if topic:
            break
        print("Please enter a valid topic.")
    
    print(f"\n🚀 Starting content generation for: '{topic}'")
    print("This may take a few minutes...")
    
    try:
        # Run the agent with interactive choice
        result = run_linkedin_agent_interactive(topic)
        
        # Display results
        print("\n" + "="*60)
        print("WORKFLOW COMPLETED")
        print("="*60)
        
        status = result.get("workflow_status", "unknown")
        print(f"Status: {status}")
        
        if status == "posting_completed":
            print("✅ Content posted to LinkedIn successfully!")
            
            # Display posting results
            if result.get("linkedin_post_id"):
                print(f"📝 Post ID: {result['linkedin_post_id']}")
            if result.get("post_url"):
                print(f"🔗 Post URL: {result['post_url']}")
            
            # Display the generated LinkedIn post
            if result.get("linkedin_post"):
                post = result["linkedin_post"]
                print("\n" + "="*60)
                print("YOUR LINKEDIN POST")
                print("="*60)
                print(f"Title: {post.title}")
                print("\nContent:")
                print(post.content)
                print(f"\nCall to Action: {post.call_to_action}")
                print(f"\nHashtags: {' '.join(post.hashtags)}")
                print(f"Estimated Engagement: {post.estimated_engagement}")
            
            # Display generated image information
            if result.get("generated_image"):
                image = result["generated_image"]
                print(f"\n🖼️  Generated Image: {image.image_path}")
                print(f"Image Description: {image.image_description}")
            
        elif status == "imaging_completed":
            print("✅ Content and image generation completed!")
            
            # Display the generated LinkedIn post
            if result.get("linkedin_post"):
                post = result["linkedin_post"]
                print("\n" + "="*60)
                print("YOUR LINKEDIN POST")
                print("="*60)
                print(f"Title: {post.title}")
                print("\nContent:")
                print(post.content)
                print(f"\nCall to Action: {post.call_to_action}")
                print(f"\nHashtags: {' '.join(post.hashtags)}")
                print(f"Estimated Engagement: {post.estimated_engagement}")
            
            # Display generated image information
            if result.get("generated_image"):
                image = result["generated_image"]
                print(f"\n🖼️  Generated Image: {image.image_path}")
                print(f"Image Description: {image.image_description}")
            
        elif status == "writing_completed":
            print("✅ Content generation successful!")
            
            # Display the generated LinkedIn post
            if result.get("linkedin_post"):
                post = result["linkedin_post"]
                print("\n" + "="*60)
                print("YOUR LINKEDIN POST")
                print("="*60)
                print(f"Title: {post.title}")
                print("\nContent:")
                print(post.content)
                print(f"\nCall to Action: {post.call_to_action}")
                print(f"\nHashtags: {' '.join(post.hashtags)}")
                print(f"Estimated Engagement: {post.estimated_engagement}")
                
                # Save to file option
                save_choice = input("\n💾 Would you like to save this post to a file? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes']:
                    filename = f"linkedin_post_{topic.replace(' ', '_').lower()}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {post.title}\n\n")
                        f.write(f"Content:\n{post.content}\n\n")
                        f.write(f"Hashtags: {' '.join(post.hashtags)}\n")
                        f.write(f"Call to Action: {post.call_to_action}\n")
                        f.write(f"Estimated Engagement: {post.estimated_engagement}\n")
                    print(f"✅ Post saved to: {filename}")
            
            # Display summary
            print(f"\n📊 Summary:")
            print(f"- Scraped {len(result.get('scraped_content', []))} pieces of content")
            print(f"- Generated 2 content ideas")
            print(f"- Created 1 LinkedIn post")
            
        elif status == "failed":
            error_msg = result.get("error_message", "Unknown error")
            print(f"❌ Workflow failed: {error_msg}")
            return 1
        else:
            print(f"⚠️  Workflow ended with status: {status}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        import traceback
        print(f"Error type: {type(e).__name__}")
        print("Full traceback:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())