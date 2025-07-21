"""
Choice node for LinkedIn Content Automation Agent
Handles user selection between generated content ideas
"""
from typing import Dict, Any
from src.state import State, ContentIdea


def choice_node(state: State) -> Dict[str, Any]:
    """
    Choice node that handles user selection between generated content ideas.
    
    Args:
        state: Current workflow state with content ideas
        
    Returns:
        Updated state with selected idea
    """
    content_ideas = state.get("content_ideas", [])
    user_choice = state.get("user_choice")
    
    if not content_ideas:
        return {
            "workflow_status": "failed",
            "error_message": "No content ideas available for selection",
            "messages": [
                {
                    "role": "system",
                    "content": "No content ideas available for selection"
                }
            ]
        }
    
    if len(content_ideas) != 2:
        return {
            "workflow_status": "failed",
            "error_message": f"Expected 2 content ideas, but found {len(content_ideas)}",
            "messages": [
                {
                    "role": "system",
                    "content": f"Expected 2 content ideas, but found {len(content_ideas)}"
                }
            ]
        }
    
    # If no user choice provided, this means we're in the initial workflow run
    # We should pause here and let the interactive function handle user input
    if user_choice is None:
        return {
            "workflow_status": "awaiting_choice",
            "messages": [
                {
                    "role": "system",
                    "content": "Content ideas generated successfully. Awaiting user choice."
                }
            ]
        }
    
    # Validate user choice
    if user_choice not in [1, 2]:
        return {
            "workflow_status": "failed",
            "error_message": f"Invalid choice: {user_choice}. Please choose 1 or 2.",
            "messages": [
                {
                    "role": "system",
                    "content": f"Invalid choice: {user_choice}. Please choose 1 or 2."
                }
            ]
        }
    
    # Select the chosen idea (convert to 0-based index)
    selected_idea = content_ideas[user_choice - 1]
    
    return {
        "selected_idea": selected_idea,
        "workflow_status": "idea_selected",
        "messages": [
            {
                "role": "system",
                "content": f"Selected idea: {selected_idea.title}\n\n{selected_idea.description}"
            }
        ]
    }


def format_ideas_for_display(content_ideas: list) -> str:
    """
    Format content ideas for user display.
    
    Args:
        content_ideas: List of ContentIdea objects
        
    Returns:
        Formatted string for display
    """
    display_parts = []
    
    for i, idea in enumerate(content_ideas, 1):
        display_parts.append(f"IDEA {i}: {idea.title}")
        display_parts.append(f"Description: {idea.description}")
        display_parts.append(f"Key Points:")
        for j, point in enumerate(idea.key_points, 1):
            display_parts.append(f"  {j}. {point}")
        display_parts.append(f"Target Audience: {idea.target_audience}")
        display_parts.append(f"Inspiration Sources: {', '.join(idea.inspiration_sources)}")
        display_parts.append("")  # Empty line for separation
    
    display_parts.append("Please respond with '1' or '2' to select your preferred idea.")
    
    return "\n".join(display_parts) 