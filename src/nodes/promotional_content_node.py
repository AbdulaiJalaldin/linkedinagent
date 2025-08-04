"""
Promotional Content Generation Node for LinkedIn Content Automation Agent
Generates promotional LinkedIn content using AI
"""
import os
import re
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from src.state import State, LinkedInPost


def promotional_content_node(state: State) -> Dict[str, Any]:
    """
    Promotional Content Generation node that creates LinkedIn posts for product promotion.
    
    Args:
        state: Current workflow state with product data
        
    Returns:
        Updated state with generated LinkedIn post
    """
    # Get Groq API key from environment
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    # Get product data
    product_data = state.get("product_data")
    if not product_data:
        return {
            "workflow_status": "failed",
            "error_message": "No product data available for content generation",
            "messages": [
                {
                    "role": "system",
                    "content": "No product data available for content generation"
                }
            ]
        }
    
    try:
        # Update status to in progress
        state["promotion_status"] = "generating_content"
        
        # Initialize Groq LLM
        llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.8
        )
        
        # Prepare context for content generation
        context = prepare_promotion_context(product_data)
        
        # Generate content using LLM
        system_prompt = """You are an expert LinkedIn content writer and marketing strategist. Your task is to create an engaging, professional LinkedIn post that promotes a work, product, or project.

LINKEDIN PROMOTIONAL POST GUIDELINES:
1. Hook: Start with a compelling hook that grabs attention
2. Storytelling: Use storytelling to make the promotion relatable
3. Value Proposition: Clearly communicate the value and benefits
4. Professional Tone: Maintain professional yet conversational tone
5. Social Proof: Include credibility elements when possible
6. Call-to-Action: End with a clear, engaging call-to-action
7. Hashtags: Include 3-5 relevant hashtags at the end
8. Length: Aim for 800-1200 characters (LinkedIn's sweet spot)

POST STRUCTURE:
- Hook (attention-grabbing opening)
- Problem/Challenge the product solves
- Solution/Product introduction
- Key benefits and features
- Social proof or credibility
- Call-to-action
- Hashtags

ENGAGEMENT TIPS:
- Ask questions to encourage comments
- Use numbers and specific details
- Include personal insights or experiences
- Make it shareable and valuable
- Use emojis sparingly but effectively
- Write in a conversational, natural tone
- Focus on providing real value to the audience

IMPORTANT: Write the post exactly as you would publish it on LinkedIn. Do not use any special formatting, JSON, or technical syntax - just write a natural, engaging LinkedIn post."""

        user_prompt = f"""Please create an engaging LinkedIn promotional post based on the following product/work information:

{context}

Write the post exactly as you would publish it on LinkedIn. Include:
- A catchy title/hook
- The main promotional content with proper formatting
- A clear call-to-action
- Relevant hashtags at the end

Focus on creating a post that would resonate with {product_data.target_audience} and effectively promote {product_data.name}.

Write the post in natural, human-readable format - no JSON or special formatting."""

        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Get LLM response
        response = llm.invoke(messages)
        
        # Parse the response and create LinkedInPost object
        try:
            response_text = response.content.strip()
            lines = response_text.split('\n')
            
            # Extract title from the first line
            title = lines[0].strip() if lines else product_data.name
            
            # Extract hashtags and content
            hashtags = []
            content_lines = []
            
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if line contains hashtags
                if line.startswith('#') or '#' in line:
                    hashtag_matches = re.findall(r'#\w+', line)
                    hashtags.extend(hashtag_matches)
                    content_line = re.sub(r'#\w+', '', line).strip()
                    if content_line:
                        content_lines.append(content_line)
                else:
                    content_lines.append(line)
            
            # Join content lines
            content = '\n'.join(content_lines).strip()
            
            # If no content was extracted, use the full response minus title
            if not content:
                content = '\n'.join(lines[1:]).strip()
            
            # If still no content, use the full response
            if not content:
                content = response_text
            
            # Generate hashtags if none were found
            if not hashtags:
                hashtags = [
                    f"#{re.sub(r'[^a-zA-Z0-9]', '', word).lower()}" 
                    for word in product_data.name.split()[:3]
                ]
            
            # Create LinkedInPost object
            post = LinkedInPost(
                title=title,
                content=content,
                hashtags=hashtags,
                call_to_action=product_data.call_to_action,
                estimated_engagement="High"
            )
            
            return {
                "linkedin_post": post,
                "promotion_status": "generating_content",
                "workflow_status": "promotion",
                "messages": [
                    {
                        "role": "system",
                        "content": f"Successfully created promotional LinkedIn post for: {product_data.name}"
                    }
                ]
            }
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            # Create fallback post
            return create_fallback_promotional_post(product_data)
        
    except Exception as e:
        error_msg = f"Error during promotional content generation: {str(e)}"
        return {
            "linkedin_post": None,
            "promotion_status": "failed",
            "workflow_status": "failed",
            "error_message": error_msg,
            "messages": [
                {
                    "role": "system",
                    "content": f"Promotional content generation failed: {error_msg}"
                }
            ]
        }


def prepare_promotion_context(product_data) -> str:
    """
    Prepare context for promotional content generation.
    
    Args:
        product_data: ProductPromotionData object
        
    Returns:
        Formatted context string
    """
    context_parts = []
    context_parts.append(f"PRODUCT/WORK NAME: {product_data.name}")
    context_parts.append(f"DESCRIPTION: {product_data.description}")
    
    if product_data.features:
        context_parts.append(f"KEY FEATURES:")
        for i, feature in enumerate(product_data.features, 1):
            context_parts.append(f"  {i}. {feature}")
    
    if product_data.benefits:
        context_parts.append(f"KEY BENEFITS:")
        for i, benefit in enumerate(product_data.benefits, 1):
            context_parts.append(f"  {i}. {benefit}")
    
    context_parts.append(f"TARGET AUDIENCE: {product_data.target_audience}")
    context_parts.append(f"CALL TO ACTION: {product_data.call_to_action}")
    
    if product_data.website:
        context_parts.append(f"WEBSITE: {product_data.website}")
    
    if product_data.contact_info:
        context_parts.append(f"CONTACT INFO: {product_data.contact_info}")
    
    if product_data.additional_info:
        context_parts.append(f"ADDITIONAL INFORMATION: {product_data.additional_info}")
    
    return "\n".join(context_parts)


def create_fallback_promotional_post(product_data) -> Dict[str, Any]:
    """
    Create fallback promotional post when LLM parsing fails.
    
    Args:
        product_data: ProductPromotionData object
        
    Returns:
        Dictionary with fallback LinkedInPost
    """
    title = f"🚀 Introducing {product_data.name}"
    
    content_parts = []
    content_parts.append(f"I'm excited to share {product_data.name} with you!")
    
    if product_data.description:
        content_parts.append(f"\n{product_data.description}")
    
    if product_data.features:
        content_parts.append("\n✨ Key Features:")
        for feature in product_data.features[:3]:  # Limit to 3 features
            content_parts.append(f"• {feature}")
    
    if product_data.benefits:
        content_parts.append("\n🎯 Benefits:")
        for benefit in product_data.benefits[:3]:  # Limit to 3 benefits
            content_parts.append(f"• {benefit}")
    
    content_parts.append(f"\n👥 Perfect for: {product_data.target_audience}")
    
    if product_data.website:
        content_parts.append(f"\n🌐 Learn more: {product_data.website}")
    
    content = "\n".join(content_parts)
    
    hashtags = [
        f"#{re.sub(r'[^a-zA-Z0-9]', '', word).lower()}" 
        for word in product_data.name.split()[:3]
    ]
    
    post = LinkedInPost(
        title=title,
        content=content,
        hashtags=hashtags,
        call_to_action=product_data.call_to_action,
        estimated_engagement="Medium"
    )
    
    return {
        "linkedin_post": post,
        "promotion_status": "generating_content",
        "workflow_status": "promotion",
        "messages": [
            {
                "role": "system",
                "content": f"Created fallback promotional post for: {product_data.name}"
            }
        ]
    } 