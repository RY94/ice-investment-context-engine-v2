# imap_email_ingestion_pipeline/intelligent_link_processor.py
# Intelligent Link Processor - Extracts, classifies, follows, and harvests research reports from email links
# The missing 90% of value - most financial emails just point to the real content!
# RELEVANT FILES: contextual_signal_extractor.py, ultra_refined_email_processor.py, attachment_processor.py

import asyncio
import aiohttp
import aiofiles
import hashlib
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
import time

try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PDF processing libraries not available")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("DOCX processing not available")

@dataclass
class ExtractedLink:
    """A link extracted from an email"""
    url: str
    context: str  # Surrounding text like "Download Report"
    link_text: str  # Actual link text
    link_type: str  # anchor, plain_text, etc.
    position: int  # Position in email content
    
@dataclass
class ClassifiedLink:
    """A link classified by importance and type"""
    url: str
    context: str
    classification: str  # research_report, portal, tracking, social, other
    priority: int  # 1=highest, 5=lowest
    confidence: float
    expected_content_type: str  # pdf, html, docx, etc.
    
@dataclass
class DownloadedReport:
    """A successfully downloaded research report"""
    url: str
    local_path: str
    content_type: str
    file_size: int
    text_content: str
    metadata: Dict[str, Any]
    download_time: datetime
    processing_time: float
    
@dataclass
class LinkProcessingResult:
    """Result of processing all links from an email"""
    total_links_found: int
    research_reports: List[DownloadedReport]
    portal_links: List[ClassifiedLink]
    failed_downloads: List[Dict[str, Any]]
    processing_summary: Dict[str, Any]

class IntelligentLinkProcessor:
    """
    ASYMMETRIC VALUE COMPONENT: Intelligent Link Processing
    
    Properly extracts ALL URLs from emails, classifies them by importance,
    follows research report links, downloads PDFs/documents, extracts text,
    and caches everything for the ICE system.
    
    This is where 90% of the real value lives - the actual research reports!
    """
    
    def __init__(self, download_dir: str = "./data/downloaded_reports", cache_dir: str = "./data/link_cache"):
        self.download_dir = Path(download_dir)
        self.cache_dir = Path(cache_dir)
        
        # Create directories
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__ + ".IntelligentLinkProcessor")
        
        # URL classification patterns
        self.classification_patterns = {
            'research_report': [
                r'\.pdf$', r'\.docx?$', r'\.pptx?$',
                r'/download/', r'/research/', r'/report/', r'/analysis/',
                r'research.*\.pdf', r'report.*\.pdf',
                r'morning.*note', r'daily.*update', r'weekly.*review'
            ],
            'portal': [
                r'/portal/', r'/login/', r'/client/', r'/secure/',
                r'research.*portal', r'client.*access'
            ],
            'tracking': [
                r'/track/', r'/pixel/', r'/beacon/', r'/analytics/',
                r'unsubscribe', r'manage.*preferences',
                r'google-analytics', r'doubleclick'
            ],
            'social': [
                r'facebook\.com', r'twitter\.com', r'linkedin\.com',
                r'youtube\.com', r'instagram\.com'
            ]
        }
        
        # Content type mapping
        self.content_type_map = {
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.ms-powerpoint': 'ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
            'text/html': 'html',
            'text/plain': 'txt'
        }
        
        # Download session configuration
        self.session_config = {
            'timeout': aiohttp.ClientTimeout(total=60),  # 1 minute timeout
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
        # Cache for downloaded content
        self.content_cache = {}
        self._load_cache_index()
        
        self.logger.info(f"Intelligent Link Processor initialized. Download dir: {self.download_dir}")
    
    async def process_email_links(self, email_html: str, email_metadata: Dict[str, Any] = None) -> LinkProcessingResult:
        """
        Main processing pipeline: Extract → Classify → Download → Extract Text
        
        Args:
            email_html: HTML content of the email
            email_metadata: Optional email metadata (sender, subject, etc.)
            
        Returns:
            LinkProcessingResult with all processed links and downloaded reports
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting intelligent link processing")
            
            # Stage 1: Extract ALL URLs properly
            extracted_links = self._extract_all_urls(email_html)
            self.logger.info(f"Extracted {len(extracted_links)} links from email")
            
            # Stage 2: Classify and prioritize URLs
            classified_links = self._classify_urls(extracted_links)
            self.logger.info(f"Classified {len(classified_links['research_report'])} research reports, "
                           f"{len(classified_links['portal'])} portals, "
                           f"{len(classified_links['other'])} other links")
            
            # Stage 3: Download research reports
            research_reports = []
            failed_downloads = []
            
            if classified_links['research_report']:
                research_reports, failed_downloads = await self._download_research_reports(
                    classified_links['research_report']
                )
            
            # Stage 4: Process portal links (look for download links)
            if classified_links['portal']:
                portal_reports, portal_failed = await self._process_portal_links(
                    classified_links['portal']
                )
                research_reports.extend(portal_reports)
                failed_downloads.extend(portal_failed)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Generate processing summary
            processing_summary = {
                'total_processing_time': processing_time,
                'links_extracted': len(extracted_links),
                'research_reports_found': len(classified_links['research_report']),
                'portal_links_found': len(classified_links['portal']),
                'successful_downloads': len(research_reports),
                'failed_downloads': len(failed_downloads),
                'total_text_extracted': sum(len(r.text_content) for r in research_reports),
                'cache_hits': self._get_cache_stats()['hits'],
                'cache_misses': self._get_cache_stats()['misses']
            }
            
            self.logger.info(f"Link processing completed in {processing_time:.2f}s. "
                           f"Downloaded {len(research_reports)} reports.")
            
            return LinkProcessingResult(
                total_links_found=len(extracted_links),
                research_reports=research_reports,
                portal_links=classified_links['portal'],
                failed_downloads=failed_downloads,
                processing_summary=processing_summary
            )
            
        except Exception as e:
            self.logger.error(f"Error processing email links: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return LinkProcessingResult(
                total_links_found=0,
                research_reports=[],
                portal_links=[],
                failed_downloads=[{'error': str(e), 'stage': 'initialization'}],
                processing_summary={'error': str(e), 'processing_time': processing_time}
            )
    
    def _extract_all_urls(self, html_content: str) -> List[ExtractedLink]:
        """Extract ALL URLs from email HTML content properly"""
        links = []
        position = 0
        
        try:
            # Parse HTML properly with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract anchor tag links
            for link_tag in soup.find_all('a', href=True):
                url = link_tag.get('href', '').strip()
                if not url or url.startswith('#'):  # Skip empty or anchor links
                    continue
                
                link_text = link_tag.get_text(strip=True)
                context = self._get_link_context(link_tag, soup)
                
                links.append(ExtractedLink(
                    url=url,
                    context=context,
                    link_text=link_text,
                    link_type='anchor',
                    position=position
                ))
                position += 1
            
            # Extract plain text URLs (not in anchor tags)
            # Remove anchor tags first to avoid duplicates
            for link_tag in soup.find_all('a'):
                link_tag.decompose()
            
            text_content = soup.get_text()
            
            # Find URLs in remaining text
            url_pattern = r'https?://[^\s<>"\']+(?:[^\s<>"\'.,;!?])'
            for match in re.finditer(url_pattern, text_content):
                url = match.group(0)
                start_pos = match.start()
                
                # Get context around the URL
                context_start = max(0, start_pos - 50)
                context_end = min(len(text_content), match.end() + 50)
                context = text_content[context_start:context_end].strip()
                
                links.append(ExtractedLink(
                    url=url,
                    context=context,
                    link_text=url,
                    link_type='plain_text',
                    position=position
                ))
                position += 1
            
        except Exception as e:
            self.logger.warning(f"Error parsing HTML, falling back to regex: {e}")
            # Fallback: simple regex extraction
            url_pattern = r'https?://[^\s<>"\']+(?:[^\s<>"\'.,;!?])'
            for match in re.finditer(url_pattern, html_content):
                url = match.group(0)
                context = html_content[max(0, match.start()-50):match.end()+50]
                
                links.append(ExtractedLink(
                    url=url,
                    context=context,
                    link_text=url,
                    link_type='regex_fallback',
                    position=position
                ))
                position += 1
        
        # Remove duplicates while preserving order
        seen_urls = set()
        unique_links = []
        for link in links:
            if link.url not in seen_urls:
                seen_urls.add(link.url)
                unique_links.append(link)
        
        return unique_links
    
    def _get_link_context(self, link_tag, soup) -> str:
        """Get meaningful context around a link"""
        contexts = []
        
        # Get link text
        link_text = link_tag.get_text(strip=True)
        if link_text:
            contexts.append(link_text)
        
        # Get parent element text
        parent = link_tag.parent
        if parent:
            parent_text = parent.get_text(strip=True)
            if parent_text and parent_text != link_text:
                contexts.append(parent_text[:100])  # Limit context length
        
        # Get preceding and following text
        prev_text = ""
        next_text = ""
        
        # Get previous sibling text
        prev_sibling = link_tag.previous_sibling
        if prev_sibling and hasattr(prev_sibling, 'strip'):
            prev_text = str(prev_sibling).strip()[-30:]  # Last 30 chars
        
        # Get next sibling text
        next_sibling = link_tag.next_sibling
        if next_sibling and hasattr(next_sibling, 'strip'):
            next_text = str(next_sibling).strip()[:30]  # First 30 chars
        
        if prev_text or next_text:
            contexts.append(f"{prev_text} [...] {next_text}")
        
        return " | ".join(contexts)
    
    def _classify_urls(self, extracted_links: List[ExtractedLink]) -> Dict[str, List[ClassifiedLink]]:
        """Classify URLs by importance and type"""
        classified = {
            'research_report': [],
            'portal': [],
            'tracking': [],
            'social': [],
            'other': []
        }
        
        for link in extracted_links:
            classification, confidence, priority = self._classify_single_url(link)
            
            # Determine expected content type
            expected_content_type = self._predict_content_type(link.url)
            
            classified_link = ClassifiedLink(
                url=link.url,
                context=link.context,
                classification=classification,
                priority=priority,
                confidence=confidence,
                expected_content_type=expected_content_type
            )
            
            classified[classification].append(classified_link)
        
        # Sort each category by priority and confidence
        for category in classified:
            classified[category].sort(key=lambda x: (x.priority, -x.confidence))
        
        return classified
    
    def _classify_single_url(self, link: ExtractedLink) -> Tuple[str, float, int]:
        """Classify a single URL and return (classification, confidence, priority)"""
        url = link.url.lower()
        context = link.context.lower()
        
        # Check each classification pattern
        for classification, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url) or re.search(pattern, context):
                    confidence = self._calculate_classification_confidence(link, classification)
                    priority = self._get_classification_priority(classification)
                    return classification, confidence, priority
        
        # Default to 'other' with low confidence
        return 'other', 0.3, 5
    
    def _calculate_classification_confidence(self, link: ExtractedLink, classification: str) -> float:
        """Calculate confidence score for classification"""
        confidence = 0.5  # Base confidence
        
        url = link.url.lower()
        context = link.context.lower()
        
        if classification == 'research_report':
            # Boost confidence for clear research indicators
            if '.pdf' in url:
                confidence += 0.3
            if any(word in context for word in ['download', 'report', 'research', 'analysis']):
                confidence += 0.2
            if any(word in url for word in ['research', 'report', 'analysis', 'morning', 'daily']):
                confidence += 0.2
                
        elif classification == 'portal':
            if any(word in context for word in ['login', 'portal', 'access']):
                confidence += 0.3
                
        elif classification == 'tracking':
            if any(word in url for word in ['track', 'pixel', 'analytics']):
                confidence += 0.4
        
        return min(1.0, confidence)
    
    def _get_classification_priority(self, classification: str) -> int:
        """Get priority level for classification type"""
        priority_map = {
            'research_report': 1,  # Highest priority
            'portal': 2,
            'other': 3,
            'social': 4,
            'tracking': 5  # Lowest priority
        }
        return priority_map.get(classification, 3)
    
    def _predict_content_type(self, url: str) -> str:
        """Predict content type based on URL"""
        url = url.lower()
        
        if '.pdf' in url:
            return 'pdf'
        elif '.doc' in url:
            return 'docx' if 'docx' in url else 'doc'
        elif '.ppt' in url:
            return 'pptx' if 'pptx' in url else 'ppt'
        elif '.xls' in url:
            return 'xlsx' if 'xlsx' in url else 'xls'
        else:
            return 'html'  # Default assumption
    
    async def _download_research_reports(self, research_links: List[ClassifiedLink]) -> Tuple[List[DownloadedReport], List[Dict[str, Any]]]:
        """Download research reports with async processing and retry logic"""
        downloaded_reports = []
        failed_downloads = []
        
        async with aiohttp.ClientSession(**self.session_config) as session:
            # Process downloads with concurrency limit
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent downloads
            
            download_tasks = [
                self._download_single_report(session, semaphore, link)
                for link in research_links[:10]  # Limit to first 10 reports
            ]
            
            results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    failed_downloads.append({
                        'error': str(result),
                        'stage': 'download_task'
                    })
                elif result['success']:
                    downloaded_reports.append(result['report'])
                else:
                    failed_downloads.append(result['error_info'])
        
        return downloaded_reports, failed_downloads
    
    async def _download_single_report(self, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, link: ClassifiedLink) -> Dict[str, Any]:
        """Download a single research report"""
        async with semaphore:
            start_time = datetime.now()
            
            try:
                # Check cache first
                url_hash = hashlib.sha256(link.url.encode()).hexdigest()
                if self._is_cached(url_hash):
                    cached_result = self._get_cached_result(url_hash)
                    if cached_result:
                        self.logger.debug(f"Cache HIT for {link.url[:50]}...")
                        return {'success': True, 'report': cached_result}
                
                # Download with retry logic
                content, content_type = await self._download_with_retry(session, link.url)
                
                # Save to local file
                file_extension = self._get_file_extension(content_type, link.url)
                local_filename = f"{url_hash[:12]}_{int(time.time())}.{file_extension}"
                local_path = self.download_dir / local_filename
                
                async with aiofiles.open(local_path, 'wb') as f:
                    await f.write(content)
                
                # Extract text content
                text_content = await self._extract_text_from_content(content, content_type, str(local_path))
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Create report object
                report = DownloadedReport(
                    url=link.url,
                    local_path=str(local_path),
                    content_type=content_type,
                    file_size=len(content),
                    text_content=text_content,
                    metadata={
                        'context': link.context,
                        'classification_confidence': link.confidence,
                        'download_timestamp': datetime.now().isoformat()
                    },
                    download_time=datetime.now(),
                    processing_time=processing_time
                )
                
                # Cache the result
                self._cache_result(url_hash, report)
                
                self.logger.info(f"Downloaded report: {link.url[:50]}... ({len(content)} bytes, {len(text_content)} chars text)")
                
                return {'success': True, 'report': report}
                
            except Exception as e:
                processing_time = (datetime.now() - start_time).total_seconds()
                error_info = {
                    'url': link.url,
                    'error': str(e),
                    'processing_time': processing_time,
                    'stage': 'download'
                }
                
                self.logger.warning(f"Failed to download {link.url}: {e}")
                return {'success': False, 'error_info': error_info}
    
    async def _download_with_retry(self, session: aiohttp.ClientSession, url: str, max_retries: int = 3) -> Tuple[bytes, str]:
        """Download content with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('content-type', 'application/octet-stream')
                        return content, content_type
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"HTTP {response.status}"
                        )
            
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                self.logger.debug(f"Download attempt {attempt + 1} failed for {url}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
    
    async def _extract_text_from_content(self, content: bytes, content_type: str, local_path: str) -> str:
        """Extract text from downloaded content based on content type"""
        try:
            if 'pdf' in content_type.lower():
                return self._extract_pdf_text(content)
            elif 'word' in content_type.lower() or content_type.endswith('docx'):
                return self._extract_docx_text(local_path)
            elif 'html' in content_type.lower():
                return self._extract_html_text(content.decode('utf-8', errors='ignore'))
            elif 'text' in content_type.lower():
                return content.decode('utf-8', errors='ignore')
            else:
                # Try to decode as text
                return content.decode('utf-8', errors='ignore')[:10000]  # Limit to first 10k chars
        
        except Exception as e:
            self.logger.warning(f"Failed to extract text from {content_type}: {e}")
            return f"[TEXT_EXTRACTION_FAILED: {str(e)}]"
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF content"""
        if not PDF_AVAILABLE:
            return "[PDF_PROCESSING_NOT_AVAILABLE]"
        
        try:
            # Try pdfplumber first (better for tables and complex layouts)
            import io
            with io.BytesIO(content) as pdf_file:
                with pdfplumber.open(pdf_file) as pdf:
                    text_parts = []
                    for page in pdf.pages[:20]:  # Limit to first 20 pages
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    
                    if text_parts:
                        return '\n\n'.join(text_parts)
        
        except Exception as e:
            self.logger.debug(f"pdfplumber failed, trying PyPDF2: {e}")
            
            # Fallback to PyPDF2
            try:
                import io
                with io.BytesIO(content) as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text_parts = []
                    
                    for page_num, page in enumerate(pdf_reader.pages[:20]):  # Limit to first 20 pages
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(page_text)
                        except Exception as page_error:
                            self.logger.debug(f"Failed to extract text from page {page_num}: {page_error}")
                            continue
                    
                    return '\n\n'.join(text_parts) if text_parts else "[NO_TEXT_EXTRACTED]"
                    
            except Exception as e2:
                return f"[PDF_TEXT_EXTRACTION_FAILED: {str(e2)}]"
        
        return "[PDF_PROCESSING_FAILED]"
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        if not DOCX_AVAILABLE:
            return "[DOCX_PROCESSING_NOT_AVAILABLE]"
        
        try:
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return '\n'.join(paragraphs)
        except Exception as e:
            return f"[DOCX_TEXT_EXTRACTION_FAILED: {str(e)}]"
    
    def _extract_html_text(self, html_content: str) -> str:
        """Extract clean text from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            return f"[HTML_TEXT_EXTRACTION_FAILED: {str(e)}]"
    
    def _get_file_extension(self, content_type: str, url: str) -> str:
        """Determine appropriate file extension"""
        # Try content type first
        if 'pdf' in content_type.lower():
            return 'pdf'
        elif 'word' in content_type.lower():
            return 'docx' if 'openxml' in content_type.lower() else 'doc'
        elif 'html' in content_type.lower():
            return 'html'
        
        # Fallback to URL extension
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        if '.' in path:
            return path.split('.')[-1][:4]  # Limit extension length
        
        return 'bin'  # Generic binary file
    
    async def _process_portal_links(self, portal_links: List[ClassifiedLink]) -> Tuple[List[DownloadedReport], List[Dict[str, Any]]]:
        """Process portal links to find embedded download links"""
        portal_reports = []
        portal_failed = []
        
        # For now, just log portal links for manual review
        # In the future, this could parse portal pages to find actual download links
        for link in portal_links[:5]:  # Limit processing
            portal_failed.append({
                'url': link.url,
                'error': 'Portal processing not implemented - requires manual review',
                'stage': 'portal_processing'
            })
        
        return portal_reports, portal_failed
    
    def _load_cache_index(self):
        """Load cache index from disk"""
        self.cache_index_file = self.cache_dir / "link_cache_index.json"
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r') as f:
                    self.cache_index = json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load cache index: {e}")
                self.cache_index = {}
        else:
            self.cache_index = {}
    
    def _save_cache_index(self):
        """Save cache index to disk"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save cache index: {e}")
    
    def _is_cached(self, url_hash: str) -> bool:
        """Check if URL is cached"""
        return url_hash in self.cache_index
    
    def _get_cached_result(self, url_hash: str) -> Optional[DownloadedReport]:
        """Get cached result"""
        if url_hash not in self.cache_index:
            return None
        
        cache_entry = self.cache_index[url_hash]
        cache_file = self.cache_dir / f"{url_hash}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                # Convert back to DownloadedReport object
                cached_data['download_time'] = datetime.fromisoformat(cached_data['download_time'])
                return DownloadedReport(**cached_data)
                
            except Exception as e:
                self.logger.warning(f"Failed to load cached result: {e}")
        
        return None
    
    def _cache_result(self, url_hash: str, report: DownloadedReport):
        """Cache download result"""
        try:
            cache_file = self.cache_dir / f"{url_hash}.json"
            
            # Convert to JSON-serializable format
            report_dict = asdict(report)
            report_dict['download_time'] = report.download_time.isoformat()
            
            with open(cache_file, 'w') as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            # Update index
            self.cache_index[url_hash] = {
                'cached_time': datetime.now().isoformat(),
                'url': report.url,
                'file_size': report.file_size,
                'text_length': len(report.text_content)
            }
            
            self._save_cache_index()
            
        except Exception as e:
            self.logger.error(f"Failed to cache result: {e}")
    
    def _get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'hits': getattr(self, '_cache_hits', 0),
            'misses': getattr(self, '_cache_misses', 0),
            'total_cached': len(self.cache_index)
        }
    
    def format_results_for_output(self, result: LinkProcessingResult) -> Dict[str, Any]:
        """Format link processing results for JSON output"""
        return {
            'link_processing_summary': {
                'total_links_found': result.total_links_found,
                'research_reports_downloaded': len(result.research_reports),
                'portal_links_found': len(result.portal_links),
                'failed_downloads': len(result.failed_downloads),
                'processing_summary': result.processing_summary
            },
            'downloaded_reports': [
                {
                    'url': report.url,
                    'local_path': report.local_path,
                    'content_type': report.content_type,
                    'file_size_bytes': report.file_size,
                    'text_length_chars': len(report.text_content),
                    'processing_time': report.processing_time,
                    'download_time': report.download_time.isoformat()
                }
                for report in result.research_reports
            ],
            'portal_links': [
                {
                    'url': link.url,
                    'context': link.context,
                    'priority': link.priority,
                    'confidence': link.confidence
                }
                for link in result.portal_links
            ],
            'extraction_ready_content': [
                {
                    'source': 'downloaded_report',
                    'url': report.url,
                    'text_content': report.text_content[:5000] + '...' if len(report.text_content) > 5000 else report.text_content,  # Truncate for preview
                    'full_text_available': True,
                    'metadata': report.metadata
                }
                for report in result.research_reports
                if report.text_content and len(report.text_content) > 100
            ]
        }