"""
Product Information Collection Node for LinkedIn Content Automation Agent
Collects comprehensive product/work information from the user
"""
from typing import Dict, Any
from src.state import State, ProductPromotionData


def product_info_node(state: State) -> Dict[str, Any]:
    """
    Product Information Collection node that gathers product/work details from the user.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with collected product information
    """
    print("\n" + "="*60)
    print("🚀 PRODUCT/WORK PROMOTION SETUP")
    print("="*60)
    print("Let's collect information about your work or product to create")
    print("compelling promotional content for LinkedIn.")
    print("="*60)
    
    # Collect product information
    name = input("\n📝 Product/Work Name: ").strip()
    
    print("\n📄 DESCRIPTION")
    print("Provide a detailed description of your work/product:")
    description = input("Description: ").strip()
    
    # Features
    print("\n✨ FEATURES")
    print("List the key features of your work/product (one per line, press Enter twice when done):")
    features = []
    while True:
        feature = input("Feature: ").strip()
        if not feature:
            break
        features.append(feature)
    
    # Benefits
    print("\n🎯 BENEFITS")
    print("List the benefits your work/product provides (one per line, press Enter twice when done):")
    benefits = []
    while True:
        benefit = input("Benefit: ").strip()
        if not benefit:
            break
        benefits.append(benefit)
    
    # Target audience
    print("\n👥 TARGET AUDIENCE")
    target_audience = input("Who is your target audience? ").strip()
    
    # Call to action
    print("\n📞 CALL TO ACTION")
    call_to_action = input("What action do you want people to take? ").strip()
    
    # Additional information
    print("\n🌐 ADDITIONAL INFORMATION")
    website = input("Website URL (optional): ").strip()
    contact_info = input("Contact information (optional): ").strip()
    
    print("\n📋 ADDITIONAL DETAILS")
    print("Any other information you'd like to include:")
    additional_info = input("Additional info: ").strip()
    
    # Create ProductPromotionData object
    product_data = ProductPromotionData(
        name=name,
        description=description,
        features=features,
        benefits=benefits,
        target_audience=target_audience,
        call_to_action=call_to_action,
        website=website if website else None,
        contact_info=contact_info if contact_info else None,
        additional_info=additional_info if additional_info else None
    )
    
    return {
        "product_data": product_data,
        "promotion_status": "collecting_info",
        "workflow_status": "promotion",
        "messages": [
            {
                "role": "system",
                "content": f"Product information collected for: {name}"
            }
        ]
    } 