# imap_email_ingestion_pipeline/imap_connector_ice_data.py
"""
IMAP Email Connector for ICE Investment Context Engine (Legacy version from ice_data_ingestion)
Extracts and processes email data from IMAP mailboxes for investment intelligence
Originally from ice_data_ingestion/imap_connector.py - moved to consolidate email ingestion
Relevant files: email_data_model_ice_data.py, imap_connector.py (main version)
"""

import imaplib
import email
from email.header import decode_header
import getpass
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def safe_decode(text, encoding=None):
    """
    Safely decode text with fallback encodings.
    Handles different character encodings commonly found in emails.
    """
    if isinstance(text, str):
        return text
    
    # List of encodings to try (most common for emails)
    encodings_to_try = [
        encoding,  # Use specified encoding first
        'utf-8',
        'latin-1', 
        'windows-1252',
        'iso-8859-1'
    ]
    
    for enc in encodings_to_try:
        if enc is None:
            continue
        try:
            return text.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    
    # If all fail, use 'replace' to avoid errors
    return text.decode('utf-8', errors='replace')


class IMAPConnector:
    """IMAP email connector for investment data ingestion"""
    
    def __init__(self, email_address: str, imap_server: str, imap_port: int = 993):
        self.email_address = email_address
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.mail = None
        
    def connect(self, password: str) -> bool:
        """Connect to IMAP server"""
        try:
            logger.info(f"Connecting to {self.email_address} at {self.imap_server}:{self.imap_port}")
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_address, password)
            logger.info("✓ Successfully connected to IMAP server")
            return True
        except Exception as e:
            logger.error(f"❌ IMAP connection failed: {e}")
            return False
    
    def get_email_list(self, folder: str = "inbox", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of emails from specified folder"""
        emails = []
        
        try:
            # Select the folder
            self.mail.select(folder)
            
            # Search for all emails
            status, messages = self.mail.search(None, "ALL")
            email_ids = messages[0].split()
            
            # Apply limit if specified
            if limit:
                email_ids = email_ids[-limit:]
            
            logger.info(f"Processing {len(email_ids)} emails from {folder}")
            
            # Read each email with proper encoding handling
            for i, email_id in enumerate(reversed(email_ids), 1):
                try:
                    # Fetch the email
                    status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Extract subject with proper encoding handling
                    subject_header = email_message["Subject"]
                    if subject_header:
                        decoded_parts = decode_header(subject_header)
                        subject_parts = []
                        for part, encoding in decoded_parts:
                            subject_parts.append(safe_decode(part, encoding))
                        subject = ''.join(subject_parts)
                    else:
                        subject = "(No Subject)"
                    
                    # Extract other details
                    sender = email_message["From"] or "(Unknown Sender)"
                    date = email_message["Date"] or "(Unknown Date)"
                    
                    # Get email body
                    body = ""
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = safe_decode(payload)
                                break
                    else:
                        payload = email_message.get_payload(decode=True)
                        if payload:
                            body = safe_decode(payload)
                    
                    emails.append({
                        'id': email_id.decode(),
                        'subject': subject,
                        'sender': sender,
                        'date': date,
                        'body': body,
                        'raw_message': email_message
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing email {i}: {e}")
                    
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            
        return emails
    
    def disconnect(self):
        """Close IMAP connection"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                logger.info("✓ IMAP connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing IMAP connection: {e}")


def connect_to_outlook_imap(email_address: str = "roy@agtpartners.com.sg", 
                           imap_server: str = "mail.agtpartners.com.sg"):
    """Legacy function for backward compatibility"""
    password = getpass.getpass("Enter your password: ")
    
    connector = IMAPConnector(email_address, imap_server)
    if connector.connect(password):
        emails = connector.get_email_list(limit=5)
        
        print(f"\nShowing {len(emails)} most recent emails from {email_address}:\n")
        
        for i, email_data in enumerate(emails, 1):
            print(f"Email {i}:")
            print(f"  Subject: {email_data['subject']}")
            print(f"  From: {email_data['sender']}")
            print(f"  Date: {email_data['date']}")
            print("-" * 50)
        
        connector.disconnect()


if __name__ == "__main__":
    connect_to_outlook_imap()