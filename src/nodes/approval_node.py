"""
Approval Node for LinkedIn Content Automation Agent
Gets user approval for promotional content before posting
"""
from typing import Dict, Any
from src.state import State


def approval_node(state: State) -> Dict[str, Any]:
    """
    Approval node that returns approval request state for Slack/async environments.
    
    Args:
        state: Current workflow state with LinkedIn post and PDF
        
    Returns:
        Updated state indicating approval is needed
    """
    # Get data from state
    linkedin_post = state.get("linkedin_post")
    pdf_path = state.get("pdf_path")
    product_data = state.get("product_data")
    
    if not linkedin_post:
        return {
            "workflow_status": "failed",
            "error_message": "No LinkedIn post available for approval",
            "messages": [
                {
                    "role": "system",
                    "content": "No LinkedIn post available for approval"
                }
            ]
        }
    
    # Return state indicating approval is needed
    return {
        "user_approval": None,  # Pending approval
        "promotion_status": "awaiting_approval",
        "workflow_status": "promotion",
        "messages": [
            {
                "role": "system",
                "content": "Content ready for approval"
            }
        ]
    } 