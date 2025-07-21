"""
Scraping node for LinkedIn Content Automation Agent
Handles scraping of YouTube videos using Apify
"""
import os
import asyncio
from typing import Dict, Any, List
from apify_client import ApifyClient
from youtube_transcript_api import YouTubeTranscriptApi
import re

from src.state import State, ScrapedContent

from apify_client import ApifyClient
import re
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List

class ContentScraper:
    """Handles YouTube video scraping"""

    def __init__(self, apify_token: str):
        self.apify_client = ApifyClient(apify_token)

    def extract_youtube_id(self, url: str) -> str:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_youtube_transcript(self, video_id: str) -> str:
        """Get transcript from YouTube video"""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([entry['text'] for entry in transcript_list])
            return transcript_text
        except Exception as e:
            print(f"Error getting transcript for video {video_id}: {e}")
            return ""

    async def scrape_youtube_videos(self, topic: str, max_videos: int = 3) -> List:
        """Scrape YouTube videos related to the topic"""
        try:
            run_input = {
                "searchQueries": [topic],   # List of search terms
                "maxResults": max_videos,   # Max videos per search term
                "maxResultsShorts": 0,
                "maxResultStreams": 0,
                "includeDescription": True,
                "includeComments": False,
                "includeSubtitles": True,
                "includeVideoUrls": True,
                "maxRequestRetries": 3,
                "maxConcurrency": 10
            }

            # Run the YouTube scraper actor
            run = self.apify_client.actor("streamers/youtube-scraper").call(run_input=run_input)

            scraped_content = []

            # Fetch results from the dataset
            dataset_items = self.apify_client.dataset(run["defaultDatasetId"]).iterate_items()

            for item in dataset_items:
                video_id = self.extract_youtube_id(item.get("url", ""))
                if video_id:
                    transcript = self.get_youtube_transcript(video_id)

                    content = ScrapedContent(
                        source_type="youtube",
                        source_url=item.get("url", ""),
                        title=item.get("title", ""),
                        content=item.get("description", ""),
                        transcript=transcript,
                        metadata={
                            "views": item.get("viewCount"),
                            "likes": item.get("likeCount"),
                            "duration": item.get("duration"),
                            "upload_date": item.get("uploadDate"),
                            "channel": item.get("channelName")
                        }
                    )
                    scraped_content.append(content)

            return scraped_content

        except Exception as e:
            print(f"Error scraping YouTube videos: {e}")
            return []

            
        except Exception as e:
            print(f"Error scraping YouTube videos: {e}")
            return []


def scraping_node(state: State) -> Dict[str, Any]:
    """
    Scraping node that scrapes YouTube videos related to the topic.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with scraped content
    """
    topic = state.get("topic", "")
    if not topic:
        raise ValueError("No topic provided for scraping")
    
    # Get Apify token from environment
    apify_token = os.getenv("APIFY_TOKEN")
    if not apify_token:
        raise ValueError("APIFY_TOKEN environment variable not set")
    
    # Initialize scraper
    scraper = ContentScraper(apify_token)
    
    try:
        # Update status to in progress
        state["scraping_status"] = "in_progress"
        state["workflow_status"] = "scraping"
        
        # Get max videos from environment or use default
        max_videos = int(os.getenv("MAX_YOUTUBE_VIDEOS", "3"))
        
        # Scrape YouTube videos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        youtube_content = loop.run_until_complete(scraper.scrape_youtube_videos(topic, max_videos))
        
        # Update state
        return {
            "scraped_content": youtube_content,
            "scraping_status": "completed",
            "workflow_status": "scraping",
            "messages": [
                {
                    "role": "system",
                    "content": f"Successfully scraped {len(youtube_content)} YouTube videos for topic: {topic}"
                }
            ]
        }
        
    except Exception as e:
        error_msg = f"Error during scraping: {str(e)}"
        return {
            "scraping_status": "failed",
            "scraping_errors": [error_msg],
            "workflow_status": "failed",
            "error_message": error_msg,
            "messages": [
                {
                    "role": "system",
                    "content": f"Scraping failed: {error_msg}"
                }
            ]
        } 