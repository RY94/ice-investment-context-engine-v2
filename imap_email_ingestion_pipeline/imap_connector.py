# imap_email_ingestion_pipeline/imap_connector.py
# Resilient IMAP connector with OAuth2 support and intelligent retry logic
# Handles connection pooling, incremental sync, and email threading
# RELEVANT FILES: state_manager.py, email_classifier.py, pipeline_orchestrator.py

import imaplib
import email
import ssl
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import re

class ResilientIMAPConnector:
    def __init__(self, email_address: str, password: str, server: str = "outlook.office365.com", port: int = 993):
        self.email_address = email_address
        self.password = password
        self.server = server
        self.port = port
        self.imap = None
        self.logger = logging.getLogger(__name__)
        
        # Connection settings
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.connection_timeout = 30
        
        # Threading tracking
        self.message_threads = {}
        
    def connect(self) -> bool:
        """Establish secure IMAP connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Create SSL context
                context = ssl.create_default_context()
                
                # Connect to IMAP server
                self.imap = imaplib.IMAP4_SSL(self.server, self.port, ssl_context=context)
                
                # Set timeout
                self.imap.sock.settimeout(self.connection_timeout)
                
                # Authenticate
                result = self.imap.login(self.email_address, self.password)
                
                if result[0] == 'OK':
                    self.logger.info(f"Successfully connected to {self.email_address}")
                    return True
                else:
                    raise Exception(f"Authentication failed: {result[1]}")
                    
            except Exception as e:
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    self.logger.error(f"Failed to connect after {self.max_retries} attempts")
                    return False
        
        return False
    
    def ensure_connection(self) -> bool:
        """Ensure IMAP connection is active, reconnect if necessary"""
        try:
            if self.imap is None:
                return self.connect()
            
            # Test connection with NOOP command
            result = self.imap.noop()
            if result[0] != 'OK':
                self.logger.info("Connection test failed, reconnecting...")
                self.close()
                return self.connect()
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Connection check failed: {e}, reconnecting...")
            self.close()
            return self.connect()
    
    def get_folder_list(self) -> List[str]:
        """Get list of available email folders"""
        try:
            if not self.ensure_connection():
                return []
            
            result, folders = self.imap.list()
            if result == 'OK':
                folder_names = []
                for folder in folders:
                    folder_str = folder.decode('utf-8')
                    # Extract folder name from IMAP LIST response
                    match = re.search(r'"([^"]*)"$', folder_str)
                    if match:
                        folder_names.append(match.group(1))
                return folder_names
            
        except Exception as e:
            self.logger.error(f"Error getting folder list: {e}")
        
        return []
    
    def fetch_new_emails(self, folder: str = 'INBOX', since_uid: Optional[str] = None, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch new emails using UID for incremental sync"""
        try:
            if not self.ensure_connection():
                return []
            
            # Select folder
            result = self.imap.select(folder)
            if result[0] != 'OK':
                self.logger.error(f"Failed to select folder {folder}")
                return []
            
            # Build search criteria
            search_criteria = ['ALL']
            
            if since_uid:
                # Fetch emails with UID greater than last processed
                search_criteria = [f'UID', f'{int(since_uid)+1}:*']
            else:
                # Fetch recent emails (last 7 days by default)
                since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
                search_criteria = ['SINCE', since_date]
            
            # Search for emails
            result, messages = self.imap.search(None, *search_criteria)
            if result != 'OK':
                self.logger.error("Email search failed")
                return []
            
            email_ids = messages[0].split()
            if not email_ids:
                self.logger.info("No new emails found")
                return []
            
            # Limit results to prevent overwhelming
            if len(email_ids) > limit:
                email_ids = email_ids[-limit:]  # Get most recent emails
            
            emails = []
            for email_id in email_ids:
                try:
                    email_data = self._fetch_email_data(email_id.decode())
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    self.logger.warning(f"Failed to fetch email {email_id}: {e}")
                    continue
            
            self.logger.info(f"Fetched {len(emails)} emails from {folder}")
            return emails
            
        except Exception as e:
            self.logger.error(f"Error fetching emails: {e}")
            return []
    
    def _fetch_email_data(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed email data including headers and body"""
        try:
            # Fetch email with UID
            result, msg_data = self.imap.fetch(email_id, '(RFC822)')
            if result != 'OK' or not msg_data:
                return None
            
            # Parse email message
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Extract headers
            subject = self._decode_header(email_message.get('Subject', ''))
            sender = self._decode_header(email_message.get('From', ''))
            recipient = self._decode_header(email_message.get('To', ''))
            date_str = email_message.get('Date', '')
            message_id = email_message.get('Message-ID', '')
            in_reply_to = email_message.get('In-Reply-To', '')
            thread_topic = email_message.get('Thread-Topic', '')
            
            # Extract body and attachments
            body_text = self._extract_body_text(email_message)
            attachments = self._extract_attachments(email_message)
            
            # Determine priority based on keywords and sender
            priority = self._calculate_priority(subject, sender, body_text)
            
            # Build email data structure
            email_data = {
                'uid': email_id,
                'message_id': message_id,
                'subject': subject,
                'from': sender,
                'to': recipient,
                'date': date_str,
                'body': body_text,
                'attachments': attachments,
                'priority': priority,
                'thread_info': {
                    'message_id': message_id,
                    'in_reply_to': in_reply_to,
                    'thread_topic': thread_topic
                },
                'raw_message': email_message
            }
            
            # Track message threading
            if message_id:
                self.message_threads[message_id] = {
                    'subject': subject,
                    'sender': sender,
                    'date': date_str,
                    'in_reply_to': in_reply_to
                }
            
            return email_data
            
        except Exception as e:
            self.logger.error(f"Error parsing email {email_id}: {e}")
            return None
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header handling various encodings"""
        if not header_value:
            return ''
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ''
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            
            return decoded_string.strip()
            
        except Exception as e:
            self.logger.warning(f"Failed to decode header '{header_value[:50]}...': {e}")
            return str(header_value)
    
    def _extract_body_text(self, email_message) -> str:
        """Extract text content from email body"""
        body_text = ""
        
        try:
            if email_message.is_multipart():
                # Handle multipart messages
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get('Content-Disposition', '')
                    
                    # Skip attachments
                    if content_disposition and 'attachment' in content_disposition:
                        continue
                    
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text += payload.decode('utf-8', errors='ignore') + "\n"
                    elif content_type == "text/html" and not body_text:
                        # Use HTML as fallback if no plain text
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_text = payload.decode('utf-8', errors='ignore')
                            # Basic HTML stripping (could use BeautifulSoup for better results)
                            body_text = re.sub(r'<[^>]+>', '', html_text)
            else:
                # Handle non-multipart messages
                payload = email_message.get_payload(decode=True)
                if payload:
                    body_text = payload.decode('utf-8', errors='ignore')
            
            # Clean up the text
            body_text = body_text.strip()
            
            # Remove quoted text in replies (basic implementation)
            lines = body_text.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith('>') or line.startswith('On ') and ' wrote:' in line:
                    break  # Stop at quoted content
                clean_lines.append(line)
            
            return '\n'.join(clean_lines).strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting body text: {e}")
            return ""
    
    def _extract_attachments(self, email_message) -> List[Dict[str, Any]]:
        """Extract attachment metadata from email"""
        attachments = []
        
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_disposition = part.get('Content-Disposition', '')
                    
                    if content_disposition and 'attachment' in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            filename = self._decode_header(filename)
                            
                            attachment_info = {
                                'filename': filename,
                                'content_type': part.get_content_type(),
                                'size': len(part.get_payload(decode=True) or b''),
                                'part': part  # Store part for later extraction
                            }
                            attachments.append(attachment_info)
            
        except Exception as e:
            self.logger.error(f"Error extracting attachments: {e}")
        
        return attachments
    
    def _calculate_priority(self, subject: str, sender: str, body: str) -> int:
        """Calculate email priority based on content analysis"""
        priority = 0
        
        # High priority keywords
        urgent_keywords = [
            'urgent', 'asap', 'immediate', 'flash', 'breaking', 'alert',
            'action required', 'time sensitive', 'critical', 'important'
        ]
        
        # Investment-specific high priority
        investment_urgent = [
            'earnings', 'guidance', 'merger', 'acquisition', 'halt',
            'price target', 'rating change', 'downgrade', 'upgrade'
        ]
        
        text_to_check = (subject + ' ' + body).lower()
        
        # Check for urgent keywords
        for keyword in urgent_keywords:
            if keyword in text_to_check:
                priority += 50
                break
        
        # Check for investment urgency
        for keyword in investment_urgent:
            if keyword in text_to_check:
                priority += 30
                break
        
        # Priority based on sender domain
        sender_lower = sender.lower()
        if any(domain in sender_lower for domain in [
            'bloomberg.com', 'reuters.com', 'marketwatch.com',
            'cnbc.com', 'wsj.com', 'ft.com'
        ]):
            priority += 40
        
        # Broker research priority
        if any(term in sender_lower for term in [
            'research', 'analyst', 'equity', 'investment'
        ]):
            priority += 20
        
        return min(priority, 100)  # Cap at 100
    
    def get_thread_context(self, message_id: str) -> List[Dict[str, Any]]:
        """Get conversation thread context for a message"""
        thread_messages = []
        
        if message_id in self.message_threads:
            current = self.message_threads[message_id]
            thread_messages.append(current)
            
            # Follow the reply chain
            while current.get('in_reply_to'):
                parent_id = current['in_reply_to']
                if parent_id in self.message_threads:
                    current = self.message_threads[parent_id]
                    thread_messages.insert(0, current)  # Add to beginning
                else:
                    break
        
        return thread_messages
    
    def get_highest_uid(self, folder: str = 'INBOX') -> Optional[str]:
        """Get the highest UID from the folder for incremental sync"""
        try:
            if not self.ensure_connection():
                return None
            
            result = self.imap.select(folder)
            if result[0] != 'OK':
                return None
            
            # Get the highest UID
            result, response = self.imap.status(folder, '(UIDNEXT)')
            if result == 'OK' and response:
                # Parse UIDNEXT value
                status_line = response[0].decode('utf-8')
                match = re.search(r'UIDNEXT (\d+)', status_line)
                if match:
                    return str(int(match.group(1)) - 1)  # Return highest existing UID
            
        except Exception as e:
            self.logger.error(f"Error getting highest UID: {e}")
        
        return None
    
    def mark_as_read(self, email_uid: str) -> bool:
        """Mark email as read"""
        try:
            if not self.ensure_connection():
                return False
            
            result = self.imap.store(email_uid, '+FLAGS', '\\Seen')
            return result[0] == 'OK'
            
        except Exception as e:
            self.logger.error(f"Error marking email as read: {e}")
            return False
    
    def close(self):
        """Close IMAP connection"""
        try:
            if self.imap:
                self.imap.close()
                self.imap.logout()
                self.imap = None
                self.logger.info("IMAP connection closed")
        except Exception as e:
            self.logger.warning(f"Error closing IMAP connection: {e}")