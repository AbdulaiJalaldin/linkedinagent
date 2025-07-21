# LinkedIn Content Automation AI Agent

A sophisticated AI agent that automates the entire LinkedIn content creation process, from topic input to automatic posting, with human approval workflow.

## Features

- **Content Scraping**: Automatically scrapes and transcribes top-performing YouTube videos
- **Content Analysis**: Extracts fresh, original content ideas from viral content
- **Interactive Choice**: Presents 2 content ideas and lets you choose your preferred one
- **AI Content Writing**: Creates engaging, value-driven LinkedIn posts from your selected idea
- **Research Integration**: Gathers supporting facts and statistics for content ideas
- **Image Generation**: Generates relevant images for posts using open-source models
- **Google Docs Integration**: Saves content to Google Docs for review
- **Human Approval Workflow**: Requires user approval before posting
- **LinkedIn Auto-Posting**: Automatically posts approved content to LinkedIn

## Architecture

The agent uses LangGraph to create a sophisticated workflow with multiple specialized nodes:

1. **Input Node**: Processes user topic and initializes workflow
2. **Scraping Node**: Scrapes YouTube videos using Apify
3. **Extract Ideas Node**: Analyzes scraped content to generate 2 original ideas
4. **Choice Node**: Handles user selection between the 2 generated ideas
5. **Content Writer Node**: Crafts engaging LinkedIn posts from selected idea
6. **Research Node**: Gathers supporting facts and statistics
7. **Image Generation Node**: Creates relevant images
8. **Google Docs Node**: Saves content for review
9. **Approval Node**: Handles user approval workflow
10. **LinkedIn Posting Node**: Posts approved content

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd linkedin_agent
   ```

2. **Create and activate virtual environment**:
   ```bash
   conda create --name linkagentenv python=3.11
   conda activate linkagentenv
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Copy `env_example.txt` to `.env`
   - Fill in your API keys and configuration

## Required API Keys

- **Apify Token**: For web scraping YouTube videos
- **Groq API Key**: For AI content generation and analysis
- **KIE AI API Key**: For image generation using 4o Image API
- **LinkedIn API Credentials**: For posting content to LinkedIn
- **Google API Credentials**: For Google Docs integration

## Usage

### Interactive Usage (Recommended)

```bash
python run_agent.py
```

This will:
1. Ask for your content topic
2. Scrape relevant YouTube videos
3. Generate 2 unique content ideas
4. Let you choose your preferred idea
5. Create a professional LinkedIn post
6. Optionally save the post to a file

### Programmatic Usage

```python
from src.graph import run_linkedin_agent_interactive

# Run the agent with interactive choice
result = run_linkedin_agent_interactive("artificial intelligence in business")
print(f"Workflow status: {result['workflow_status']}")

# Access the generated post
if result.get("linkedin_post"):
    post = result["linkedin_post"]
    print(f"Title: {post.title}")
    print(f"Content: {post.content}")
```

### Advanced Usage

```python
from src.graph import create_linkedin_agent_graph

# Create the graph
graph = create_linkedin_agent_graph()

# Run with custom inputs
inputs = {
    "topic": "digital marketing trends 2024",
    "messages": [
        {
            "role": "user",
            "content": "Create LinkedIn content about digital marketing trends"
        }
    ]
}

# Execute the workflow
result = graph.invoke(inputs)
```

## Project Structure

```
linkedin_agent/
├── src/
│   ├── __init__.py
│   ├── state.py              # LangGraph state management
│   ├── graph.py              # Main workflow graph
│   └── nodes/
│       ├── __init__.py
│       ├── input_node.py     # Input processing node
│       ├── scraping_node.py  # YouTube video scraping node
│       ├── extract_ideas_node.py  # Content idea generation
│       ├── choice_node.py    # User choice handling
│       └── content_writer_node.py # LinkedIn post creation
├── run_agent.py              # Interactive main runner
├── requirements.txt          # Python dependencies
├── env_example.txt          # Environment variables template
└── README.md               # This file
```

## Current Implementation Status

✅ **Completed**:
- State management with comprehensive data structures
- Input node for topic processing
- Scraping node with Apify integration for YouTube videos
- Extract ideas node that generates 2 unique content ideas
- Choice node for interactive user selection
- Content writer node that creates engaging LinkedIn posts
- Image generation node using KIE AI 4o Image API
- Interactive workflow with user choice functionality
- YouTube video scraping and transcription
- Complete workflow graph with choice integration

🔄 **In Progress**:
- Research node
- Google Docs integration
- Approval workflow
- LinkedIn posting

## Configuration

The agent can be configured through environment variables:

- `MAX_YOUTUBE_VIDEOS`: Maximum number of YouTube videos to scrape (default: 3)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on GitHub or contact the development team. 