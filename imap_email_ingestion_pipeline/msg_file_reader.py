# imap_email_ingestion_pipeline/msg_file_reader.py
"""
MSG File Reader for ICE Investment Context Engine
Processes Outlook .msg files to extract investment-relevant content
Originally from ice_data_ingestion/msg_file_reader.py - moved to consolidate email processing
Relevant files: email_data_model_ice_data.py, imap_connector.py, read_msg_files_python.ipynb
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import extract_msg
    EXTRACT_MSG_AVAILABLE = True
except ImportError:
    EXTRACT_MSG_AVAILABLE = False
    logger.warning("extract-msg not installed. Run: pip install extract-msg")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not installed. Run: pip install pillow")


class MSGFileReader:
    """Reader for Outlook .msg files with investment data extraction"""
    
    def __init__(self, output_folder: str = "extracted_images"):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        
        if not EXTRACT_MSG_AVAILABLE:
            raise ImportError("extract-msg library is required. Install with: pip install extract-msg")
    
    def read_msg_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read an Outlook .msg file and extract all relevant data
        
        Returns:
            Dict with email metadata, body, and attachment information
        """
        try:
            # Load the message
            msg = extract_msg.Message(file_path)
            
            # Extract basic metadata
            email_data = {
                'subject': msg.subject or '',
                'sender': msg.sender or '',
                'to': msg.to or '',
                'date': msg.date,
                'body': msg.body or '',
                'attachments': [],
                'embedded_images': [],
                'file_path': file_path
            }
            
            # Process attachments
            if msg.attachments:
                logger.info(f"Processing {len(msg.attachments)} attachments")
                
                for i, att in enumerate(msg.attachments):
                    attachment_data = {
                        'filename': att.longFilename or f'attachment_{i}',
                        'size': len(att.data) if hasattr(att, 'data') else 0,
                        'is_image': False,
                        'saved_path': None
                    }
                    
                    # Check if attachment is an image and save it
                    if hasattr(att, "data") and att.longFilename:
                        filename = att.longFilename.lower()
                        if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                            attachment_data['is_image'] = True
                            
                            try:
                                # Save the image
                                image_path = self.output_folder / att.longFilename
                                with open(image_path, 'wb') as f:
                                    f.write(att.data)
                                
                                attachment_data['saved_path'] = str(image_path)
                                logger.info(f"Saved image: {image_path}")
                                
                            except Exception as e:
                                logger.error(f"Error saving image {att.longFilename}: {e}")
                    
                    email_data['attachments'].append(attachment_data)
            
            # Extract embedded images from RTF attachments
            if hasattr(msg, "rtf_attachments") and msg.rtf_attachments:
                logger.info(f"Processing {len(msg.rtf_attachments)} embedded images")
                
                for i, (name, data) in enumerate(msg.rtf_attachments.items()):
                    try:
                        # Generate a filename for embedded images
                        image_name = f"embedded_image_{i}.png"
                        image_path = self.output_folder / image_name
                        
                        # Save the embedded image
                        with open(image_path, 'wb') as f:
                            f.write(data)
                        
                        embedded_data = {
                            'name': name or image_name,
                            'filename': image_name,
                            'saved_path': str(image_path),
                            'size': len(data)
                        }
                        
                        email_data['embedded_images'].append(embedded_data)
                        logger.info(f"Saved embedded image: {image_path}")
                        
                    except Exception as e:
                        logger.error(f"Error saving embedded image {i}: {e}")
            
            return email_data
            
        except Exception as e:
            logger.error(f"Error reading MSG file {file_path}: {e}")
            return {
                'error': str(e),
                'file_path': file_path
            }
    
    def process_msg_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Process all .msg files in a directory"""
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return []
        
        msg_files = list(directory.glob("*.msg"))
        logger.info(f"Found {len(msg_files)} MSG files in {directory_path}")
        
        results = []
        for msg_file in msg_files:
            logger.info(f"Processing: {msg_file.name}")
            email_data = self.read_msg_file(str(msg_file))
            results.append(email_data)
        
        return results
    
    def extract_investment_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract investment-relevant content from email data"""
        investment_keywords = [
            'earnings', 'results', 'financial', 'revenue', 'profit', 'loss',
            'dividend', 'share price', 'valuation', 'P/E', 'EPS', 'EBIT',
            'market cap', 'cash', 'debt', 'guidance', 'outlook'
        ]
        
        body = email_data.get('body', '').lower()
        subject = email_data.get('subject', '').lower()
        
        # Check for investment keywords
        found_keywords = []
        for keyword in investment_keywords:
            if keyword in body or keyword in subject:
                found_keywords.append(keyword)
        
        return {
            'has_investment_content': len(found_keywords) > 0,
            'investment_keywords': found_keywords,
            'investment_score': len(found_keywords) / len(investment_keywords)
        }


def read_msg_file(file_path: str) -> Dict[str, Any]:
    """Legacy function for backward compatibility"""
    reader = MSGFileReader()
    return reader.read_msg_file(file_path)


if __name__ == "__main__":
    # Example usage
    reader = MSGFileReader()
    
    # Check if the example file exists
    example_file = "Development Plan/mails files/361 Degrees International Limited FY24 Results.msg"
    if os.path.exists(example_file):
        result = reader.read_msg_file(example_file)
        print(f"Subject: {result.get('subject')}")
        print(f"From: {result.get('sender')}")
        print(f"Attachments: {len(result.get('attachments', []))}")
        print(f"Body preview: {result.get('body', '')[:200]}...")
    else:
        print(f"Example file not found: {example_file}")
        print("Place .msg files in the directory to process them.")