"""
Main LangGraph workflow for LinkedIn Content Automation Agent
"""
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from src.state import State
from src.nodes.input_node import input_node
from src.nodes.scraping_node import scraping_node
from src.nodes.extract_ideas_node import extract_ideas_node
from src.nodes.choice_node import choice_node
from src.nodes.content_writer_node import content_writer_node
from src.nodes.image_generation_node import image_generation_node


def create_linkedin_agent_graph():
    """
    Create the LinkedIn Content Automation Agent workflow graph.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("input", input_node)
    workflow.add_node("scraping", scraping_node)
    workflow.add_node("extract_ideas", extract_ideas_node)
    workflow.add_node("choice", choice_node)
    workflow.add_node("content_writer", content_writer_node)
    workflow.add_node("image_generation", image_generation_node)
    
    # Add edges
    workflow.add_edge("input", "scraping")
    workflow.add_edge("scraping", "extract_ideas")
    workflow.add_edge("extract_ideas", "choice")
    workflow.add_edge("content_writer", "image_generation")
    
    # Add conditional routing after choice node
    def route_after_choice(state):
        """Route to content writer if idea is selected, otherwise end"""
        if state.get("selected_idea") is not None:
            return "content_writer"
        else:
            return "__end__"  # End the workflow
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "choice",
        route_after_choice,
        {
            "content_writer": "content_writer",
            "__end__": "__end__"  # This will end the workflow
        }
    )
    
    # Set entry point
    workflow.set_entry_point("input")
    
    # Compile the graph
    return workflow.compile()


def run_linkedin_agent(topic: str, user_choice: int = None):
    """
    Run the LinkedIn Content Automation Agent with a given topic.
    
    Args:
        topic: The topic to create content about
        user_choice: User's choice (1 or 2) for content ideas, if provided
        
    Returns:
        The final state of the workflow
    """
    # Create the graph
    graph = create_linkedin_agent_graph()
    
    # Prepare input
    inputs = {
        "topic": topic,
        "messages": [
            {
                "role": "user",
                "content": f"Create LinkedIn content about: {topic}"
            }
        ]
    }
    
    # If user choice is provided, add it to the inputs
    if user_choice is not None:
        inputs["user_choice"] = user_choice
    
    # Run the workflow
    result = graph.invoke(inputs)
    
    return result


def run_linkedin_agent_interactive(topic: str):
    """
    Run the LinkedIn Content Automation Agent with interactive user choice.
    
    Args:
        topic: The topic to create content about
        
    Returns:
        The final state of the workflow
    """
    # Create the graph
    graph = create_linkedin_agent_graph()
    
    # Prepare initial input
    inputs = {
        "topic": topic,
        "messages": [
            {
                "role": "user",
                "content": f"Create LinkedIn content about: {topic}"
            }
        ]
    }
    
    # Run the workflow up to the choice point
    result = graph.invoke(inputs)
    
    # print(f"Debug: Workflow status after first run: {result.get('workflow_status')}")
    # print(f"Debug: Content ideas count: {len(result.get('content_ideas', []))}")
    
    # Check if we need user input
    if result.get("workflow_status") == "awaiting_choice":
        # Display the ideas and get user choice
        # print("\n" + "="*50)
        # print("CONTENT IDEAS GENERATED")
        # print("="*50)
        
        content_ideas = result.get("content_ideas", [])
        for i, idea in enumerate(content_ideas, 1):
            print(f"\nIDEA {i}: {idea.title}")
            print(f"Description: {idea.description}")
            print(f"Key Points:")
            for j, point in enumerate(idea.key_points, 1):
                print(f"  {j}. {point}")
            print(f"Target Audience: {idea.target_audience}")
            print(f"Inspiration Sources: {', '.join(idea.inspiration_sources)}")
            print("-" * 30)
        
        # Get user choice
        while True:
            try:
                choice = input("\nPlease choose an idea (1 or 2): ").strip()
                if choice in ['1', '2']:
                    user_choice = int(choice)
                    break
                else:
                    print("Please enter 1 or 2.")
            except ValueError:
                print("Please enter a valid number (1 or 2).")
        
        # Get the selected idea
        selected_idea = content_ideas[user_choice - 1]
        
        # Update the result with the user choice and selected idea
        result["user_choice"] = user_choice
        result["selected_idea"] = selected_idea
        result["workflow_status"] = "idea_selected"
        
        # Instead of running the entire workflow again, just run the content writer directly
        # print(f"Debug: Running content writer with choice: {user_choice}")
        from src.nodes.content_writer_node import content_writer_node
        
        # Create the state for content writing
        content_state = {
            "topic": topic,
            "scraped_content": result.get("scraped_content", []),
            "selected_idea": selected_idea,
            "workflow_status": "idea_selected"
        }
        
        # Run content writer directly
        content_result = content_writer_node(content_state)
        result.update(content_result)
        # print(f"Debug: Content writer completed with status: {content_result.get('workflow_status')}")
        
        # Run image generation if content writing was successful
        if content_result.get("workflow_status") == "writing_completed":
            # print("Debug: Running image generation...")
            from src.nodes.image_generation_node import image_generation_node
            
            # Create the state for image generation
            image_state = {
                "topic": topic,
                "linkedin_post": content_result.get("linkedin_post"),
                "selected_idea": selected_idea,
                "workflow_status": "writing_completed"
            }
            
            # Run image generation directly
            image_result = image_generation_node(image_state)
            result.update(image_result)
            # print(f"Debug: Image generation completed with status: {image_result.get('workflow_status')}")

            # After both content and image are generated, save to PDF
            if image_result.get("workflow_status") == "imaging_completed":
                from src.utils_save_output import save_content_and_image_to_pdf
                linkedin_post = result.get("linkedin_post")
                generated_image = result.get("generated_image")
                if linkedin_post and generated_image:
                    # Combine content and hashtags
                    content = f"{linkedin_post.title}\n\n{linkedin_post.content}\n\nHashtags: {' '.join(linkedin_post.hashtags)}\n\nCall to Action: {linkedin_post.call_to_action}"
                    image_path = generated_image.image_path
                    # Sanitize topic for filename
                    import re
                    safe_topic = re.sub(r'[^a-zA-Z0-9_\-]', '_', topic)[:40]
                    output_pdf = f"outputs/linkedin_content_{safe_topic}.pdf"
                    save_content_and_image_to_pdf(content, image_path, output_pdf)
                    # Prompt user for next action
                    while True:
                        user_action = input("\nDo you want to post this content to LinkedIn or regenerate the content? (Type 'post' to post, 'regenerate' to regenerate): ").strip().lower()
                        if user_action in ['post', 'regenerate']:
                            break
                        print("Please type 'post' or 'regenerate'.")
                    if user_action == 'post':
                        # Call LinkedIn posting node (to be implemented)
                        from src.nodes.linkedin_posting_node import linkedin_posting_node
                        post_state = {
                            "linkedin_post": linkedin_post,
                            "generated_image": generated_image,
                            "topic": topic,
                            "workflow_status": "ready_to_post"
                        }
                        post_result = linkedin_posting_node(post_state)
                        result.update(post_result)
                    elif user_action == 'regenerate':
                        # Rerun content writer and image generation
                        print("\nRegenerating content...")
                        from src.nodes.content_writer_node import content_writer_node
                        content_state = {
                            "topic": topic,
                            "scraped_content": result.get("scraped_content", []),
                            "selected_idea": selected_idea,
                            "workflow_status": "idea_selected"
                        }
                        content_result = content_writer_node(content_state)
                        result.update(content_result)
                        if content_result.get("workflow_status") == "writing_completed":
                            from src.nodes.image_generation_node import image_generation_node
                            image_state = {
                                "topic": topic,
                                "linkedin_post": content_result.get("linkedin_post"),
                                "selected_idea": selected_idea,
                                "workflow_status": "writing_completed"
                            }
                            image_result = image_generation_node(image_state)
                            result.update(image_result)
                            if image_result.get("workflow_status") == "imaging_completed":
                                linkedin_post = result.get("linkedin_post")
                                generated_image = result.get("generated_image")
                                content = f"{linkedin_post.title}\n\n{linkedin_post.content}\n\nHashtags: {' '.join(linkedin_post.hashtags)}\n\nCall to Action: {linkedin_post.call_to_action}"
                                image_path = generated_image.image_path
                                import re
                                safe_topic = re.sub(r'[^a-zA-Z0-9_\-]', '_', topic)[:40]
                                output_pdf = f"outputs/linkedin_content_{safe_topic}.pdf"
                                save_content_and_image_to_pdf(content, image_path, output_pdf)
                                print(f"\nRegenerated content and PDF saved to {output_pdf}.")
                                # Optionally, you could loop back to ask again

    return result


if __name__ == "__main__":
    # Example usage with interactive choice
    topic = "artificial intelligence in business"
    result = run_linkedin_agent_interactive(topic)
    
    # print(f"\nWorkflow completed with status: {result['workflow_status']}")
    # print(f"Scraped {len(result['scraped_content'])} pieces of content")
    
    # Display final results
    # if result.get("linkedin_post"):
    #     print("\n" + "="*50)
    #     print("GENERATED LINKEDIN POST")
    #     print("="*50)
    #     post = result["linkedin_post"]
    #     print(f"Title: {post.title}")
    #     print(f"Content: {post.content}")
    #     print(f"Hashtags: {' '.join(post.hashtags)}")
    #     print(f"Call to Action: {post.call_to_action}")
    #     print(f"Estimated Engagement: {post.estimated_engagement}")
        
        # Display generated image information
    # if result.get("generated_image"):
    #     print("\n" + "="*50)
    #     print("GENERATED IMAGE")
    #     print("="*50)
    #     image = result["generated_image"]
    #     print(f"Image Path: {image.image_path}")
    #     print(f"Description: {image.image_description}")
    #     print(f"Prompt Used: {image.prompt_used[:100]}...")
    
    # Display scraped content summary
    # for i, content in enumerate(result['scraped_content']):
    #     print(f"\nContent {i+1}:")
    #     print(f"Source: {content.source_type}")
    #     print(f"Title: {content.title}")
    #     print(f"URL: {content.source_url}")
    #     print(f"Content length: {len(content.content)} characters")
    #     if content.transcript:
    #         print(f"Transcript length: {len(content.transcript)} characters") 