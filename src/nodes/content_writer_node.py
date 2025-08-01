"""
LinkedIn Content Writer node for LinkedIn Content Automation Agent
Crafts engaging LinkedIn posts from selected content ideas
"""
import os
import re
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from src.state import State, LinkedInPost


def content_writer_node(state: State) -> Dict[str, Any]:
    """
    LinkedIn Content Writer node that crafts engaging posts from selected content ideas.
    
    Args:
        state: Current workflow state with selected idea
        
    Returns:
        Updated state with generated LinkedIn post
    """
    # Get Groq API key from environment
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    # Get selected idea
    selected_idea = state.get("selected_idea")
    scraped_content = state.get("scraped_content", [])
    topic = state.get("topic", "")
    
    if not selected_idea:
        return {
            "workflow_status": "failed",
            "error_message": "No selected idea available for content writing",
            "messages": [
                {
                    "role": "system",
                    "content": "No selected idea available for content writing"
                }
            ]
        }
    
    try:
        # Update status to in progress
        state["workflow_status"] = "writing"
        
        # Initialize Groq LLM
        llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="meta-llama/llama-4-scout-17b-16e-instruct",  # Using Llama 3.3 70B Versatile for high-quality writing
            temperature=0.8
        )
        
        # Prepare context for writing
        writing_context = prepare_writing_context(selected_idea, scraped_content, topic)
        
        # Generate LinkedIn post using LLM
        linkedin_post = generate_linkedin_post(llm, writing_context, selected_idea)
        
        # Update state
        return {
            "linkedin_post": linkedin_post,
            "writing_status": "completed",
            "workflow_status": "writing_completed",
            "messages": [
                {
                    "role": "system",
                    "content": f"Successfully created LinkedIn post: {linkedin_post.title}"
                }
            ]
        }
        
    except Exception as e:
        error_msg = f"Error during content writing: {str(e)}"
        return {
            "linkedin_post": None,
            "writing_status": "failed",
            "workflow_status": "failed",
            "error_message": error_msg,
            "messages": [
                {
                    "role": "system",
                    "content": f"Content writing failed: {error_msg}"
                }
            ]
        }


def prepare_writing_context(selected_idea, scraped_content: list, topic: str) -> str:
    """
    Prepare context for LinkedIn post writing.
    
    Args:
        selected_idea: The selected ContentIdea object
        scraped_content: List of scraped content objects
        topic: The original topic
        
    Returns:
        Formatted context for writing
    """
    context_parts = [f"TOPIC: {topic}\n"]
    context_parts.append("SELECTED IDEA:")
    context_parts.append(f"Title: {selected_idea.title}")
    context_parts.append(f"Description: {selected_idea.description}")
    context_parts.append(f"Key Points: {', '.join(selected_idea.key_points)}")
    context_parts.append(f"Target Audience: {selected_idea.target_audience}")
    context_parts.append(f"Inspiration Sources: {', '.join(selected_idea.inspiration_sources)}")
    
    # Add relevant scraped content for reference
    if scraped_content:
        context_parts.append("\nRELEVANT SOURCE CONTENT:")
        for i, content in enumerate(scraped_content[:3], 1):  # Limit to 3 sources
            context_parts.append(f"\n--- SOURCE {i} ---")
            context_parts.append(f"Title: {content.title}")
            if content.transcript:
                transcript_preview = content.transcript[:1000] + "..." if len(content.transcript) > 1000 else content.transcript
                context_parts.append(f"Key Insights: {transcript_preview}")
    
    return "\n".join(context_parts)


def generate_linkedin_post(llm: ChatGroq, writing_context: str, selected_idea) -> LinkedInPost:
    """
    Use LLM to generate an engaging LinkedIn post from the selected idea.
    
    Args:
        llm: LangChain Groq LLM instance
        writing_context: Formatted writing context
        selected_idea: The selected ContentIdea object
        
    Returns:
        LinkedInPost object
    """
    
    # Create the prompt for LinkedIn post generation
    system_prompt = """You are an expert LinkedIn content writer and social media strategist. Your task is to create an engaging, professional LinkedIn post from a selected content idea.

LINKEDIN POST GUIDELINES:
1. Hook: Start with a compelling hook that grabs attention in the first line
2. Storytelling: Use storytelling elements to make the content relatable and engaging
3. Value: Provide clear, actionable insights and takeaways
4. Professional Tone: Maintain a professional yet conversational tone
5. Structure: Use short paragraphs, bullet points, and white space for readability
6. Call-to-Action: End with a clear, engaging call-to-action
7. Hashtags: Include 3-5 relevant hashtags at the end
8. Length: Aim for 800-1200 characters (LinkedIn's sweet spot)

POST STRUCTURE:
- Hook (first line with emoji if appropriate)
- Problem/Challenge or story
- Solution/Insight with specific examples
- Key takeaways with bullet points
- Call-to-action
- Hashtags (separate from main content)

ENGAGEMENT TIPS:
- Ask questions to encourage comments
- Use numbers and statistics when relevant
- Include personal insights or experiences
- Make it shareable and valuable
- Use emojis sparingly but effectively
- Write in a conversational, natural tone
- Focus on providing real value to the audience

IMPORTANT: Write the post exactly as you would publish it on LinkedIn. Do not use any special formatting, JSON, or technical syntax - just write a natural, engaging LinkedIn post."""

    user_prompt = f"""Please create an engaging LinkedIn post based on the following content idea and context:

{writing_context}

Write the post exactly as you would publish it on LinkedIn. Include:
- A catchy title/hook
- The main content with proper formatting
- A clear call-to-action
- Relevant hashtags at the end

Focus on creating a post that would resonate with {selected_idea.target_audience} and provide value related to {selected_idea.title}.

Write the post in natural, human-readable format - no JSON or special formatting."""

    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    # Get LLM response
    response = llm.invoke(messages)
    
    # Parse the response and create LinkedInPost object
    try:
        # Extract content from the response
        response_text = response.content.strip()
        
        # Split the response into lines
        lines = response_text.split('\n')
        
        # Extract title from the first line
        title = lines[0].strip() if lines else selected_idea.title
        
        # Extract hashtags from the end of the post
        hashtags = []
        content_lines = []
        call_to_action = "Connect with me for more insights!"
        
        # Process lines to separate content, hashtags, and call-to-action
        for line in lines[1:]:  # Skip the title line
            line = line.strip()
            if not line:
                continue
                
            # Check if line contains hashtags
            if line.startswith('#') or '#' in line:
                # Extract hashtags from this line
                hashtag_matches = re.findall(r'#\w+', line)
                hashtags.extend(hashtag_matches)
                # Remove hashtags from the line for content
                content_line = re.sub(r'#\w+', '', line).strip()
                if content_line:
                    content_lines.append(content_line)
            else:
                content_lines.append(line)
        
        # Join content lines
        content = '\n'.join(content_lines).strip()
        
        # If no content was extracted, use the full response minus title
        if not content:
            content = '\n'.join(lines[1:]).strip()
        
        # If still no content, use the full response
        if not content:
            content = response_text
        
        # Generate hashtags if none were found
        if not hashtags:
            hashtags = [
                f"#{re.sub(r'[^a-zA-Z0-9]', '', word).lower()}" 
                for word in selected_idea.title.split()[:3]
            ]
        
        # Create LinkedInPost object
        post = LinkedInPost(
            title=title,
            content=content,
            hashtags=hashtags,
            call_to_action=call_to_action,
            estimated_engagement="Medium"
        )
        
        return post
        
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        # Fallback: create post from the raw response
        return create_fallback_post(response.content, selected_idea)


def create_fallback_post(response_text: str, selected_idea) -> LinkedInPost:
    """
    Create fallback LinkedIn post when JSON parsing fails.
    
    Args:
        response_text: Raw LLM response text
        selected_idea: The selected ContentIdea object
        
    Returns:
        LinkedInPost object
    """
    # Remove any JSON-like blocks from the response text
    cleaned_text = re.sub(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', response_text, flags=re.DOTALL)
    content = cleaned_text.strip()
    # Extract title from first line or use idea title
    lines = content.split('\n')
    title = lines[0].strip() if lines and lines[0].strip() else selected_idea.title
    # Use the rest as content
    post_content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
    # If post_content is empty, use the full cleaned_text minus the title
    if not post_content:
        post_content = cleaned_text.strip()
        if post_content.startswith(title):
            post_content = post_content[len(title):].strip()
    # If still empty, use a placeholder and print debug info
    if not post_content:
        print("[DEBUG] LLM response produced empty content. Raw response:")
        print(response_text)
        post_content = "[Content could not be extracted. Please review the AI response above.]"
    # Generate hashtags based on the idea
    hashtags = [
        f"#{re.sub(r'[^a-zA-Z0-9]', '', word).lower()}" for word in selected_idea.title.split()[:3]
    ]
    return LinkedInPost(
        title=title,
        content=post_content,
        hashtags=hashtags,
        call_to_action="Connect with me for more insights!",
        estimated_engagement="Medium"
    ) 