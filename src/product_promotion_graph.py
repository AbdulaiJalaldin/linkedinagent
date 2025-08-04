"""
Product Promotion Graph for LinkedIn Content Automation Agent
LangGraph workflow for product/work promotion content creation
"""
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from src.state import State
from src.nodes.product_info_node import product_info_node
from src.nodes.image_upload_node import image_upload_node
from src.nodes.promotional_content_node import promotional_content_node
from src.nodes.pdf_generation_node import pdf_generation_node
from src.nodes.approval_node import approval_node
from src.nodes.linkedin_posting_node import linkedin_posting_node


def create_product_promotion_graph():
    """
    Create the Product Promotion workflow graph.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("product_info", product_info_node)
    workflow.add_node("image_upload", image_upload_node)
    workflow.add_node("promotional_content", promotional_content_node)
    workflow.add_node("pdf_generation", pdf_generation_node)
    workflow.add_node("approval", approval_node)
    workflow.add_node("linkedin_posting", linkedin_posting_node)
    
    # Add edges
    workflow.add_edge("product_info", "image_upload")
    workflow.add_edge("image_upload", "promotional_content")
    workflow.add_edge("promotional_content", "pdf_generation")
    workflow.add_edge("pdf_generation", "approval")
    
    # Add conditional routing after approval node
    def route_after_approval(state):
        """Route to LinkedIn posting if approved, otherwise end"""
        if state.get("user_approval") is True:
            return "linkedin_posting"
        else:
            return "__end__"  # End the workflow
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "linkedin_posting": "linkedin_posting",
            "__end__": "__end__"  # This will end the workflow
        }
    )
    
    # Set entry point
    workflow.set_entry_point("product_info")
    
    # Compile the graph
    return workflow.compile()


def run_product_promotion_workflow():
    """
    Run the complete product promotion workflow.
    
    Returns:
        The final state of the workflow
    """
    # Create the graph
    graph = create_product_promotion_graph()
    
    # Prepare initial input
    inputs = {
        "topic": "product_promotion",  # Placeholder topic for product promotion
        "messages": [
            {
                "role": "user",
                "content": "Create promotional LinkedIn content for a product or work"
            }
        ],
        "workflow_status": "promotion",
        "promotion_status": "pending"
    }
    
    # Run the workflow
    result = graph.invoke(inputs)
    
    return result


def run_product_promotion_interactive():
    """
    Run the product promotion workflow with interactive user input.
    
    Returns:
        The final state of the workflow
    """
    print("\n" + "="*60)
    print("🚀 PRODUCT/WORK PROMOTION WORKFLOW")
    print("="*60)
    print("This workflow will help you create promotional LinkedIn content by:")
    print("1. Collecting product/work information")
    print("2. Uploading promotional images")
    print("3. Generating professional LinkedIn posts")
    print("4. Creating PDF with content and images")
    print("5. Getting your approval")
    print("6. Auto-posting to LinkedIn")
    print("="*60)
    
    try:
        # Run the workflow
        result = run_product_promotion_workflow()
        
        # Display results
        print("\n" + "="*60)
        print("WORKFLOW COMPLETED")
        print("="*60)
        
        status = result.get("workflow_status", "unknown")
        print(f"Status: {status}")
        
        if status == "completed":
            print("✅ Product promotion workflow completed successfully!")
            
            # Display posting results
            if result.get("linkedin_post_id"):
                print(f"📝 Post ID: {result['linkedin_post_id']}")
            
            # Display the generated LinkedIn post
            if result.get("linkedin_post"):
                post = result["linkedin_post"]
                print("\n" + "="*60)
                print("YOUR LINKEDIN POST")
                print("="*60)
                print(f"Title: {post.title}")
                print("\nContent:")
                print(post.content)
                print(f"\nCall to Action: {post.call_to_action}")
                print(f"\nHashtags: {' '.join(post.hashtags)}")
                print(f"Estimated Engagement: {post.estimated_engagement}")
            
            # Display PDF information
            if result.get("pdf_path"):
                print(f"\n📄 PDF Document: {result['pdf_path']}")
            
            # Display uploaded images
            if result.get("uploaded_images"):
                print(f"\n🖼️  Uploaded Images: {len(result['uploaded_images'])} images")
                for i, img in enumerate(result['uploaded_images'], 1):
                    print(f"  {i}. {img.file_name}")
            
        elif status == "promotion":
            print("✅ Product promotion content generated!")
            
            # Display the generated LinkedIn post
            if result.get("linkedin_post"):
                post = result["linkedin_post"]
                print("\n" + "="*60)
                print("YOUR LINKEDIN POST")
                print("="*60)
                print(f"Title: {post.title}")
                print("\nContent:")
                print(post.content)
                print(f"\nCall to Action: {post.call_to_action}")
                print(f"\nHashtags: {' '.join(post.hashtags)}")
                print(f"Estimated Engagement: {post.estimated_engagement}")
            
            # Display PDF information
            if result.get("pdf_path"):
                print(f"\n📄 PDF Document: {result['pdf_path']}")
            
            # Display uploaded images
            if result.get("uploaded_images"):
                print(f"\n🖼️  Uploaded Images: {len(result['uploaded_images'])} images")
                for i, img in enumerate(result['uploaded_images'], 1):
                    print(f"  {i}. {img.file_name}")
            
        elif status == "failed":
            error_msg = result.get("error_message", "Unknown error")
            print(f"❌ Workflow failed: {error_msg}")
            return 1
        else:
            print(f"⚠️  Workflow ended with status: {status}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        import traceback
        print(f"Error type: {type(e).__name__}")
        print("Full traceback:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Example usage
    result = run_product_promotion_interactive()
    
    # Display final results
    if result.get("linkedin_post"):
        print("\n" + "="*50)
        print("GENERATED LINKEDIN POST")
        print("="*50)
        post = result["linkedin_post"]
        print(f"Title: {post.title}")
        print(f"Content: {post.content}")
        print(f"Hashtags: {' '.join(post.hashtags)}")
        print(f"Call to Action: {post.call_to_action}")
        print(f"Estimated Engagement: {post.estimated_engagement}")
    
    # Display uploaded images
    if result.get("uploaded_images"):
        print("\n" + "="*50)
        print("UPLOADED IMAGES")
        print("="*50)
        for i, img in enumerate(result['uploaded_images'], 1):
            print(f"Image {i}: {img.file_name} ({img.file_size} bytes)")
    
    # Display PDF path
    if result.get("pdf_path"):
        print(f"\n📄 PDF saved to: {result['pdf_path']}") 