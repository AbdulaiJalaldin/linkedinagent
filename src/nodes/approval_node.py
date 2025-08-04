"""
Approval Node for LinkedIn Content Automation Agent
Gets user approval for promotional content before posting
"""
from typing import Dict, Any
from src.state import State


def approval_node(state: State) -> Dict[str, Any]:
    """
    Approval node that displays generated content and gets user approval.
    
    Args:
        state: Current workflow state with LinkedIn post and PDF
        
    Returns:
        Updated state with user approval decision
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
    
    print("\n" + "="*60)
    print("📋 CONTENT PREVIEW")
    print("="*60)
    
    print(f"Title: {linkedin_post.title}")
    print("\nContent:")
    print(linkedin_post.content)
    print(f"\nCall to Action: {linkedin_post.call_to_action}")
    print(f"Hashtags: {' '.join(linkedin_post.hashtags)}")
    print(f"Estimated Engagement: {linkedin_post.estimated_engagement}")
    
    if pdf_path:
        print(f"\n📄 PDF Document: {pdf_path}")
    
    print("\n" + "="*60)
    print("APPROVAL")
    print("="*60)
    
    while True:
        approval = input("Do you approve this content for LinkedIn posting? (y/n): ").strip().lower()
        if approval in ['y', 'yes']:
            user_approval = True
            break
        elif approval in ['n', 'no']:
            user_approval = False
            break
        else:
            print("Please enter 'y' for yes or 'n' for no.")
    
    if user_approval:
        return {
            "user_approval": True,
            "promotion_status": "awaiting_approval",
            "workflow_status": "promotion",
            "messages": [
                {
                    "role": "system",
                    "content": "User approved the promotional content for LinkedIn posting"
                }
            ]
        }
    else:
        return {
            "user_approval": False,
            "promotion_status": "awaiting_approval",
            "workflow_status": "promotion",
            "messages": [
                {
                    "role": "system",
                    "content": "User rejected the promotional content"
                }
            ]
        } 