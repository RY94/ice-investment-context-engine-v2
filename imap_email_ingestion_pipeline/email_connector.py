# imap_email_ingestion_pipeline/email_connector.py
# IMAP email connection handler for ICE system
# Connects to Outlook IMAP and fetches emails
# RELEVANT FILES: ice_lightrag/ice_rag.py, simple_demo.py

import imaplib
import email
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import ssl
import logging

class EmailConnector:
    def __init__(self, email_address: str, password: str):
        self.email = email_address
        self.password = password
        self.imap = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """Connect to Outlook IMAP server"""
        try:
            # Outlook IMAP settings
            imap_server = "outlook.office365.com"
            imap_port = 993
            
            self.imap = imaplib.IMAP4_SSL(imap_server, imap_port)
            self.imap.login(self.email, self.password)
            self.logger.info(f"Connected to {self.email}")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def fetch_recent_emails(self, folder='INBOX', limit=10) -> List[Dict[str, Any]]:
        """Fetch recent emails from specified folder"""
        if not self.imap:
            if not self.connect():
                return []
        
        try:
            self.imap.select(folder)
            
            # Search for all emails, get most recent
            status, messages = self.imap.search(None, 'ALL')
            email_ids = messages[0].split()[-limit:]  # Get last N emails
            
            emails = []
            for email_id in email_ids:
                status, msg_data = self.imap.fetch(email_id, '(RFC822)')
                email_message = email.message_from_bytes(msg_data[0][1])
                
                # Extract basic info
                email_info = {
                    'id': email_id.decode(),
                    'subject': email_message.get('Subject', ''),
                    'from': email_message.get('From', ''),
                    'date': email_message.get('Date', ''),
                    'body': self._extract_body(email_message),
                    'raw_message': email_message
                }
                emails.append(email_info)
            
            return emails
        
        except Exception as e:
            self.logger.error(f"Fetch failed: {e}")
            return []
    
    def _extract_body(self, email_message) -> str:
        """Extract email body text"""
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode('utf-8', errors='ignore')
        else:
            payload = email_message.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        return body.strip()
    
    def close(self):
        """Close IMAP connection"""
        if self.imap:
            self.imap.close()
            self.imap.logout()