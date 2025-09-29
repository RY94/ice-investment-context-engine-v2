# imap_email_ingestion_pipeline/email_data_model_dev_plan.py
# Originally from Development Plan/email_data_model.py - moved to consolidate email ingestion
# Email data model for investment AI knowledge graph extraction

import json
import hashlib
import re
from datetime import datetime
from email.utils import parsedate_tz, mktime_tz
from email.header import decode_header

class EmailDataModel:
    """
    Comprehensive email data model for investment AI knowledge graph.
    Extracts ALL email information in a structured format ready for Neo4j.
    Uses existing IMAP connection code without modification.
    """
    
    def __init__(self, email_message, email_id, raw_email):
        """Initialize with email message object from existing IMAP code"""
        self.email_message = email_message
        self.email_id = email_id  
        self.raw_email = raw_email
        self.data = self._extract_all_data()
    
    def _safe_decode(self, text, encoding=None):
        """Use the same safe_decode logic from existing code"""
        if isinstance(text, str):
            return text
        
        encodings_to_try = [encoding, 'utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']
        
        for enc in encodings_to_try:
            if enc is None:
                continue
            try:
                return text.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        
        return text.decode('utf-8', errors='replace')
    
    def _extract_all_data(self):
        """Extract comprehensive email data for knowledge graph"""
        return {
            # === CORE IDENTIFIERS ===
            "email_id": str(self.email_id),
            "message_id": self._get_header("Message-ID"),
            "thread_id": self._extract_thread_id(),
            "content_hash": self._generate_content_hash(),
            
            # === TEMPORAL DATA ===
            "timestamp": self._parse_timestamp(),
            "date_sent": self._get_header("Date"),
            "timezone": self._extract_timezone(),
            
            # === PARTICIPANTS ===
            "sender": self._extract_sender(),
            "recipients": self._extract_recipients(),
            
            # === CONTENT ===
            "subject": self._extract_subject(),
            "body_text": self._extract_body_text(),
            "body_html": self._extract_body_html(),
            "language": self._detect_language(),
            
            # === EMAIL STRUCTURE ===
            "email_type": self._classify_email_type(),
            "in_reply_to": self._get_header("In-Reply-To"),
            "references": self._extract_references(),
            
            # === ATTACHMENTS ===
            "attachments": self._extract_attachments(),
            
            # === INVESTMENT ENTITIES (Pre-extracted for KG) ===
            "extracted_entities": self._extract_investment_entities(),
            
            # === METADATA ===
            "raw_headers": self._extract_all_headers(),
            "ingestion_timestamp": datetime.now().isoformat(),
            "source": "IMAP_AGT_Partners"
        }
    
    def _get_header(self, header_name):
        """Safely extract header with encoding handling"""
        header = self.email_message.get(header_name)
        if not header:
            return None
        
        try:
            decoded_parts = decode_header(header)
            parts = []
            for part, encoding in decoded_parts:
                parts.append(self._safe_decode(part, encoding))
            return ''.join(parts)
        except Exception:
            return str(header)
    
    def _extract_thread_id(self):
        """Extract conversation thread identifier"""
        thread_id = self._get_header("Thread-Topic") or self._get_header("Thread-Index")
        if not thread_id:
            # Fallback: create thread ID from subject
            subject = self._extract_subject()
            if subject:
                clean_subject = re.sub(r'^(Re:|RE:|Fwd:|FW:)\s*', '', subject, flags=re.IGNORECASE)
                return hashlib.md5(clean_subject.encode()).hexdigest()[:16]
        return thread_id
    
    def _parse_timestamp(self):
        """Parse email timestamp to ISO format"""
        date_header = self._get_header("Date")
        if not date_header:
            return None
        
        try:
            parsed_date = parsedate_tz(date_header)
            if parsed_date:
                timestamp = mktime_tz(parsed_date)
                return datetime.fromtimestamp(timestamp).isoformat()
        except Exception:
            pass
        return None
    
    def _extract_timezone(self):
        """Extract timezone from date header"""
        date_header = self._get_header("Date")
        if date_header:
            tz_match = re.search(r'([+-]\d{4})$', date_header)
            if tz_match:
                return tz_match.group(1)
        return None
    
    def _extract_sender(self):
        """Extract sender information"""
        sender = self._get_header("From")
        if not sender:
            return None
        
        # Parse email and name
        email_match = re.search(r'<([^>]+)>', sender)
        email_addr = email_match.group(1) if email_match else sender
        
        name_match = re.search(r'^[^<]*', sender)
        name = name_match.group(0).strip(' "') if name_match else ""
        
        return {
            "email": email_addr,
            "name": name,
            "domain": email_addr.split('@')[1] if '@' in email_addr else None
        }
    
    def _extract_recipients(self):
        """Extract all recipients (To, CC, BCC)"""
        recipients = []
        
        for header_type in ['To', 'Cc', 'Bcc']:
            header_value = self._get_header(header_type)
            if header_value:
                # Split by comma and extract each recipient
                for recipient in header_value.split(','):
                    recipient = recipient.strip()
                    if recipient:
                        email_match = re.search(r'<([^>]+)>', recipient)
                        email_addr = email_match.group(1) if email_match else recipient
                        
                        name_match = re.search(r'^[^<]*', recipient)
                        name = name_match.group(0).strip(' "') if name_match else ""
                        
                        recipients.append({
                            "email": email_addr,
                            "name": name,
                            "type": header_type.lower()
                        })
        
        return recipients
    
    def _extract_subject(self):
        """Extract subject with encoding handling"""
        return self._get_header("Subject") or "(No Subject)"
    
    def _extract_body_text(self):
        """Extract plain text body"""
        for part in self.email_message.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return self._safe_decode(payload)
        return ""
    
    def _extract_body_html(self):
        """Extract HTML body"""
        for part in self.email_message.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    return self._safe_decode(payload)
        return ""
    
    def _detect_language(self):
        """Simple language detection (can be enhanced)"""
        # For now, assume English for AGT Partners emails
        return "en"
    
    def _classify_email_type(self):
        """Classify email as original, reply, or forward"""
        subject = self._extract_subject()
        if re.match(r'^(Re:|RE:)', subject, re.IGNORECASE):
            return "reply"
        elif re.match(r'^(Fwd:|FW:|Forward:)', subject, re.IGNORECASE):
            return "forward"
        return "original"
    
    def _extract_references(self):
        """Extract message references for threading"""
        references = self._get_header("References")
        if references:
            return [ref.strip() for ref in references.split()]
        return []
    
    def _extract_attachments(self):
        """Extract attachment information"""
        attachments = []
        
        for part in self.email_message.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                if filename:
                    content_type = part.get_content_type()
                    payload = part.get_payload(decode=True)
                    
                    attachment_info = {
                        "filename": filename,
                        "content_type": content_type,
                        "size_bytes": len(payload) if payload else 0,
                        "content_hash": hashlib.sha256(payload).hexdigest() if payload else None
                    }
                    
                    # Extract text from common file types
                    if content_type in ['text/plain', 'text/html'] and payload:
                        attachment_info["extracted_text"] = self._safe_decode(payload)
                    
                    attachments.append(attachment_info)
        
        return attachments
    
    def _extract_investment_entities(self):
        """Extract investment-specific entities from email content"""
        full_text = f"{self._extract_subject()} {self._extract_body_text()}"
        
        # Simple regex patterns for investment entities
        companies = re.findall(r'\b[A-Z][a-zA-Z\s&]+(?:Limited|Ltd|Inc|Corp|Corporation|International|Group)\b', full_text)
        financial_metrics = re.findall(r'\b(?:EPS|P/E|ROE|ROA|EBITDA|Revenue|Market Cap|Dividend|Yield)\b', full_text, re.IGNORECASE)
        amounts = re.findall(r'[A-Z]{2,3}\$?[\d,]+\.?\d*[kmb]?', full_text)  # HK$4.60, USD123M, etc.
        dates = re.findall(r'\b(?:FY|Q[1-4])\d{2,4}\b', full_text)  # FY24, Q1 2024, etc.
        
        return {
            "companies": list(set(companies)),
            "financial_metrics": list(set(financial_metrics)),
            "amounts": list(set(amounts)),
            "dates": list(set(dates))
        }
    
    def _extract_all_headers(self):
        """Extract all email headers for complete metadata"""
        headers = {}
        for key, value in self.email_message.items():
            headers[key] = value
        return headers
    
    def _generate_content_hash(self):
        """Generate unique hash for email content"""
        content = f"{self._extract_subject()}{self._extract_body_text()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_json(self):
        """Convert to JSON for storage"""
        return json.dumps(self.data, indent=2, ensure_ascii=False)
    
    def get_kg_nodes(self):
        """Extract nodes ready for Neo4j knowledge graph"""
        nodes = []
        
        # Email node
        nodes.append({
            "type": "Email",
            "id": self.data["email_id"],
            "properties": {
                "subject": self.data["subject"],
                "timestamp": self.data["timestamp"],
                "email_type": self.data["email_type"],
                "content_hash": self.data["content_hash"]
            }
        })
        
        # Person nodes
        if self.data["sender"]:
            nodes.append({
                "type": "Person",
                "id": self.data["sender"]["email"],
                "properties": {
                    "name": self.data["sender"]["name"],
                    "email": self.data["sender"]["email"],
                    "domain": self.data["sender"]["domain"]
                }
            })
        
        # Company nodes
        for company in self.data["extracted_entities"]["companies"]:
            nodes.append({
                "type": "Company", 
                "id": company,
                "properties": {"name": company}
            })
        
        return nodes
    
    def get_kg_relationships(self):
        """Extract relationships ready for Neo4j"""
        relationships = []
        
        # SENT relationship
        if self.data["sender"]:
            relationships.append({
                "type": "SENT",
                "from_node": self.data["sender"]["email"],
                "to_node": self.data["email_id"],
                "properties": {"timestamp": self.data["timestamp"]}
            })
        
        # MENTIONS relationships for companies
        for company in self.data["extracted_entities"]["companies"]:
            relationships.append({
                "type": "MENTIONS",
                "from_node": self.data["email_id"],
                "to_node": company,
                "properties": {}
            })
        
        return relationships

# Helper function to process emails from existing IMAP code
def process_email_with_data_model(email_message, email_id, raw_email):
    """
    Process a single email using the comprehensive data model.
    Designed to work with existing IMAP connection code.
    """
    email_data = EmailDataModel(email_message, email_id, raw_email)
    return email_data

# Example usage with existing IMAP code:
# email_data = process_email_with_data_model(email_message, email_id, raw_email)
# print(email_data.to_json())  # Complete email data
# kg_nodes = email_data.get_kg_nodes()  # Neo4j nodes
# kg_relationships = email_data.get_kg_relationships()  # Neo4j relationships
