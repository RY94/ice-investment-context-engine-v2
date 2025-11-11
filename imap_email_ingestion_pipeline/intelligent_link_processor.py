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
import os
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
    
    def __init__(self, storage_path: str = "./data/attachments", cache_dir: str = "./data/link_cache", config: Optional[Any] = None, docling_processor: Optional[Any] = None):
        # Use storage_path instead of download_dir to align with AttachmentProcessor pattern
        # Files saved directly to: storage_path/{email_uid}/{file_hash}/original/{filename}
        self.storage_path = Path(storage_path)
        self.cache_dir = Path(cache_dir)

        # Create directories
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__ + ".IntelligentLinkProcessor")

        # Docling processor for URL PDFs (97.9% table accuracy)
        # Phase 2 implementation (2025-11-04): Integrate Docling for URL PDFs
        self.docling_processor = docling_processor
        self.use_docling_urls = config.use_docling_urls if config else False

        # Crawl4AI configuration (hybrid URL fetching strategy)
        # Prefer simple HTTP (fast, free) for direct downloads
        # Use Crawl4AI (browser automation) for complex sites (JS-heavy, login-required)
        self.use_crawl4ai = config.use_crawl4ai_links if config else False
        self.crawl4ai_timeout = config.crawl4ai_timeout if config else 60
        self.crawl4ai_headless = config.crawl4ai_headless if config else True

        # URL processing master switch (complete enable/disable)
        # Controls whether to process URLs at all (extraction, classification, downloads)
        # Fail-safe: defaults to True if config not provided or attribute missing
        self.process_urls_enabled = getattr(config, 'process_urls', True) if config else True

        # Rate limiting configuration to prevent overwhelming servers
        # Configurable via environment variables for flexibility
        self.rate_limit_delay = float(os.getenv('URL_RATE_LIMIT_DELAY', '1.0'))  # Default 1 second between requests
        self.concurrent_downloads = int(os.getenv('URL_CONCURRENT_DOWNLOADS', '3'))  # Max 3 concurrent downloads
        self.last_download_time = {}  # Track last download time per domain
        self.download_semaphore = asyncio.Semaphore(self.concurrent_downloads)  # Limit concurrent downloads
        
        # URL classification patterns
        self.classification_patterns = {
            'research_report': [
                # Static file downloads
                r'\.pdf$', r'\.docx?$', r'\.pptx?$',

                # Path-based patterns
                r'/download/', r'/research/', r'/report/', r'/analysis/',
                r'research.*\.pdf', r'report.*\.pdf',
                r'morning.*note', r'daily.*update', r'weekly.*review',

                # Dynamic research endpoints (broker platforms)
                r'research\S*\.(aspx|jsp|php)',  # Research URLs with dynamic backends (DBS, UOB, etc.)
                r'(ResearchManager|DownloadResearch|ReportDownload)',  # Common research platform endpoints

                # Authenticated research URLs
                r'research\S*\?E=',      # DBS/UOB-style auth tokens
                r'research\S*\?token=',  # Generic research auth tokens
                r'download\S*\?id=',     # Generic download tokens
            ],
            'portal': [
                r'/portal/', r'/login/', r'/client/', r'/secure/',
                r'research.*portal', r'client.*access',
                r'/insightsdirect/',  # DBS Insights Direct portal (research report pages)
                r'/corporateaccess',   # DBS Corporate Access portal
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

        self.logger.info(f"Intelligent Link Processor initialized. Storage path: {self.storage_path}")
        self.logger.info(f"Rate limiting: {self.rate_limit_delay}s delay, max {self.concurrent_downloads} concurrent downloads")

    def _sanitize_email_uid(self, subject: str) -> str:
        """Sanitize email subject for use as directory name (matches AttachmentProcessor pattern)"""
        # Remove or replace characters that are problematic for file systems
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', subject)
        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip(' .')
        # Limit length to avoid path issues
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        return sanitized if sanitized else 'unknown_email'

    def _compute_file_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of file content for deduplication"""
        return hashlib.sha256(content).hexdigest()

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
            # Extract email_uid from metadata for structured storage
            email_uid = 'unknown_email'
            if email_metadata and 'subject' in email_metadata:
                email_uid = self._sanitize_email_uid(email_metadata['subject'])

            self.logger.info("Starting intelligent link processing")

            # Early exit if URL processing is disabled
            if not self.process_urls_enabled:
                self.logger.info("⏭️ URL processing disabled (ICE_PROCESS_URLS=false) - skipping all URL extraction and downloads")
                return LinkProcessingResult(
                    total_links_found=0,
                    research_reports=[],
                    portal_links=[],
                    failed_downloads=[],
                    processing_summary={
                        'status': 'skipped',
                        'reason': 'URL processing disabled via ICE_PROCESS_URLS flag',
                        'timestamp': datetime.now().isoformat()
                    }
                )

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
                    classified_links['research_report'],
                    email_uid=email_uid
                )

            # Stage 4: Process portal links (look for download links)
            if classified_links['portal']:
                portal_reports, portal_failed = await self._process_portal_links(
                    classified_links['portal'],
                    email_uid=email_uid
                )
                research_reports.extend(portal_reports)
                failed_downloads.extend(portal_failed)

            # FIX (2025-11-04): Account for skipped URLs (tracking, social, other)
            # Bug: Stage 2 classification filtered out non-research URLs, causing them to be missing from output
            # Result: "4 URLs extracted" but only 1 shown (3 tracking/social/other URLs silently dropped)
            # Fix: Add tracking/social/other URLs to failed_downloads as skipped for transparency
            for category in ['tracking', 'social', 'other']:
                for link in classified_links.get(category, []):
                    failed_downloads.append({
                        'url': link.url,
                        'skipped': True,
                        'tier': 6,
                        'tier_name': 'skip',
                        'reason': f'URL classified as {category} (no research value)',
                        'stage': 'classification'
                    })

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

    def _is_simple_http_url(self, url: str) -> bool:
        """
        Check if URL can use simple HTTP (no browser automation needed).

        Cases for simple HTTP:
        - DBS research URLs with embedded auth tokens (?E=...)
        - Direct file downloads (.pdf, .xlsx, etc.)
        - SEC EDGAR (static HTML)
        - CDN/static content

        Returns:
            True if simple HTTP is sufficient
        """
        # DBS research portal with embedded auth token
        if 'researchwise.dbsvresearch.com' in url and '?E=' in url:
            self.logger.debug(f"Simple HTTP: DBS research portal with auth token")
            return True

        # Direct file downloads
        if url.endswith(('.pdf', '.xlsx', '.docx', '.pptx', '.csv', '.zip')):
            self.logger.debug(f"Simple HTTP: Direct file download")
            return True

        # SEC EDGAR (static HTML)
        if 'sec.gov' in url:
            self.logger.debug(f"Simple HTTP: SEC EDGAR (static HTML)")
            return True

        # Static content delivery (CDN, S3, CloudFront)
        static_indicators = ['cdn', 'static', 's3.amazonaws.com', 'cloudfront.net']
        if any(indicator in url.lower() for indicator in static_indicators):
            self.logger.debug(f"Simple HTTP: Static content delivery")
            return True

        return False

    def _is_complex_url(self, url: str) -> bool:
        """
        Check if URL requires Crawl4AI browser automation.

        Cases for Crawl4AI:
        - Premium research portals (login required)
        - JavaScript-heavy IR sites (React/Angular/Vue)
        - Portal/dashboard sites (multi-step navigation)

        Returns:
            True if Crawl4AI is required
        """
        # Premium research portals (login required)
        premium_portals = [
            'research.goldmansachs.com',
            'research.morganstanley.com',
            'research.jpmorgan.com',
            'research.baml.com',
            'research.credit-suisse.com'
        ]

        if any(portal in url for portal in premium_portals):
            self.logger.debug(f"Complex URL: Premium research portal (login required)")
            return True

        # JavaScript-heavy investor relations sites
        js_heavy_sites = [
            'ir.nvidia.com',
            'investor.apple.com',
            'investors.tesla.com',
            'investor.fb.com',
            'investor.google.com'
        ]

        if any(site in url for site in js_heavy_sites):
            self.logger.debug(f"Complex URL: JavaScript-heavy IR site")
            return True

        # Portal/dashboard indicators (multi-step navigation)
        portal_indicators = ['portal', 'dashboard', 'member', 'login']
        if any(indicator in url.lower() for indicator in portal_indicators):
            # But exclude DBS (already handled above as simple HTTP)
            if 'researchwise.dbsvresearch.com' not in url:
                self.logger.debug(f"Complex URL: Portal/dashboard site")
                return True

        return False

    def _classify_url_tier(self, url: str) -> Tuple[int, str]:
        """
        Classify URL into one of 6 tiers for processing strategy.
        
        Returns:
            (tier_number, tier_name) tuple
            
        Tier 1: Direct downloads (simple HTTP)
        Tier 2: Token-authenticated direct (simple HTTP) 
        Tier 3: Simple crawl (Crawl4AI + content filtering)
        Tier 4: Research portals (Crawl4AI + session auth)
        Tier 5: News paywalls (Crawl4AI + BM25 filtering)
        Tier 6: Skip (social media, tracking)
        """
        url_lower = url.lower()
        
        # Tier 6: Skip (social, tracking) - Check first to avoid processing
        if self._is_tier6_skip(url_lower):
            return (6, "skip")
        
        # Tier 1: Direct file downloads
        if url.endswith(('.pdf', '.xlsx', '.docx', '.pptx', '.csv', '.zip')):
            return (1, "direct_download")
        
        # Tier 2: Token-authenticated direct (DBS research)
        # DBS uses both ?E= and ?I= parameters for authenticated downloads
        if 'researchwise.dbsvresearch.com' in url_lower and ('?e=' in url_lower or '?i=' in url_lower):
            return (2, "token_auth_direct")
        
        # Tier 4: Research portals (auth required) - Check before Tier 3
        if self._is_tier4_portal(url_lower):
            return (4, "portal_auth")
        
        # Tier 5: News paywalls - Check before Tier 3
        if self._is_tier5_paywall(url_lower):
            return (5, "news_paywall")
        
        # Tier 3: Simple crawl (news sites, general content)
        if self._is_tier3_simple_crawl(url_lower):
            return (3, "simple_crawl")
        
        # Default: Tier 3 fallback (safest - Crawl4AI with markdown)
        return (3, "simple_crawl_fallback")
    
    def _is_tier3_simple_crawl(self, url_lower: str) -> bool:
        """
        Check if URL is Tier 3: Simple crawl (news/content sites without paywall).
        
        These are sites that can be scraped with Crawl4AI + content filtering
        but don't require authentication or special handling.
        """
        tier3_domains = [
            # Financial news (no paywalls)
            'www.reuters.com',
            'www.caixinglobal.com',
            'www.bangkokpost.com',
            'www.scmp.com',  # South China Morning Post
            'www.straitstimes.com',
            
            # General business news
            'www.cnbc.com',
            'www.ft.com',  # Financial Times (some articles free)
            'www.economist.com',  # Some free articles
            
            # Regional/specific content
            'rfs.cgsi.com',  # CGS research file server
            'www.investing.com',
            'seekingalpha.com',  # Some free articles
            
            # CDN/static (use simple crawl if not direct download)
            'cdn.',
            'static.',
            's3.amazonaws.com',
            'cloudfront.net'
        ]
        
        return any(domain in url_lower for domain in tier3_domains)
    
    def _is_tier4_portal(self, url_lower: str) -> bool:
        """
        Check if URL is Tier 4: Research portal (authentication required).
        
        These portals require:
        - Login credentials
        - Session management
        - Multi-step navigation
        - CSS extraction schemas
        """
        # Research portals discovered in analysis
        tier4_portals = [
            # Top portals from 71-email analysis
            'research.rhbtradesmart.com',  # 234 URLs (12.8%)
            'resmail.cgsi.com',  # 104 URLs (5.7%)
            
            # Premium broker portals
            'research.goldmansachs.com',
            'research.morganstanley.com',
            'research.jpmorgan.com',
            'research.baml.com',
            'research.credit-suisse.com',
            'research.ubs.com',
            'research.citi.com',
            'research.barclays.com',
            
            # DBS portal pages (not direct research downloads)
            # Note: researchwise.dbsvresearch.com with ?E= is Tier 2, already handled
            'www.dbs.com/insightsdirect/company',  # 443 URLs (portal pages)
            'www.dbs.com/insightsdirect/corporateaccess',
            
            # Generic patterns
            'portal.',
            'dashboard.',
            'member.',
            'login.'
        ]
        
        # Check for portal domains
        if any(portal in url_lower for portal in tier4_portals):
            return True
        
        # Check for .aspx files (often auth-required broker portals)
        # 179 URLs (9.7%) are .aspx files
        if '.aspx' in url_lower and 'research' in url_lower:
            # But exclude DBS direct downloads (already Tier 2)
            if 'researchwise.dbsvresearch.com' not in url_lower:
                return True
        
        return False
    
    def _is_tier5_paywall(self, url_lower: str) -> bool:
        """
        Check if URL is Tier 5: News site with potential paywall.
        
        These sites may require:
        - Subscription/premium content bypass attempts
        - BM25 content filtering for relevance
        - Graceful failure handling (some articles will be blocked)
        """
        tier5_paywall_sites = [
            # Confirmed paywalls from analysis
            'blinks.bloomberg.com',  # 162 URLs (8.8%)
            'www.bloomberg.com',
            'www.businesstimes.com.sg',  # 194 URLs (10.6%)
            
            # Other known paywalls
            'www.wsj.com',  # Wall Street Journal
            'www.nytimes.com',
            'www.washingtonpost.com',
            'www.telegraph.co.uk',
            'www.ft.com',  # Financial Times (premium)
            
            # Asian business paywalls
            'asia.nikkei.com',
            'www.scmp.com/business',  # SCMP premium
        ]
        
        return any(site in url_lower for site in tier5_paywall_sites)
    
    def _is_tier6_skip(self, url_lower: str) -> bool:
        """
        Check if URL is Tier 6: Skip (no investment research value).
        
        These URLs provide no value and should be skipped entirely:
        - Social media links
        - Tracking pixels / analytics
        - Unsubscribe links
        - Advertisement redirects
        """
        skip_patterns = [
            # Social media
            'twitter.com',
            'linkedin.com',
            'facebook.com',
            'youtube.com',
            'instagram.com',
            'weibo.com',
            
            # Tracking / analytics
            'track',
            'analytics',
            'pixel',
            'beacon',
            'unsubscribe',
            'preferences',
            'opt-out',
            
            # Ad networks
            'doubleclick',
            'googlesyndication',
            'adservice',
            'advertising',
            
            # Email tracking
            'email-track',
            'open-track',
            'click-track'
        ]
        
        return any(pattern in url_lower for pattern in skip_patterns)

    async def _fetch_with_crawl4ai(self, url: str) -> tuple[bytes, str]:
        """
        Fetch URL using Crawl4AI browser automation.

        This method handles:
        - JavaScript-heavy pages (React/Angular/Vue)
        - Login-required portals (session management)
        - Multi-step navigation
        - Dynamic content loading

        Args:
            url: URL to fetch

        Returns:
            tuple: (content bytes, content_type string)

        Raises:
            Exception: If Crawl4AI fetch fails
        """
        try:
            from crawl4ai import AsyncWebCrawler

            self.logger.info(f"Fetching with Crawl4AI: {url[:60]}...")

            async with AsyncWebCrawler(
                headless=self.crawl4ai_headless,
                verbose=False  # Set to True for debugging
            ) as crawler:
                # Fetch with timeout
                result = await asyncio.wait_for(
                    crawler.arun(url=url, bypass_cache=True),
                    timeout=self.crawl4ai_timeout
                )

                if not result.success:
                    raise Exception(f"Crawl4AI fetch failed: {result.error if hasattr(result, 'error') else 'Unknown error'}")

                # Check what we got
                content_type = 'text/html'  # Default

                # If we got markdown content (HTML was rendered)
                if result.markdown and len(result.markdown) > 100:
                    content = result.markdown.encode('utf-8')
                    content_type = 'text/markdown'
                    self.logger.info(f"Crawl4AI success: {len(content)} bytes markdown from {url[:60]}...")

                # If we got HTML but no markdown (possible PDF download)
                elif result.html and len(result.html) > 100:
                    content = result.html.encode('utf-8')
                    content_type = 'text/html'
                    self.logger.info(f"Crawl4AI success: {len(content)} bytes HTML from {url[:60]}...")

                # Very short content - might be redirect or error
                else:
                    raise Exception(f"Crawl4AI returned minimal content ({len(result.markdown if result.markdown else '')} chars)")

                return content, content_type

        except asyncio.TimeoutError:
            raise Exception(f"Crawl4AI timeout after {self.crawl4ai_timeout}s")

        except ImportError as e:
            raise Exception(
                "Crawl4AI not installed. Install with: pip install -U crawl4ai && crawl4ai-setup"
            ) from e

        except Exception as e:
            raise Exception(f"Crawl4AI error: {e}")

    async def _download_research_reports(self, research_links: List[ClassifiedLink], email_uid: str) -> Tuple[List[DownloadedReport], List[Dict[str, Any]]]:
        """Download research reports with async processing and retry logic"""
        downloaded_reports = []
        failed_downloads = []

        async with aiohttp.ClientSession(**self.session_config) as session:
            # Process downloads with concurrency limit
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent downloads

            download_tasks = [
                self._download_single_report(session, semaphore, link, email_uid)
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
    
    async def _download_single_report(self, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, link: ClassifiedLink, email_uid: str) -> Dict[str, Any]:
        """
        Download a single research report using 6-tier classification system.

        Tier 1: Direct downloads (simple HTTP)
        Tier 2: Token-authenticated direct (simple HTTP)
        Tier 3: Simple crawl (Crawl4AI + content filtering)
        Tier 4: Research portals (Crawl4AI + session auth)
        Tier 5: News paywalls (Crawl4AI + BM25 filtering)
        Tier 6: Skip (social media, tracking)

        Saves directly to: storage_path/{email_uid}/{file_hash}/original/{filename}
        """
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
                
                # NEW: 6-Tier Classification System
                tier, tier_name = self._classify_url_tier(link.url)
                self.logger.info(f"URL classified as Tier {tier} ({tier_name}): {link.url[:60]}...")
                
                # Handle Tier 6: Skip
                # FIX (2025-11-04): Return consistent error_info structure for transparency
                # Bug: Previously returned {'success': False, 'skipped': True} without 'url' or 'error_info'
                # Result: Skipped URLs missing from Cell 15 output (4 URLs extracted, only 1 shown)
                # Fix: Wrap in error_info structure matching line 994 error handling
                if tier == 6:
                    self.logger.info(f"Skipping Tier 6 URL (social/tracking): {link.url[:60]}...")
                    return {
                        'success': False,
                        'error_info': {  # ✅ Consistent with error handling (line 994)
                            'url': link.url,  # ✅ Required by output formatter (data_ingestion.py:1359)
                            'skipped': True,
                            'tier': tier,
                            'tier_name': tier_name,
                            'reason': 'URL classified as social media or tracking (no research value)',
                            'stage': 'classification'
                        }
                    }
                
                # Route based on tier
                content = None
                content_type = None
                
                if tier in [1, 2]:
                    # Tier 1 & 2: Simple HTTP (direct downloads, token auth)
                    self.logger.debug(f"Using simple HTTP for Tier {tier}: {link.url[:60]}...")
                    content, content_type = await self._download_with_retry(session, link.url)
                
                elif tier == 3:
                    # Tier 3: Simple crawl (Crawl4AI + content filtering)
                    if self.use_crawl4ai:
                        self.logger.info(f"Using Crawl4AI for Tier 3 (simple crawl): {link.url[:60]}...")
                        try:
                            # Phase 1: Basic Crawl4AI (markdown only)
                            # Phase 2 will add PruningContentFilter here
                            content, content_type = await self._fetch_with_crawl4ai(link.url)
                        except Exception as crawl4ai_error:
                            # Graceful degradation: fallback to simple HTTP
                            self.logger.warning(f"Crawl4AI failed for Tier 3, falling back to simple HTTP: {crawl4ai_error}")
                            content, content_type = await self._download_with_retry(session, link.url)
                    else:
                        # Crawl4AI disabled - use simple HTTP
                        content, content_type = await self._download_with_retry(session, link.url)
                
                elif tier == 4:
                    # Tier 4: Research portals (Crawl4AI + session auth + CSS extraction)
                    if self.use_crawl4ai:
                        self.logger.info(f"Using Crawl4AI for Tier 4 (portal auth): {link.url[:60]}...")
                        try:
                            # Phase 1: Basic Crawl4AI (markdown only)
                            # Phase 3 will add portal-specific strategies + CSS extraction here
                            content, content_type = await self._fetch_with_crawl4ai(link.url)
                        except Exception as crawl4ai_error:
                            # Graceful degradation: fallback to simple HTTP (likely to fail but try anyway)
                            self.logger.warning(f"Crawl4AI failed for Tier 4, falling back to simple HTTP: {crawl4ai_error}")
                            content, content_type = await self._download_with_retry(session, link.url)
                    else:
                        # Crawl4AI disabled - portals likely won't work with simple HTTP
                        self.logger.warning(f"Tier 4 portal requires Crawl4AI but it's disabled. Trying simple HTTP anyway: {link.url[:60]}...")
                        content, content_type = await self._download_with_retry(session, link.url)
                
                elif tier == 5:
                    # Tier 5: News paywalls (Crawl4AI + BM25 filtering)
                    if self.use_crawl4ai:
                        self.logger.info(f"Using Crawl4AI for Tier 5 (paywall): {link.url[:60]}...")
                        try:
                            # Phase 1: Basic Crawl4AI (markdown only)
                            # Phase 2 will add BM25ContentFilter here
                            content, content_type = await self._fetch_with_crawl4ai(link.url)
                        except Exception as crawl4ai_error:
                            # Graceful degradation: fallback to simple HTTP (paywalls likely block)
                            self.logger.warning(f"Crawl4AI failed for Tier 5, falling back to simple HTTP: {crawl4ai_error}")
                            content, content_type = await self._download_with_retry(session, link.url)
                    else:
                        # Crawl4AI disabled - paywalls likely won't work
                        self.logger.warning(f"Tier 5 paywall requires Crawl4AI but it's disabled. Trying simple HTTP anyway: {link.url[:60]}...")
                        content, content_type = await self._download_with_retry(session, link.url)
                
                else:
                    # Unknown tier (should not happen) - default to simple HTTP
                    self.logger.warning(f"Unknown tier {tier}, defaulting to simple HTTP: {link.url[:60]}...")
                    content, content_type = await self._download_with_retry(session, link.url)
                
                # Save to structured storage (matches AttachmentProcessor pattern)
                # Pattern: storage_path/{email_uid}/{file_hash}/original/{filename}
                file_hash = self._compute_file_hash(content)
                file_extension = self._get_file_extension(content_type, link.url)
                local_filename = f"{url_hash[:12]}_{int(time.time())}.{file_extension}"

                # Create directory structure
                storage_dir = self.storage_path / email_uid / file_hash
                original_dir = storage_dir / 'original'
                original_dir.mkdir(parents=True, exist_ok=True)

                # Save to final location
                local_path = original_dir / local_filename

                async with aiofiles.open(local_path, 'wb') as f:
                    await f.write(content)

                # CRITICAL: Verify file was actually written to disk
                if not local_path.exists():
                    raise IOError(f"File write claimed success but file not found: {local_path}")

                actual_size = local_path.stat().st_size
                if actual_size != len(content):
                    self.logger.warning(f"⚠️  Size mismatch: expected {len(content)} bytes, got {actual_size} bytes")

                # Log detailed storage information for debugging
                self.logger.info(f"📁 STORAGE VERIFIED: {local_path}")
                self.logger.info(f"   Size on disk: {actual_size:,} bytes (expected: {len(content):,})")
                self.logger.info(f"   Email UID: {email_uid}")
                self.logger.info(f"   File hash: {file_hash}")
                self.logger.info(f"   Storage dir: {storage_dir}")

                # Extract text content
                text_content = await self._extract_text_from_content(content, content_type, str(local_path))

                # Save extracted text (consistency with AttachmentProcessor)
                if text_content:
                    extracted_path = storage_dir / 'extracted.txt'
                    async with aiofiles.open(extracted_path, 'w', encoding='utf-8') as f:
                        await f.write(text_content)

                # Create metadata.json for traceability
                try:
                    metadata = {
                        "source_type": "url_pdf",
                        "source_context": {
                            "email_uid": email_uid,
                            "original_url": link.url,
                            "url_classification": {
                                "tier": tier,
                                "tier_name": tier_name
                            },
                            "link_context": link.context,
                            "classification_confidence": link.confidence,
                            "download_method": "crawl4ai" if tier in [3, 4, 5] and self.use_crawl4ai else "simple_http"
                        },
                        "file_info": {
                            "original_filename": local_filename,
                            "file_hash": file_hash,
                            "file_size": len(content),
                            "mime_type": content_type
                        },
                        "processing": {
                            "timestamp": datetime.now().isoformat(),
                            "extraction_method": "docling" if self.use_docling_urls and self.docling_processor else "pdfplumber",
                            "status": "completed",
                            "text_chars": len(text_content)
                        },
                        "storage": {
                            "original_path": f"original/{local_filename}",
                            "extracted_text_path": "extracted.txt" if text_content else None,
                            "created_at": datetime.now().isoformat()
                        }
                    }

                    metadata_path = storage_dir / 'metadata.json'
                    async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
                        await f.write(json.dumps(metadata, indent=2))

                    self.logger.debug(f"Saved metadata for {link.url[:50]}...")

                except Exception as e:
                    # Log but don't fail the entire process
                    self.logger.warning(f"Failed to create metadata.json for {link.url[:50]}...: {e}")

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
                        'download_timestamp': datetime.now().isoformat(),
                        'tier': tier,  # NEW: Track which tier was used
                        'tier_name': tier_name
                    },
                    download_time=datetime.now(),
                    processing_time=processing_time
                )
                
                # Cache the result
                self._cache_result(url_hash, report)
                
                self.logger.info(f"Downloaded Tier {tier} report: {link.url[:50]}... ({len(content)} bytes, {len(text_content)} chars text)")
                
                return {'success': True, 'report': report, 'tier': tier, 'tier_name': tier_name}
                
            except Exception as e:
                processing_time = (datetime.now() - start_time).total_seconds()
                error_info = {
                    'url': link.url,
                    'error': str(e),
                    'processing_time': processing_time,
                    'stage': 'download',
                    'tier': tier if 'tier' in locals() else None,
                    'tier_name': tier_name if 'tier_name' in locals() else None
                }
                
                self.logger.warning(f"Failed to download {link.url}: {e}")
                return {'success': False, 'error_info': error_info}
    
    async def _download_with_retry(self, session: aiohttp.ClientSession, url: str, max_retries: int = 3) -> Tuple[bytes, str]:
        """Download content with exponential backoff retry logic and rate limiting
        
        Implements:
        - Per-domain rate limiting to respect server limits
        - Concurrent download limits to prevent resource exhaustion
        - Exponential backoff on failures
        """
        # Extract domain for rate limiting
        domain = urlparse(url).netloc
        
        # Acquire semaphore to limit concurrent downloads
        async with self.download_semaphore:
            # Apply rate limiting per domain
            if domain in self.last_download_time:
                time_since_last = time.time() - self.last_download_time[domain]
                if time_since_last < self.rate_limit_delay:
                    delay = self.rate_limit_delay - time_since_last
                    self.logger.debug(f"Rate limiting: waiting {delay:.1f}s before downloading from {domain}")
                    await asyncio.sleep(delay)
            
            # Record download time
            self.last_download_time[domain] = time.time()
            
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
                return self._extract_pdf_text(content, local_path)
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

    def _extract_pdf_with_docling(self, content: bytes, filename: str) -> str:
        """
        Extract text from PDF using Docling (97.9% table accuracy)

        Phase 2 implementation (2025-11-04): URL PDFs now use same processor as email attachments

        Args:
            content: PDF bytes from URL download
            filename: Original filename from URL (for error messages)

        Returns:
            Extracted text content (markdown format)
            Empty string if processing fails (graceful degradation to pdfplumber)
        """
        if not self.docling_processor:
            self.logger.debug("Docling processor not available, falling back to pdfplumber")
            return ""

        if not self.use_docling_urls:
            self.logger.debug("Docling for URL PDFs disabled (USE_DOCLING_URLS=false)")
            return ""

        try:
            # Process PDF bytes with Docling (same API as email attachments)
            result = self.docling_processor.process_pdf_bytes(content, filename)

            if result.get('processing_status') == 'completed':
                text = result.get('extracted_text', '')
                tables = result.get('extracted_data', {}).get('tables', [])
                self.logger.info(f"✅ Docling processed {filename}: {len(text)} chars, {len(tables)} tables (97.9% accuracy)")
                return text
            else:
                error = result.get('error', 'Unknown error')
                self.logger.warning(f"Docling processing failed for {filename}: {error}")
                return ""  # Fall back to pdfplumber

        except Exception as e:
            self.logger.warning(f"Docling processing exception for {filename}: {e}")
            return ""  # Fall back to pdfplumber

    def _extract_pdf_text(self, content: bytes, filename: str = "unknown.pdf") -> str:
        """
        Extract text from PDF content (with Docling integration)

        Phase 2 implementation (2025-11-04): Graceful degradation strategy
        1. Try Docling first (97.9% table accuracy)
        2. Fall back to pdfplumber (42% table accuracy)
        3. Fall back to PyPDF2 (basic text)
        """
        if not PDF_AVAILABLE:
            return "[PDF_PROCESSING_NOT_AVAILABLE]"

        # PHASE 2: Try Docling first (97.9% accuracy)
        docling_text = self._extract_pdf_with_docling(content, filename)
        if docling_text:
            return docling_text

        # FALLBACK 1: pdfplumber (42% accuracy)
        try:
            # Try pdfplumber (better for tables and complex layouts than PyPDF2)
            import io
            with io.BytesIO(content) as pdf_file:
                with pdfplumber.open(pdf_file) as pdf:
                    text_parts = []
                    for page in pdf.pages[:20]:  # Limit to first 20 pages
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)

                    if text_parts:
                        self.logger.info(f"⚠️  pdfplumber processed {filename} (42% accuracy - consider enabling Docling)")
                        return '\n\n'.join(text_parts)
        
        except Exception as e:
            self.logger.debug(f"pdfplumber failed, trying PyPDF2: {e}")

            # FALLBACK 2: PyPDF2 (basic text extraction)
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
    
    async def _process_portal_links(self, portal_links: List[ClassifiedLink], email_uid: str) -> Tuple[List[DownloadedReport], List[Dict[str, Any]]]:
        """
        Process portal links to find embedded download links.

        Portals (e.g., DBS Insights Direct, Goldman Sachs Research Portal) contain
        embedded research reports that require browser automation to access.

        Strategy:
        1. Use Crawl4AI to fetch portal page HTML
        2. Parse HTML to find download links (PDFs, .aspx reports, etc.)
        3. Download discovered links using existing _download_single_report()

        Args:
            portal_links: List of ClassifiedLink objects for portal URLs
            email_uid: Sanitized email subject for structured storage

        Returns:
            Tuple of (downloaded_reports, failed_downloads)
        """
        portal_reports = []
        portal_failed = []

        # Check if Crawl4AI is enabled
        if not self.use_crawl4ai:
            for link in portal_links[:5]:  # Limit processing
                portal_failed.append({
                    'url': link.url,
                    'error': 'Portal processing requires Crawl4AI (set USE_CRAWL4AI_LINKS=true)',
                    'stage': 'portal_processing'
                })
            return portal_reports, portal_failed

        # Process each portal link
        async with aiohttp.ClientSession(**self.session_config) as session:
            for link in portal_links[:5]:  # Limit to first 5 portals
                try:
                    self.logger.info(f"Processing portal: {link.url[:70]}...")

                    # Fetch portal page with Crawl4AI
                    portal_html, content_type = await self._fetch_with_crawl4ai(link.url)

                    # Parse HTML to find download links
                    discovered_links = self._extract_download_links_from_portal(
                        portal_html.decode('utf-8', errors='ignore'),
                        link.url
                    )

                    if not discovered_links:
                        portal_failed.append({
                            'url': link.url,
                            'error': 'No download links found in portal page',
                            'stage': 'portal_parsing'
                        })
                        continue

                    self.logger.info(f"Found {len(discovered_links)} download links in portal")

                    # Download discovered links
                    semaphore = asyncio.Semaphore(3)  # Limit concurrent downloads
                    download_tasks = [
                        self._download_single_report(session, semaphore, disc_link, email_uid)
                        for disc_link in discovered_links[:3]  # Limit to first 3 links
                    ]

                    results = await asyncio.gather(*download_tasks, return_exceptions=True)

                    for result in results:
                        if isinstance(result, Exception):
                            portal_failed.append({
                                'url': link.url,
                                'error': str(result),
                                'stage': 'portal_download'
                            })
                        elif result['success']:
                            portal_reports.append(result['report'])
                        else:
                            portal_failed.append(result['error'])

                except Exception as e:
                    portal_failed.append({
                        'url': link.url,
                        'error': f'Portal processing failed: {str(e)}',
                        'stage': 'portal_crawl'
                    })

        return portal_reports, portal_failed

    def _extract_download_links_from_portal(self, html_content: str, base_url: str) -> List[ClassifiedLink]:
        """
        Extract download links from portal page HTML.

        Looks for:
        - Direct PDF links: <a href="report.pdf">
        - ASPX report links: <a href="report.aspx?id=123">
        - Download buttons: <a class="download-btn" href="...">

        Args:
            html_content: Portal page HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of ClassifiedLink objects for discovered download links
        """
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse

        discovered_links = []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all <a> tags with href
            for link_tag in soup.find_all('a', href=True):
                href = link_tag.get('href', '').strip()
                if not href or href.startswith('#'):
                    continue

                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)

                # Check if this looks like a download link
                url_lower = absolute_url.lower()
                is_download = any([
                    url_lower.endswith('.pdf'),
                    url_lower.endswith('.aspx'),
                    url_lower.endswith('.docx'),
                    url_lower.endswith('.xlsx'),
                    '/download' in url_lower,
                    '/report' in url_lower,
                    'download' in link_tag.get('class', []),
                    'download' in link_tag.get_text(strip=True).lower()
                ])

                if is_download:
                    # Classify the discovered link using existing classification logic
                    # Create ExtractedLink to reuse classification infrastructure
                    extracted_link = ExtractedLink(
                        url=absolute_url,
                        context=f"Portal: {base_url}",
                        link_text=link_tag.get_text(strip=True),
                        link_type='portal_discovered',
                        position=0
                    )

                    # Get classification, confidence, and priority from existing method
                    classification, confidence, priority = self._classify_single_url(extracted_link)

                    # Predict content type
                    expected_content_type = self._predict_content_type(absolute_url)

                    # Create ClassifiedLink with correct schema (all required attributes)
                    discovered_links.append(ClassifiedLink(
                        url=absolute_url,
                        context=f"Portal: {base_url}",
                        classification=classification,  # ✅ Correct attribute name
                        priority=priority,               # ✅ Required attribute
                        confidence=confidence,           # ✅ Required attribute
                        expected_content_type=expected_content_type  # ✅ Required attribute
                    ))

        except Exception as e:
            self.logger.error(f"Failed to parse portal HTML: {e}")

        return discovered_links
    
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