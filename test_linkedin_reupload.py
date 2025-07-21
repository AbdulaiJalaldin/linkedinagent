from dotenv import load_dotenv
load_dotenv()

import os
print("LINKEDIN_ACCESS_TOKEN:", os.getenv("LINKEDIN_ACCESS_TOKEN"))
print("LINKEDIN_CLIENT_ID:", os.getenv("LINKEDIN_CLIENT_ID"))
print("LINKEDIN_CLIENT_SECRET:", os.getenv("LINKEDIN_CLIENT_SECRET"))

from src.nodes.linkedin_posting_node import linkedin_posting_node
from src.state import LinkedInPost, GeneratedImage

# === FILL THESE IN WITH YOUR PREVIOUS OUTPUT ===
image_path = r"generated_images\linkedin_image_775e681b671edc134913b1154679141c_20250717_052810.png"

linkedin_post = LinkedInPost(
    title="The Future of Learning: Harnessing AI to Enhance Human Intelligence",
    content=(
        "As we stand at the intersection of AI and human intelligence, the future of learning is being redefined. 🚀\n\n"
        "The rise of AI-driven education brings both opportunities and challenges. While it has the potential to revolutionize the way we learn, it also risks widening the gap between students who have access to these tools and those who do not.\n\n"
        "To ensure that AI enhances human intelligence without replacing it, we need to develop guidelines and regulations for its use in education. This includes leveraging AI as a tool to support teachers, rather than replacing them, and focusing on developing skills like creativity, problem-solving, and communication.\n\n"
        "Some key takeaways to consider:\n"
        "• AI can help personalize learning experiences for students\n"
        "• It can also help teachers streamline administrative tasks and focus on what matters most - teaching\n"
        "• However, we need to be aware of the potential biases and limitations of AI and take steps to mitigate them\n\n"
        "As we navigate this new landscape, it's essential to ask: how can we ensure that AI is used to augment human intelligence, rather than replace it?\n\n"
        "What are your thoughts on the future of learning in the age of AI? Share your insights and let's continue the conversation!"
    ),
    hashtags=[],  # No hashtags in main content or at the end
    call_to_action="Join the conversation and share your thoughts on how we can harness AI to enhance human intelligence in education!",
    estimated_engagement="High"
)

generated_image = GeneratedImage(
    image_path=image_path,
    image_description="Professional business illustration, the use of AI in education, modern design, clean composition, corporate style, high quality, detailed, professional color palette, technology elements, digital transformation, innovation, futuristic design, minimalist design, modern typography, professional layout, suitable for LinkedIn, business presentation style, clean background, high resolution, professional photography style, corporate aesthetic, business professional",
    prompt_used="Professional business illustration, the use of AI in education, modern design, clean composition, corporate style, high quality, detailed, professional color palette, technology elements, digital transformation, innovation, futuristic design, minimalist design, modern typography, professional layout, suitable for LinkedIn, business presentation style, clean background, high resolution, professional photography style, corporate aesthetic, business professional"
)

# Compose the state for posting
state = {
    "linkedin_post": linkedin_post,
    "generated_image": generated_image,
    "topic": "the use of AI in education",
    "workflow_status": "ready_to_post"
}

# Run the posting node
def main():
    result = linkedin_posting_node(state)
    print("\n=== POSTING RESULT (FULL DICT) ===")
    import pprint
    pprint.pprint(result)
    # Print full API error response if present
    if result.get("id") == "api_error" and "response" in result:
        print("\n--- FULL LINKEDIN API ERROR RESPONSE ---")
        pprint.pprint(result["response"])
        if isinstance(result["response"], dict):
            for k, v in result["response"].items():
                print(f"{k}: {v}")

if __name__ == "__main__":
    main() 