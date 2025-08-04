"""
PDF Generation Node for LinkedIn Content Automation Agent
Creates PDF documents with promotional content and images
"""
import os
from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from src.state import State


def pdf_generation_node(state: State) -> Dict[str, Any]:
    """
    PDF Generation node that creates PDF documents with promotional content and images.
    
    Args:
        state: Current workflow state with LinkedIn post and images
        
    Returns:
        Updated state with PDF file path
    """
    # Get data from state
    linkedin_post = state.get("linkedin_post")
    product_data = state.get("product_data")
    uploaded_images = state.get("uploaded_images", [])
    
    if not linkedin_post:
        return {
            "workflow_status": "failed",
            "error_message": "No LinkedIn post available for PDF generation",
            "messages": [
                {
                    "role": "system",
                    "content": "No LinkedIn post available for PDF generation"
                }
            ]
        }
    
    try:
        # Update status to in progress
        state["promotion_status"] = "creating_pdf"
        
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate PDF filename
        if product_data:
            pdf_filename = f"promotional_content_{product_data.name.replace(' ', '_').lower()}.pdf"
        else:
            pdf_filename = f"linkedin_promotional_content.pdf"
        
        pdf_path = output_dir / pdf_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=1  # Center alignment
        )
        
        # Add title
        story.append(Paragraph("LinkedIn Promotional Content", title_style))
        story.append(Spacer(1, 20))
        
        # Add product information if available
        if product_data:
            story.append(Paragraph(f"<b>Product/Work:</b> {product_data.name}", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            if product_data.description:
                story.append(Paragraph(f"<b>Description:</b> {product_data.description}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Add features
            if product_data.features:
                story.append(Paragraph("<b>Key Features:</b>", styles['Heading3']))
                for feature in product_data.features:
                    story.append(Paragraph(f"• {feature}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Add benefits
            if product_data.benefits:
                story.append(Paragraph("<b>Key Benefits:</b>", styles['Heading3']))
                for benefit in product_data.benefits:
                    story.append(Paragraph(f"• {benefit}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"<b>Target Audience:</b> {product_data.target_audience}", styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Add LinkedIn post content
        story.append(Paragraph("<b>LinkedIn Post Content:</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"<b>Title:</b> {linkedin_post.title}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Split content into paragraphs
        content_paragraphs = linkedin_post.content.split('\n\n')
        for paragraph in content_paragraphs:
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), styles['Normal']))
                story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Call to Action:</b> {linkedin_post.call_to_action}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"<b>Hashtags:</b> {' '.join(linkedin_post.hashtags)}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add images
        if uploaded_images:
            story.append(Paragraph("<b>Promotional Images:</b>", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            for i, uploaded_image in enumerate(uploaded_images, 1):
                try:
                    # Add image to PDF
                    img = RLImage(uploaded_image.file_path, width=4*inch, height=3*inch)
                    story.append(img)
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(f"Image {i}: {uploaded_image.file_name}", styles['Normal']))
                    story.append(Spacer(1, 10))
                except Exception as e:
                    print(f"Warning: Could not add image {uploaded_image.file_path} to PDF: {e}")
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ PDF created: {pdf_path}")
        
        return {
            "pdf_path": str(pdf_path),
            "promotion_status": "creating_pdf",
            "workflow_status": "promotion",
            "messages": [
                {
                    "role": "system",
                    "content": f"Successfully created PDF: {pdf_path}"
                }
            ]
        }
        
    except Exception as e:
        error_msg = f"Error during PDF generation: {str(e)}"
        return {
            "pdf_path": None,
            "promotion_status": "failed",
            "workflow_status": "failed",
            "error_message": error_msg,
            "messages": [
                {
                    "role": "system",
                    "content": f"PDF generation failed: {error_msg}"
                }
            ]
        } 