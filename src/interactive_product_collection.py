"""
Interactive Product Information Collection for Slack
Asks product information questions one by one in a conversational manner
"""
from src.state import State, ProductPromotionData
from typing import Dict, Any, List

class ProductInfoCollector:
    """Interactive product information collector"""
    
    def __init__(self):
        self.questions = [
            {
                "key": "name",
                "question": "What's the name of your product or service?",
                "required": True
            },
            {
                "key": "description", 
                "question": "Please describe what your product/service does in 1-2 sentences:",
                "required": True
            },
            {
                "key": "target_audience",
                "question": "Who is your target audience? (e.g., business owners, developers, students):",
                "required": True
            },
            {
                "key": "features",
                "question": "What are the key features of your product? (separate with commas):",
                "required": False
            },
            {
                "key": "benefits",
                "question": "What are the main benefits users get from your product? (separate with commas):",
                "required": False
            },
            {
                "key": "call_to_action",
                "question": "What would you like people to do? (e.g., 'Try it free', 'Contact us', 'Learn more') or type 'skip' to skip:",
                "required": False
            },
            {
                "key": "website",
                "question": "Do you have a website? (optional - type 'skip' to skip):",
                "required": False
            },
            {
                "key": "contact",
                "question": "How can people contact you? (optional - type 'skip' to skip):",
                "required": False
            }
        ]
    
    def get_current_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current question based on session progress"""
        current_step = session.get("product_info_step", 0)
        
        if current_step >= len(self.questions):
            return None  # All questions completed
        
        return self.questions[current_step]
    
    def process_answer(self, session: Dict[str, Any], answer: str) -> Dict[str, Any]:
        """Process user's answer and move to next question"""
        current_step = session.get("product_info_step", 0)
        
        if current_step >= len(self.questions):
            return {"status": "completed", "message": "All questions completed"}
        
        current_question = self.questions[current_step]
        key = current_question["key"]
        
        # Store the answer
        if "product_info_answers" not in session:
            session["product_info_answers"] = {}
        
        # Process special cases
        if key in ["features", "benefits"] and answer.strip():
            # Split by commas and clean up
            items = [item.strip() for item in answer.split(",") if item.strip()]
            session["product_info_answers"][key] = items
        else:
            session["product_info_answers"][key] = answer.strip()
        
        # Move to next question
        session["product_info_step"] = current_step + 1
        
        # Check if we're done
        if session["product_info_step"] >= len(self.questions):
            return {"status": "completed", "message": "All questions completed"}
        else:
            next_question = self.questions[session["product_info_step"]]
            return {
                "status": "next_question",
                "question": next_question["question"],
                "required": next_question["required"]
            }
    
    def build_product_data(self, session: Dict[str, Any]) -> ProductPromotionData:
        """Build ProductPromotionData from collected answers"""
        answers = session.get("product_info_answers", {})
        
        return ProductPromotionData(
            name=answers.get("name", "Your Product"),
            description=answers.get("description", ""),
            target_audience=answers.get("target_audience", "LinkedIn audience"),
            features=answers.get("features", []),
            benefits=answers.get("benefits", []),
            call_to_action=answers.get("call_to_action", "Learn more!"),
            website=answers.get("website", ""),
            contact_info=answers.get("contact", "")
        )

def start_product_info_collection(session: Dict[str, Any]) -> str:
    """Start the product information collection process"""
    collector = ProductInfoCollector()
    first_question = collector.get_current_question(session)
    
    if first_question:
        session["product_info_collector"] = collector
        session["product_info_step"] = 0
        return f"🎯 *Let's collect information about your product!*\n\n{first_question['question']}"
    else:
        return "❌ Error: Could not start product information collection"

def process_product_info_answer(session: Dict[str, Any], answer: str) -> str:
    """Process user's answer to product information question"""
    collector = session.get("product_info_collector")
    
    if not collector:
        return "❌ Error: Product information collection not started"
    
    result = collector.process_answer(session, answer)
    
    if result["status"] == "completed":
        # Build the product data
        product_data = collector.build_product_data(session)
        session["product_data"] = product_data
        
        # Move to image upload phase
        session["type"] = "image_upload"
        session["uploaded_images"] = []
        
        return f"✅ *Product information collected successfully!*\n\n🖼️ *Image Upload Phase*\n\nYou can now upload promotional images for your product. Supported formats: JPG, PNG, GIF\n\nUpload images now, or type 'skip' to continue without images."
    
    elif result["status"] == "next_question":
        question_text = result["question"]
        required = result["required"]
        
        if required:
            return f"📝 {question_text}"
        else:
            return f"📝 {question_text} *(optional)*"
    
    else:
        return "❌ Error processing answer"

def get_collection_progress(session: Dict[str, Any]) -> Dict[str, Any]:
    """Get the current progress of product information collection"""
    current_step = session.get("product_info_step", 0)
    total_questions = 8  # Total number of questions
    
    return {
        "current_step": current_step,
        "total_questions": total_questions,
        "progress_percentage": (current_step / total_questions) * 100
    } 