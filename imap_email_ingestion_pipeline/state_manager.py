# imap_email_ingestion_pipeline/state_manager.py
# SQLite-based state management for email processing pipeline
# Tracks processed emails, attachments, errors, and performance metrics
# RELEVANT FILES: pipeline_orchestrator.py, imap_connector.py, attachment_processor.py

import sqlite3
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class StateManager:
    def __init__(self, db_path: str = "./data/state.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript("""
                -- Email processing state
                CREATE TABLE IF NOT EXISTS emails (
                    email_uid TEXT PRIMARY KEY,
                    message_id TEXT,
                    subject TEXT,
                    sender TEXT,
                    received_date TEXT,
                    processed_date TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    processing_time_ms INTEGER
                );
                
                -- Attachment tracking with deduplication
                CREATE TABLE IF NOT EXISTS attachments (
                    file_hash TEXT PRIMARY KEY,
                    email_uid TEXT,
                    filename TEXT,
                    file_size INTEGER,
                    mime_type TEXT,
                    extracted_text_length INTEGER,
                    ocr_confidence REAL,
                    processing_status TEXT DEFAULT 'pending',
                    extraction_method TEXT,
                    created_date TEXT,
                    FOREIGN KEY (email_uid) REFERENCES emails (email_uid)
                );
                
                -- Performance metrics
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    metadata TEXT
                );
                
                -- Sender reputation scoring
                CREATE TABLE IF NOT EXISTS senders (
                    sender_email TEXT PRIMARY KEY,
                    reputation_score INTEGER DEFAULT 50,
                    total_emails INTEGER DEFAULT 0,
                    avg_processing_time_ms INTEGER DEFAULT 0,
                    last_seen TEXT,
                    categories TEXT  -- JSON array
                );
                
                -- Error tracking
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    email_uid TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    retry_count INTEGER
                );
                
                -- Create indexes for performance
                CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status);
                CREATE INDEX IF NOT EXISTS idx_emails_priority ON emails(priority DESC);
                CREATE INDEX IF NOT EXISTS idx_attachments_status ON attachments(processing_status);
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC);
                """)
                
            self.logger.info("State database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def is_email_processed(self, email_uid: str) -> bool:
        """Check if email has already been processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT status FROM emails WHERE email_uid = ?", 
                    (email_uid,)
                )
                result = cursor.fetchone()
                return result and result[0] == 'completed'
        except Exception as e:
            self.logger.error(f"Error checking email status: {e}")
            return False
    
    def mark_email_processing(self, email_uid: str, email_data: Dict[str, Any]) -> bool:
        """Mark email as currently being processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO emails 
                    (email_uid, message_id, subject, sender, received_date, 
                     processed_date, status, priority) 
                    VALUES (?, ?, ?, ?, ?, ?, 'processing', ?)
                """, (
                    email_uid,
                    email_data.get('message_id', ''),
                    email_data.get('subject', ''),
                    email_data.get('from', ''),
                    email_data.get('date', ''),
                    datetime.now().isoformat(),
                    email_data.get('priority', 0)
                ))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error marking email as processing: {e}")
            return False
    
    def mark_email_completed(self, email_uid: str, processing_time_ms: int = 0) -> bool:
        """Mark email as successfully processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE emails 
                    SET status = 'completed', 
                        processing_time_ms = ?,
                        processed_date = ?
                    WHERE email_uid = ?
                """, (processing_time_ms, datetime.now().isoformat(), email_uid))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error marking email as completed: {e}")
            return False
    
    def mark_email_failed(self, email_uid: str, error_message: str) -> bool:
        """Mark email as failed with error message"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE emails 
                    SET status = 'failed', 
                        error_message = ?,
                        retry_count = retry_count + 1
                    WHERE email_uid = ?
                """, (error_message, email_uid))
                conn.commit()
                
                # Log error to errors table
                cursor.execute("""
                    INSERT INTO errors 
                    (timestamp, email_uid, error_type, error_message, retry_count)
                    VALUES (?, ?, 'processing', ?, 
                            (SELECT retry_count FROM emails WHERE email_uid = ?))
                """, (datetime.now().isoformat(), email_uid, error_message, email_uid))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error marking email as failed: {e}")
            return False
    
    def get_attachment_hash(self, content: bytes) -> str:
        """Generate SHA-256 hash for attachment deduplication"""
        return hashlib.sha256(content).hexdigest()
    
    def is_attachment_processed(self, file_hash: str) -> bool:
        """Check if attachment has already been processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT processing_status FROM attachments WHERE file_hash = ?",
                    (file_hash,)
                )
                result = cursor.fetchone()
                return result and result[0] == 'completed'
        except Exception as e:
            self.logger.error(f"Error checking attachment status: {e}")
            return False
    
    def record_attachment(self, email_uid: str, filename: str, file_hash: str, 
                         file_size: int, mime_type: str) -> bool:
        """Record attachment metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO attachments
                    (file_hash, email_uid, filename, file_size, mime_type, 
                     processing_status, created_date)
                    VALUES (?, ?, ?, ?, ?, 'processing', ?)
                """, (file_hash, email_uid, filename, file_size, mime_type, 
                      datetime.now().isoformat()))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error recording attachment: {e}")
            return False
    
    def update_attachment_results(self, file_hash: str, extracted_text_length: int,
                                 ocr_confidence: float, extraction_method: str) -> bool:
        """Update attachment processing results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE attachments 
                    SET processing_status = 'completed',
                        extracted_text_length = ?,
                        ocr_confidence = ?,
                        extraction_method = ?
                    WHERE file_hash = ?
                """, (extracted_text_length, ocr_confidence, extraction_method, file_hash))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating attachment results: {e}")
            return False
    
    def record_metric(self, metric_name: str, value: float, metadata: Dict = None):
        """Record performance metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO metrics (timestamp, metric_name, metric_value, metadata)
                    VALUES (?, ?, ?, ?)
                """, (datetime.now().isoformat(), metric_name, value, 
                      json.dumps(metadata) if metadata else None))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error recording metric: {e}")
    
    def get_processing_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get processing statistics for last N hours"""
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Email processing stats
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM emails 
                    WHERE processed_date > ? 
                    GROUP BY status
                """, (cutoff_time,))
                email_stats = dict(cursor.fetchall())
                
                # Attachment processing stats
                cursor.execute("""
                    SELECT processing_status, COUNT(*), AVG(ocr_confidence)
                    FROM attachments 
                    WHERE created_date > ? 
                    GROUP BY processing_status
                """, (cutoff_time,))
                attachment_stats = {row[0]: {'count': row[1], 'avg_confidence': row[2]} 
                                  for row in cursor.fetchall()}
                
                # Error stats
                cursor.execute("""
                    SELECT error_type, COUNT(*) 
                    FROM errors 
                    WHERE timestamp > ? 
                    GROUP BY error_type
                """, (cutoff_time,))
                error_stats = dict(cursor.fetchall())
                
                return {
                    'emails': email_stats,
                    'attachments': attachment_stats,
                    'errors': error_stats,
                    'period_hours': hours
                }
                
        except Exception as e:
            self.logger.error(f"Error getting processing stats: {e}")
            return {}
    
    def get_pending_emails(self, limit: int = 100) -> List[Tuple[str, int]]:
        """Get list of pending emails ordered by priority"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT email_uid, priority 
                    FROM emails 
                    WHERE status = 'pending' 
                    ORDER BY priority DESC, received_date ASC 
                    LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error getting pending emails: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old processed data to manage database size"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old completed emails
                cursor.execute("""
                    DELETE FROM emails 
                    WHERE status = 'completed' 
                    AND processed_date < ?
                """, (cutoff_date,))
                
                # Delete old metrics
                cursor.execute("""
                    DELETE FROM metrics 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                # Delete old errors
                cursor.execute("""
                    DELETE FROM errors 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                conn.commit()
                self.logger.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def close(self):
        """Close database connection"""
        # SQLite connections are per-transaction, so no persistent connection to close
        self.logger.info("State manager closed")