"""
State management for LinkedIn Content Automation Agent
"""
from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class ScrapedContent(BaseModel):
    """Represents scraped content from various sources"""
    source_type: str  # "youtube", "article", etc.
    source_url: str
    title: str
    content: str
    transcript: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ContentIdea(BaseModel):
    """Represents a content idea generated from scraped content"""
    title: str
    description: str
    key_points: List[str]
    target_audience: str
    inspiration_sources: List[str]


class ResearchData(BaseModel):
    """Represents research data gathered to support content ideas"""
    facts: List[str]
    statistics: List[str]
    sources: List[str]
    supporting_evidence: List[str]


class LinkedInPost(BaseModel):
    """Represents a LinkedIn post"""
    title: str
    content: str
    hashtags: List[str]
    call_to_action: str
    estimated_engagement: str


class GeneratedImage(BaseModel):
    """Represents a generated image for the post"""
    image_path: str
    image_description: str
    prompt_used: str


class GoogleDoc(BaseModel):
    """Represents a Google Doc with the content"""
    doc_id: str
    doc_url: str
    title: str


class State(TypedDict):
    """Main state for the LinkedIn Content Automation Agent"""
    # Input
    topic: str
    
    # Messages for agent communication
    messages: Annotated[List[Dict[str, Any]], add_messages]
    
    # Scraping phase
    scraped_content: List[ScrapedContent]
    scraping_status: str  # "pending", "in_progress", "completed", "failed"
    scraping_errors: List[str]
    
    # Content generation phase
    content_ideas: List[ContentIdea]
    selected_idea: Optional[ContentIdea]
    
    # Research phase
    research_data: Optional[ResearchData]
    research_status: str  # "pending", "in_progress", "completed", "failed"
    
    # Content writing phase
    linkedin_post: Optional[LinkedInPost]
    writing_status: str  # "pending", "in_progress", "completed", "failed"
    
    # Image generation phase
    generated_image: Optional[GeneratedImage]
    image_status: str  # "pending", "in_progress", "completed", "failed"
    
    # Google Docs phase
    google_doc: Optional[GoogleDoc]
    docs_status: str  # "pending", "in_progress", "completed", "failed"
    
    # Approval phase
    user_approval: Optional[bool]  # True for approved, False for rejected, None for pending
    approval_feedback: Optional[str]
    
    # LinkedIn posting phase
    linkedin_post_id: Optional[str]
    posting_status: str  # "pending", "in_progress", "completed", "failed"
    
    # Overall workflow status
    workflow_status: str  # "initialized", "scraping", "generating", "researching", "writing", "imaging", "docs", "approval", "posting", "completed", "failed"
    error_message: Optional[str] 