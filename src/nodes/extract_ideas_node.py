"""
Extract Ideas node for LinkedIn Content Automation Agent
Uses LangChain Groq to analyze transcribed content and generate fresh content ideas
"""
import os
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from src.state import State, ContentIdea


def extract_ideas_node(state: State) -> Dict[str, Any]:
    """
    Extract Ideas node that analyzes scraped content and generates fresh content ideas.
    
    Args:
        state: Current workflow state with scraped content
        
    Returns:
        Updated state with generated content ideas
    """
    # Get Groq API key from environment
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    # Get scraped content
    scraped_content = state.get("scraped_content", [])
    topic = state.get("topic", "")
    
    if not scraped_content:
        return {
            "content_ideas": [],
            "workflow_status": "failed",
            "error_message": "No scraped content available for idea extraction",
            "messages": [
                {
                    "role": "system",
                    "content": "No scraped content available for idea extraction"
                }
            ]
        }
    
    try:
        # Update status to in progress
        state["workflow_status"] = "generating"
        
        # Initialize Groq LLM
        llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama-3.3-70b-versatile",  # Using Llama 3.3 70B Versatile for high-quality analysis
            temperature=0.7
        )
        
        # Prepare content for analysis
        content_summary = prepare_content_for_analysis(scraped_content, topic)
        
        # Generate content ideas using LLM
        content_ideas = generate_content_ideas(llm, content_summary, topic)
        
        # Update state
        return {
            "content_ideas": content_ideas,
            "workflow_status": "awaiting_choice",
            "messages": [
                {
                    "role": "system",
                    "content": f"Successfully generated {len(content_ideas)} content ideas from {len(scraped_content)} scraped videos. Please choose which idea you'd like to develop into content."
                }
            ]
        }
        
    except Exception as e:
        error_msg = f"Error during idea extraction: {str(e)}"
        return {
            "content_ideas": [],
            "workflow_status": "failed",
            "error_message": error_msg,
            "messages": [
                {
                    "role": "system",
                    "content": f"Idea extraction failed: {error_msg}"
                }
            ]
        }


def prepare_content_for_analysis(scraped_content: List, topic: str) -> str:
    """
    Prepare scraped content for LLM analysis by creating a structured summary.
    
    Args:
        scraped_content: List of scraped content objects
        topic: The original topic
        
    Returns:
        Formatted content summary for LLM analysis
    """
    summary_parts = [f"TOPIC: {topic}\n"]
    summary_parts.append("SCRAPED CONTENT SUMMARY:\n")
    
    for i, content in enumerate(scraped_content, 1):
        summary_parts.append(f"\n--- VIDEO {i} ---")
        summary_parts.append(f"Title: {content.title}")
        summary_parts.append(f"Channel: {content.metadata.get('channel', 'Unknown')}")
        summary_parts.append(f"Views: {content.metadata.get('views', 'Unknown')}")
        summary_parts.append(f"Duration: {content.metadata.get('duration', 'Unknown')}")
        
        # Add transcript (truncated if too long)
        if content.transcript:
            transcript_preview = content.transcript[:2000] + "..." if len(content.transcript) > 2000 else content.transcript
            summary_parts.append(f"Transcript Preview: {transcript_preview}")
        
        # Add description if available
        if content.content:
            desc_preview = content.content[:500] + "..." if len(content.content) > 500 else content.content
            summary_parts.append(f"Description: {desc_preview}")
    
    return "\n".join(summary_parts)


def generate_content_ideas(llm: ChatGroq, content_summary: str, topic: str) -> List[ContentIdea]:
    """
    Use LLM to generate fresh, original content ideas from scraped content.
    
    Args:
        llm: LangChain Groq LLM instance
        content_summary: Formatted content summary
        topic: Original topic
        
    Returns:
        List of ContentIdea objects
    """
    
    # Create the prompt for idea generation
    system_prompt = """You are an expert LinkedIn content strategist and AI analyst. Your task is to analyze transcribed content from YouTube videos and generate fresh, original content ideas for LinkedIn posts.

IMPORTANT GUIDELINES:
1. Generate EXACTLY 2 unique, original content ideas
2. Each idea should be different from the source material but inspired by it
3. Focus on actionable insights, trends, and valuable takeaways
4. Target business professionals and thought leaders
5. Make ideas engaging and shareable
6. Include specific angles or perspectives not covered in the source material

CONTENT IDEA STRUCTURE:
- Title: Catchy, professional title
- Description: Brief explanation of the idea
- Key Points: 3-5 main talking points
- Target Audience: Specific audience segment
- Inspiration Sources: Which video(s) inspired this idea

ANALYSIS APPROACH:
- Look for patterns, trends, and insights across multiple videos
- Identify gaps or opportunities not fully explored
- Extract actionable business insights
- Consider current market context and timing
- Focus on unique angles and perspectives"""

    user_prompt = f"""Please analyze the following content and generate EXACTLY 2 fresh, original LinkedIn content ideas:

{content_summary}

Generate your response in the following JSON format:
{{
    "ideas": [
        {{
            "title": "Catchy title here",
            "description": "Brief description of the idea",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "target_audience": "Specific audience description",
            "inspiration_sources": ["Video 1", "Video 2"]
        }}
    ]
}}

Focus on creating original insights that would be valuable for LinkedIn professionals interested in {topic}."""

    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    # Get LLM response
    response = llm.invoke(messages)
    
    # Parse the response and create ContentIdea objects
    try:
        # Extract JSON from response (handle potential formatting issues)
        response_text = response.content
        print(f"Raw LLM response before parsing:\n{response_text}")  # Debug print
        
        # Try to extract JSON from the response
        import json
        import re
        
        # Look for JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}. Attempting to sanitize control characters.")
                # Remove control characters
                sanitized = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
                print(f"Sanitized JSON string:\n{sanitized}")
                data = json.loads(sanitized)
            
            ideas = []
            for idea_data in data.get("ideas", []):
                idea = ContentIdea(
                    title=idea_data.get("title", ""),
                    description=idea_data.get("description", ""),
                    key_points=idea_data.get("key_points", []),
                    target_audience=idea_data.get("target_audience", ""),
                    inspiration_sources=idea_data.get("inspiration_sources", [])
                )
                ideas.append(idea)
            
            return ideas
        else:
            print("No JSON found in LLM response. Using fallback.")
            return create_fallback_ideas(response_text, topic)
            
    except Exception as e:
        print(f"Error parsing LLM response: {e}\nRaw response was:\n{response.content}")
        # Fallback: create ideas from the raw response
        return create_fallback_ideas(response.content, topic)


def create_fallback_ideas(response_text: str, topic: str) -> List[ContentIdea]:
    """
    Create fallback content ideas when JSON parsing fails.
    
    Args:
        response_text: Raw LLM response text
        topic: Original topic
        
    Returns:
        List of ContentIdea objects
    """
    # Split response into sections and create ideas
    sections = response_text.split('\n\n')
    ideas = []
    
    for i, section in enumerate(sections[:2]):  # Limit to 2 ideas
        if section.strip() and len(section.strip()) > 50:
            # Extract title (first line or sentence)
            lines = section.strip().split('\n')
            title = lines[0].strip()
            if title.startswith(('1.', '2.', '3.', '4.', '5.', '-')):
                title = title[2:].strip()
            
            # Create description from the rest
            description = ' '.join(lines[1:])[:200] + "..." if len(' '.join(lines[1:])) > 200 else ' '.join(lines[1:])
            
            idea = ContentIdea(
                title=title or f"Content Idea {i+1}",
                description=description or f"Generated idea based on {topic}",
                key_points=[f"Key insight {j+1}" for j in range(3)],
                target_audience="Business professionals and thought leaders",
                inspiration_sources=[f"Video {j+1}" for j in range(min(3, i+1))]
            )
            ideas.append(idea)
    
    return ideas 