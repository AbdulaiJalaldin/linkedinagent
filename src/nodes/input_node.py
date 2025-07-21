"""
Input node for LinkedIn Content Automation Agent
Handles user topic input and initializes the workflow state
"""
from typing import Dict, Any
from src.state import State


def input_node(state: State) -> Dict[str, Any]:
    """
    Input node that processes the user's topic and initializes the workflow state.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with initialized values
    """
    # Extract topic from messages (assuming it's the last user message)
    topic = state.get("topic", "")
    
    if not topic:
        # Try to extract topic from messages
        messages = state.get("messages", [])
        for message in reversed(messages):
            if message.get("role") == "user":
                topic = message.get("content", "")
                break
    
    if not topic:
        raise ValueError("No topic provided. Please provide a topic for content generation.")
    
    # Initialize the state with default values
    return {
        "topic": topic,
        "scraped_content": [],
        "scraping_status": "pending",
        "scraping_errors": [],
        "content_ideas": [],
        "selected_idea": None,
        "research_data": None,
        "research_status": "pending",
        "linkedin_post": None,
        "writing_status": "pending",
        "generated_image": None,
        "image_status": "pending",
        "google_doc": None,
        "docs_status": "pending",
        "user_approval": None,
        "approval_feedback": None,
        "linkedin_post_id": None,
        "posting_status": "pending",
        "workflow_status": "initialized",
        "error_message": None,
        "messages": [
            {
                "role": "system",
                "content": f"LinkedIn Content Automation Agent initialized. Topic: {topic}"
            },
            {
                "role": "user", 
                "content": f"Please create LinkedIn content about: {topic}"
            }
        ]
    } 